import React from 'react';
import PropTypes from 'prop-types';
import { renderRoutes } from 'react-router-config';
import { makeStyles } from '@material-ui/core';
import TopBar from './TopBar';

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

function Dashboard({route, children}) {
  const classes = useStyles();
  return (
    <>
      <TopBar />
      <div className={classes.container}>
        <div className={classes.content}>
          {route && renderRoutes(route.routes)}
          {children}
        </div>
      </div>
    </>
  );
}

Dashboard.propTypes = {
  route: PropTypes.object,
  children: PropTypes.node,
};

export default Dashboard;