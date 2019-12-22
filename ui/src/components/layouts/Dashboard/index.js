import React from 'react';
import TopBar from "./TopBar";
import { makeStyles } from "@material-ui/core";

const useStyles = makeStyles(theme => ({
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
}));

function Dashboard() {
  const classes = useStyles();
  return (
    <>
      <TopBar />
      <div className={classes.container}>
        <div className={classes.content}>
        </div>
      </div>
    </>
  );
}

export default Dashboard;