import React, { Fragment, useReducer } from 'react';
import PropTypes from 'prop-types';
import {
  Badge,
  Button,
  Card,
  CardActions,
  CardContent,
  CardHeader,
  CircularProgress,
  Divider,
  FormControlLabel,
  Grid,
  IconButton,
  InputAdornment,
  makeStyles,
  MenuItem,
  Modal,
  TextField
} from '@material-ui/core';
import { AddBox as AddBoxIcon, Check as CheckIcon, Close as CloseIcon, Delete as DeleteIcon } from '@material-ui/icons';
import { DateTimePicker } from '@material-ui/pickers';
import { validate } from 'validate.js';
import moment from 'moment';
import axios from 'axios';
import useCategories from '../store/categories';
import useAccounts from '../store/accounts';
import RedGreenSwitch from '../components/RedGreenSwitch';

const useStyles = makeStyles((theme) => ({
  root: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    outline: 'none',
    boxShadow: theme.shadows[20],
    width: 720,
    maxHeight: '100%',
    overflowY: 'auto',
    maxWidth: '100%'
  },
  labelWrapper: {
    display: 'flex',
    justifyContent: 'center'
  },
  fullWidth: {
    width: '100%'
  },
  actions: {
    justifyContent: 'flex-end'
  },
  leftAction: {
    marginRight: 'auto'
  },
  buttonWrapper: {
    position: 'relative'
  },
  buttonProgress: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    marginTop: -12,
    marginLeft: -12,
  },
}));

const schema = {
  category: {presence: true},
  description: {
    presence: {allowEmpty: false}
  },
  items: {
    array: {
      account: {presence: true},
      amount: {
        presence: {allowEmpty: false},
        numericality: {greaterThan: 0}
      }
    }
  }
};

const initialState = {
  values: {time: moment(), timezoneUS: true, items: [{inflow: false, currencyUS: true}]},
  touched: {items: [{}]},
  errors: {},
  isValid: false,
  isLoading: false
};

function reducer(state, action) {
  switch (action.type) {
    case 'CHANGE':
      const {name, value} = action;
      const dot = name.indexOf('.');
      let values, touched;
      if (dot < 0) {
        values = {...state.values, [name]: value};
        touched = {...state.touched, [name]: true};
      } else {
        values = {...state.values, items: [...state.values.items]};
        touched = {...state.touched, items: [...state.touched.items]};
        const index = parseInt(name.substring(0, dot));
        const field = name.substring(dot + 1);
        values.items[index] = {...values.items[index], [field]: value};
        touched.items[index] = {...touched.items[index], [field]: true};
        if (field === 'account')
          delete values.items[index]['mergeEntry'];
      }
      const errors = validate(values, schema, {fullMessages: false});
      return {...state, values, touched, errors: errors || {}, isValid: !errors};
    case 'ADD_ITEM':
      return {
        ...state, isValid: false,
        values: {...state.values, items: [...state.values.items, {inflow: false, currencyUS: true}]},
        touched: {...state.touched, items: [...state.touched.items, {}]}
      };
    case 'DEL_ITEM':
      state = {
        ...state, isValid: false,
        values: {...state.values, items: [...state.values.items]},
        touched: {...state.touched, items: [...state.touched.items]}
      };
      state.values.items.splice(action.index, 1);
      state.touched.items.splice(action.index, 1);
      return state;
    case 'SUBMIT':
      const query = `
        mutation addTransaction($input: TransactionInput!) {
          addTransaction(input: $input) {
            ok
          }
        }`;
      const input = state.values;
      axios.post('/q', {query, variables: {input}})
        .then(response => {
          if (!response.data.errors) {
            action.accountsReset();
            action.onClose();
          } else {
            action.dispatch({type: 'FAILURE', message: response.data.errors[0].message});
          }
        })
        .catch(error => action.dispatch({type: 'FAILURE', message: error.message}));
      return {...state, isValid: false, isLoading: true};
    case 'FAILURE':
      alert(action.message); // TODO global snackbar
      return {...state, isValid: false, isLoading: false};
    default:
      throw new Error();
  }
}

