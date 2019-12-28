import React from 'react';
import { Container, Grid, makeStyles } from '@material-ui/core';
import Accounts from './Accounts';

const useStyles = makeStyles((theme) => ({
  root: {
    paddingTop: theme.spacing(3),
    paddingBottom: theme.spacing(3)
  }
}));

function Home() {
  const classes = useStyles();
  return (
    <div className={classes.root}>
      <Container maxWidth={false}>
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Accounts />
          </Grid>
        </Grid>
      </Container>
    </div>
  );
}

export default Home;