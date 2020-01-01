import React from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { Button, makeStyles, Typography } from '@material-ui/core';
import notFound from '../assets/images/undraw_page_not_found_su7k.svg';

const useStyles = makeStyles((theme) => ({
  root: {
    padding: theme.spacing(3),
    paddingTop: '10vh',
    display: 'flex',
    flexDirection: 'column',
    alignContent: 'center'
  },
  imageContainer: {
    marginTop: theme.spacing(6),
    display: 'flex',
    justifyContent: 'center'
  },
  image: {
    maxWidth: '100%',
    width: 560,
    maxHeight: 300,
    height: 'auto'
  },
  buttonContainer: {
    marginTop: theme.spacing(6),
    display: 'flex',
    justifyContent: 'center'
  }
}));

function Error404() {
  const classes = useStyles();
  return (
    <div className={classes.root}>
      <Typography align="center" variant="h1">
        404: The page you are looking for isn’t here
      </Typography>
      <Typography align="center" variant="subtitle2">
        You either tried some shady route or you came here by mistake. Whichever
        it is, try using the navigation
      </Typography>
      <div className={classes.imageContainer}>
        <img src={notFound} alt="Under development" className={classes.image} />
      </div>
      <div className={classes.buttonContainer}>
        <Button color="primary" variant="outlined" component={RouterLink} to="/">
          Back to home
        </Button>
      </div>
    </div>
  );
}

export default Error404;