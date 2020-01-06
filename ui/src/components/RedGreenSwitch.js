import { colors, Switch, withStyles } from '@material-ui/core';

const RedGreenSwitch = withStyles({
  switchBase: {
    color: colors.red[500],
    '&$checked': {
      color: colors.green[500],
    },
    '&$checked + $track': {
      backgroundColor: colors.green[500],
    },
  },
  checked: {},
  track: {
    backgroundColor: colors.red[500]
  },
})(Switch);

export default RedGreenSwitch;