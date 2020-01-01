import React, { useReducer } from 'react';
import PropTypes from 'prop-types';
import { useHistory } from 'react-router';
import { Button, makeStyles, TextField } from '@material-ui/core';
import { validate } from 'validate.js';
import axios from 'axios';
import { stringify } from 'qs';

const useStyles = makeStyles((theme) => ({
  fields: {
    margin: theme.spacing(-1),
    display: 'flex',
    flexWrap: 'wrap',
    '& > *': {
      flexGrow: 1,
      margin: theme.spacing(1)
    }
  },
  submitButton: {
    marginTop: theme.spacing(2),
    width: '100%'
  },
}));

const schema = {
  username: {
    presence: {allowEmpty: false, message: '必填'},
  },
  password: {
    presence: {allowEmpty: false, message: '必填'}
  }
};

const initialState = {
  values: {},
  touched: {},
  errors: {},
  isValid: false
};

function reducer(state, action) {
  switch (action.type) {
    case 'CHANGE':
      const target = action.event.target;
      const values = {...state.values, [target.name]: target.value};
      const touched = {...state.touched, [target.name]: true};
      const errors = validate(values, schema, {fullMessages: false});
      return {values, touched, errors: errors || {}, isValid: !errors};
    case 'SUBMIT':
      axios.post('/login', stringify(state.values))
        .then(() => action.history.push('/'))
        .catch(() => action.dispatch({type: 'FAILURE'}));
      return {...state, isValid: false};
    case 'FAILURE':
      return {
        ...state,
        errors: {username: ['用户名或密码不正确'], password: ['用户名或密码不正确']},
        isValid: false
      };
    default:
      throw new Error();
  }
}

function LoginForm({className}) {
  const classes = useStyles();
  const history = useHistory();
  const [state, dispatch] = useReducer(reducer, initialState);

  const handleChange = (event) => {
    event.persist();
    dispatch({type: 'CHANGE', event});
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    dispatch({type: 'SUBMIT', history, dispatch});
  };

  return (
    <form className={className} onSubmit={handleSubmit}>
      <div className={classes.fields}>
        <TextField
          error={state.touched.username && !!state.errors.username}
          fullWidth
          helperText={state.touched.username && state.errors.username && state.errors.username[0]}
          label="用户名"
          name="username"
          onChange={handleChange}
          value={state.values.username || ''}
          variant="outlined" />
        <TextField
          error={state.touched.password && !!state.errors.password}
          fullWidth
          helperText={state.touched.password && state.errors.password && state.errors.password[0]}
          label="密码"
          name="password"
          onChange={handleChange}
          type="password"
          value={state.values.password || ''}
          variant="outlined" />
      </div>
      <Button
        className={classes.submitButton}
        color="secondary"
        disabled={!state.isValid}
        size="large"
        type="submit"
        variant="contained">登录</Button>
    </form>
  );
}

LoginForm.propTypes = {
  className: PropTypes.string
};

export default LoginForm;