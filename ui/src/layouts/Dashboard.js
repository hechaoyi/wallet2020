import React from 'react';
import PropTypes from 'prop-types';
import { renderRoutes } from 'react-router-config';
import { makeStyles } from '@material-ui/core';
import TopBar from './TopBar';
import AuthCheck from './AuthCheck';

const useStyles = makeStyles({
  container: {
    minHeight: '100vh',
    display: 'flex',
  },
  content: {
    paddingTop: 48,
    flexGrow: 1,
    maxWidth: '100%',
    overflowX: 'hidden',
  },
});

function Dashboard({route}) {
  const classes = useStyles();
  return (
    <>
      <TopBar />
      {route.loginPath && <AuthCheck loginPath={route.loginPath} />}
      <div className={classes.container}>
        <div className={classes.content}>
          {renderRoutes(route.routes)}
        </div>
      </div>
    </>
  );
}

Dashboard.propTypes = {
  route: PropTypes.object.isRequired
};

export default Dashboard;