function AddTransactionModal({onClose}) {
  const classes = useStyles();
  const {loading: categoriesLoading, data: categoriesData} = useCategories();
  const {loading: accountsLoading, data: accountsData, reset: accountsReset} = useAccounts();
  const [state, dispatch] = useReducer(reducer, initialState);

  const handleChange = (event) => {
    dispatch({type: 'CHANGE', name: event.target.name, value: event.target.value});
  };
  const handlePickerChange = (time) => {
    dispatch({type: 'CHANGE', name: 'time', value: time});
  };
  const handleSwitchChange = (event) => {
    dispatch({type: 'CHANGE', name: event.target.name, value: event.target.checked});
  };

  const isItemFieldError = (index, field, touched = false) => {
    if (touched && (!state.touched.items || !state.touched.items[index] || !state.touched.items[index][field]))
      return false;
    return state.errors.items && state.errors.items[0][index] && !!state.errors.items[0][index][field];
  };

  const addItem = () => dispatch({type: 'ADD_ITEM'});
  const delItem = (index) => dispatch({type: 'DEL_ITEM', index});

  const handleSubmit = (event) => {
    event.preventDefault();
    dispatch({type: 'SUBMIT', accountsReset, onClose, dispatch});
  };

  return (
    <Modal onClose={onClose} open>
      <Card className={classes.root}>
        <form onSubmit={handleSubmit}>
          <CardHeader title="添加交易记录" />
          <Divider />
          <CardContent>
            <Grid container spacing={2}>
              <Grid item xs={5}>
                <TextField label="分类" name="category" variant="outlined" margin="dense" fullWidth select
                           value={state.values.category || ''} onChange={handleChange}
                           error={!!state.errors.category}>
                  {categoriesLoading ?
                    <MenuItem disabled><CircularProgress size={18} /></MenuItem>
                    : categoriesData.map(category =>
                      <MenuItem key={category.id} value={category.id}>{category.name}</MenuItem>)}
                </TextField>
              </Grid>
              <Grid item xs={4}>
                <DateTimePicker label="时间" name="time" inputVariant="outlined" margin="dense" fullWidth
                                value={state.values.time} onChange={handlePickerChange}
                                format="YYYY-MM-DD HH:mm" variant="inline" disableFuture autoOk hideTabs />
              </Grid>
              <Grid item xs={3} className={classes.labelWrapper}>
                <FormControlLabel
                  control={
                    <RedGreenSwitch name="timezoneUS" size="small"
                                    checked={state.values.timezoneUS} onChange={handleSwitchChange} />
                  }
                  label={state.values.timezoneUS ? '美西时间' : '北京时间'} />
              </Grid>
              <Grid item xs={12}>
                <TextField label="说明" name="description" variant="outlined" margin="dense" fullWidth
                           value={state.values.description || ''} onChange={handleChange}
                           error={state.touched.description && !!state.errors.description} />
              </Grid>
              {state.values.items.map((item, i) => (
                <Fragment key={i}>
                  <Grid item xs={12}><Divider /></Grid>
                  <Grid item xs={5}>
                    <Badge badgeContent={i + 1} color="primary" className={classes.fullWidth}
                           anchorOrigin={{horizontal: 'left', vertical: 'top'}}>
                      <TextField label="账户" name={`${i}.account`} variant="outlined" margin="dense" fullWidth select
                                 value={state.values.items[i].account || ''} onChange={handleChange}
                                 error={isItemFieldError(i, 'account')}>
                        {accountsLoading ?
                          <MenuItem disabled><CircularProgress size={18} /></MenuItem>
                          : accountsData.map(account =>
                            <MenuItem key={account.id} value={account.id}>
                              {account.name} | {state.values.items[i].currencyUS ?
                              <>${account.balanceUsd}</> : <>¥{account.balanceRmb}</>}
                            </MenuItem>)}
                      </TextField>
                    </Badge>
                  </Grid>
                  <Grid item xs={3} className={classes.labelWrapper}>
                    <FormControlLabel
                      control={
                        <RedGreenSwitch name={`${i}.inflow`} size="small"
                                        checked={!!state.values.items[i].inflow} onChange={handleSwitchChange} />
                      }
                      label={(!state.values.items[i].account ||
                        accountsData.find(a => a.id === state.values.items[i].account).type !== 3) ?
                        (state.values.items[i].inflow ? '收入' : '支出') :
                        (state.values.items[i].inflow ? '权益增加' : '权益减少')} />
                  </Grid>
                  <Grid item xs={2}>
                    <TextField label="金额" name={`${i}.amount`} variant="outlined" margin="dense" fullWidth
                               InputProps={state.values.items[i].amount ? {
                                 startAdornment: <InputAdornment position="start">
                                   {state.values.items[i].currencyUS ? '$' : '¥'}
                                 </InputAdornment>
                               } : null}
                               value={state.values.items[i].amount || ''} onChange={handleChange}
                               error={isItemFieldError(i, 'amount', true)} />
                  </Grid>
                  <Grid item xs={2} className={classes.labelWrapper}>
                    <FormControlLabel
                      control={
                        <RedGreenSwitch name={`${i}.currencyUS`} size="small"
                                        checked={!!state.values.items[i].currencyUS} onChange={handleSwitchChange} />
                      }
                      label={state.values.items[i].currencyUS ? '美元' : '人民币'} />
                  </Grid>
                  <Grid item xs={state.values.items.length > 1 ? 6 : 7}>
                    <TextField label="说明（可选）" name={`${i}.description`} variant="outlined" margin="dense" fullWidth
                               value={state.values.items[i].description || ''} onChange={handleChange} />
                  </Grid>
                  <Grid item xs={5}>
                    <TextField label="计入子项（可选）" name={`${i}.mergeEntry`} variant="outlined" margin="dense" fullWidth
                               select disabled={!state.values.items[i].account}
                               value={state.values.items[i].mergeEntry || ''} onChange={handleChange}>
                      {!state.values.items[i].account ? ' ' :
                        accountsData.find(a => a.id === state.values.items[i].account).activeEntries
                          .map(entry => <MenuItem key={entry.id} value={entry.id}>
                            {entry.name} | {entry.currencySymbol}{entry.amount}
                          </MenuItem>)}
                    </TextField>
                  </Grid>
                  {state.values.items.length > 1 && <Grid item xs={1}>
                    <IconButton onClick={() => delItem(i)}><DeleteIcon /></IconButton>
                  </Grid>}
                </Fragment>
              ))}
            </Grid>
          </CardContent>
          <Divider />
          <CardActions className={classes.actions}>
            <div className={classes.leftAction}>
              <IconButton color="primary" onClick={addItem}><AddBoxIcon /></IconButton>
            </div>
            <Button variant="contained" startIcon={<CloseIcon />} onClick={onClose}>取消</Button>
            <div className={classes.buttonWrapper}>
              <Button variant="contained" startIcon={<CheckIcon />} color="primary" type="submit"
                      disabled={!state.isValid}>确认</Button>
              {state.isLoading && <CircularProgress size={24} className={classes.buttonProgress} />}
            </div>
          </CardActions>
        </form>
      </Card>
    </Modal>
  );
}

AddTransactionModal.propTypes = {
  onClose: PropTypes.func.isRequired
};

export default AddTransactionModal;