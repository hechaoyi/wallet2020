import React from 'react';
import { Card, CardContent, makeStyles, Typography } from '@material-ui/core';
import { Lock as LockIcon } from '@material-ui/icons';
import LoginForm from './LoginForm';
import gradients from '../../utils/gradients';

const useStyles = makeStyles((theme) => ({
  root: {
    height: '100%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: theme.spacing(2, 2, 20, 2)
  },
  card: {
    width: '400px',
    maxWidth: '100%',
    overflow: 'visible',
    display: 'flex',
    position: 'relative',
    '& > *': {
      flexGrow: 1
    }
  },
  content: {
    padding: theme.spacing(8, 4, 3, 4)
  },
  icon: {
    backgroundImage: gradients.green,
    color: theme.palette.common.white,
    borderRadius: theme.shape.borderRadius,
    padding: theme.spacing(1),
    position: 'absolute',
    top: -32,
    left: theme.spacing(3),
    height: 64,
    width: 64,
    fontSize: 32
  },
  loginForm: {
    marginTop: theme.spacing(3)
  },
}));

function Login() {
  const classes = useStyles();
  return (
    <div className={classes.root}>
      <Card className={classes.card}>
        <CardContent className={classes.content}>
          <LockIcon className={classes.icon} />
          <Typography variant="h3" gutterBottom>登录</Typography>
          <LoginForm className={classes.loginForm} />
        </CardContent>
      </Card>
    </div>
  );
}

export default Login;