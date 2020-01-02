import React from 'react';
import { Drawer, List, ListSubheader, makeStyles } from '@material-ui/core';
import {
  BarChart as BarChartIcon,
  Dashboard as DashboardIcon,
  Home as HomeIcon,
  ListAlt as ListAltIcon,
  Settings as SettingsIcon
} from '@material-ui/icons';
import NavItem from '../components/NavItem';

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
    padding: theme.spacing(0, 2, 2, 2),
    flexGrow: 1
  },
}));

function NavBar() {
  const classes = useStyles();
  return (
    <Drawer variant="persistent" open classes={{paper: classes.desktopDrawer}}>
      <div className={classes.root}>
        <nav className={classes.navigation}>
          <List>
            <NavItem href="/u/home" title="总览" icon={HomeIcon} />
          </List>
          <List>
            <ListSubheader>收支</ListSubheader>
            <NavItem href="/u/xxxx" title="xxxx" icon={ListAltIcon} />
            <NavItem href="/u/xxxx" title="xxxx" icon={ListAltIcon} />
            <NavItem href="/u/xxxx" title="xxxx" icon={ListAltIcon} />
            <NavItem href="/u/xxxx" title="xxxx" icon={ListAltIcon} />
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
    </Drawer>
  );
}

export default NavBar;