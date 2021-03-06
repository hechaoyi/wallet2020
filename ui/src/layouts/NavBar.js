import React, { useState } from 'react';
import { Button, Divider, Drawer, List, ListSubheader, makeStyles } from '@material-ui/core';
import {
  AccountBalance as BudgetIcon,
  Add as AddIcon,
  BarChart as BarChartIcon,
  Dashboard as DashboardIcon,
  Home as HomeIcon,
  ListAlt as TransactionIcon,
  Settings as SettingsIcon,
  ViewWeek as AccountIcon,
} from '@material-ui/icons';
import NavItem from '../components/NavItem';
import SplitButton from '../components/SplitButton';
import useTransactionTemplates from '../store/templates';
import AddTransactionModal from '../views/AddTransactionModal';

const useStyles = makeStyles((theme) => ({
  desktopDrawer: {
    width: 160,
    top: 48,
    height: 'calc(100% - 48px)'
  },
  root: {
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
  },
  navigation: {
    overflow: 'auto',
    padding: theme.spacing(2),
    flexGrow: 1
  },
  addButton: {
    marginBottom: theme.spacing(2),
    justifyContent: 'flex-start'
  },
  addIcon: {
    marginRight: theme.spacing(1)
  },
}));

function NavBar() {
  const classes = useStyles();
  const {data: transactionTemplatesData} = useTransactionTemplates();
  const [openAddTransactionModal, setOpenAddTransactionModal] = useState(false);
  const [transactionTemplate, setTransactionTemplate] = useState(undefined);
  const handleAddTransactionClick = (index = -1) => {
    setOpenAddTransactionModal(true);
    setTransactionTemplate(index >= 0 ? transactionTemplatesData[index] : undefined);
  };
  return (
    <Drawer variant="persistent" open classes={{paper: classes.desktopDrawer}}>
      <div className={classes.root}>
        <nav className={classes.navigation}>
          {transactionTemplatesData.length > 0 ?
            <SplitButton primaryOption="记一笔"
                         secondaryOptions={transactionTemplatesData.map(e => e.templateName)}
                         primaryHandleClick={handleAddTransactionClick}
                         secondaryHandleClick={handleAddTransactionClick} />
            :
            <Button variant="contained" color="primary" className={classes.addButton} fullWidth
                    onClick={handleAddTransactionClick}>
              <AddIcon className={classes.addIcon} /> 记一笔
            </Button>
          }
          <Divider />
          <List>
            <NavItem href="/u/home" title="总览" icon={HomeIcon} />
          </List>
          <List>
            <ListSubheader>收支</ListSubheader>
            <NavItem href="/u/transaction" title="交易列表" icon={TransactionIcon} />
            <NavItem href="/u/account" title="账户详情" icon={AccountIcon} />
            <NavItem href="/u/budget" title="预算管理" icon={BudgetIcon} />
          </List>
          <List>
            <ListSubheader>统计</ListSubheader>
            <NavItem href="/u/xxxx" title="xxxx" icon={DashboardIcon} />
            <NavItem href="/u/xxxx" title="xxxx" icon={DashboardIcon} />
            <NavItem href="/u/xxxx" title="xxxx" icon={BarChartIcon} />
            <NavItem href="/u/xxxx" title="xxxx" icon={BarChartIcon} />
          </List>
          <List>
            <ListSubheader>配置</ListSubheader>
            <NavItem href="/u/xxxx" title="xxxx" icon={SettingsIcon} />
            <NavItem href="/u/xxxx" title="xxxx" icon={SettingsIcon} />
            <NavItem href="/u/xxxx" title="xxxx" icon={SettingsIcon} />
            <NavItem href="/u/xxxx" title="xxxx" icon={SettingsIcon} />
          </List>
        </nav>
      </div>
      {openAddTransactionModal && (
        <AddTransactionModal onClose={() => setOpenAddTransactionModal(false)} template={transactionTemplate} />
      )}
    </Drawer>
  );
}

export default NavBar;