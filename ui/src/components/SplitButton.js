import React, { useRef, useState } from 'react';
import PropTypes from 'prop-types';
import {
  Button,
  ButtonGroup,
  ClickAwayListener,
  Grow,
  makeStyles,
  MenuItem,
  MenuList,
  Paper,
  Popper
} from '@material-ui/core';
import { ArrowDropDown as DownIcon, ArrowDropUp as UpIcon } from '@material-ui/icons';


const useStyles = makeStyles(() => ({
  fullWidth: {
    width: '100%'
  },
  narrow: {
    padding: '6px',
    minWidth: '20px'
  },
  paper: {
    zIndex: 100,
  }
}));

function SplitButton({primaryOption, secondaryOptions, primaryHandleClick, secondaryHandleClick}) {
  const classes = useStyles();
  const anchorRef = useRef(null);
  const [open, setOpen] = useState(false);
  const handleToggle = () => setOpen(isOpen => !isOpen);
  const handleClose = () => setOpen(false);
  return (
    <>
      <ButtonGroup variant="contained" color="primary" className={classes.fullWidth}>
        <Button className={classes.fullWidth} onClick={primaryHandleClick}>{primaryOption}</Button>
        <Button className={classes.narrow} ref={anchorRef} onClick={handleToggle}>
          {open ? <UpIcon /> : <DownIcon />}</Button>
      </ButtonGroup>
      <Popper open={open} anchorEl={anchorRef.current} transition disablePortal className={classes.paper}>
        {({TransitionProps, placement}) => (
          <Grow {...TransitionProps} style={{transformOrigin: placement === 'bottom' ? 'center top' : 'center bottom'}}>
            <Paper elevation={3}>
              <ClickAwayListener onClickAway={handleClose}>
                <MenuList>
                  {secondaryOptions.map((option, index) => (
                    <MenuItem key={index} onClick={() => {
                      secondaryHandleClick(index);
                      handleClose();
                    }}>{option}</MenuItem>
                  ))}
                </MenuList>
              </ClickAwayListener>
            </Paper>
          </Grow>
        )}
      </Popper>
    </>
  );
}

SplitButton.propTypes = {
  primaryOption: PropTypes.string.isRequired,
  secondaryOptions: PropTypes.arrayOf(PropTypes.string).isRequired,
  primaryHandleClick: PropTypes.func.isRequired,
  secondaryHandleClick: PropTypes.func.isRequired,
};

export default SplitButton;