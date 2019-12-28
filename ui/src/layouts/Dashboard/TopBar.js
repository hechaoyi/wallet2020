import React from 'react';
import { AppBar, makeStyles, Toolbar, Typography } from '@material-ui/core';
import logo from '../../assets/images/icons8-google-photos.svg';

const useStyles = makeStyles(theme => ({
  logoImg: {
    height: 32,
    marginRight: theme.spacing(1)
  },
}));

function TopBar() {
  const classes = useStyles();
  return (
    <AppBar>
      <Toolbar variant="dense">
        <img src={logo} alt="logo" className={classes.logoImg} />
        <Typography variant="h5" color="inherit">我的账本</Typography>
      </Toolbar>
    </AppBar>
  );
}

export default TopBar;