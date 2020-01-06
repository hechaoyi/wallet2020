import React from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  colors,
  Divider,
  makeStyles,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography
} from '@material-ui/core';
import clsx from 'clsx';
import Label from '../../components/Label';
import useAccounts from '../../store/accounts';

const useStyles = makeStyles(theme => ({
  content: {
    padding: 0
  },
  entryLabel: {
    marginRight: theme.spacing(1)
  },
  positiveValue: {
    color: colors.green[600],
    fontWeight: theme.typography.fontWeightMedium
  },
  negativeValue: {
    color: colors.red[600],
    fontWeight: theme.typography.fontWeightMedium
  },
}));

const balanceColor = (type, value, classes) => {
  return clsx({
    [classes.positiveValue]: (type === 1 && value > 0) || (type === 2 && value < 0),
    [classes.negativeValue]: (type === 1 && value < 0) || (type === 2 && value > 0),
  });
};

const balanceColorForEntry = (type, value) => {
  if ((type === 1 && value > 0) || (type === 2 && value < 0))
    return colors.green[400];
  if ((type === 1 && value < 0) || (type === 2 && value > 0))
    return colors.red[400];
  return colors.blueGrey[400];
};

function Accounts() {
  const classes = useStyles();
  const {data: accounts} = useAccounts();
  return (
    <Card>
      <CardHeader title="账户列表" />
      <Divider />
      <CardContent className={classes.content}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>名称</TableCell>
              <TableCell>类型</TableCell>
              <TableCell>余额(美元)</TableCell>
              <TableCell>余额(人民币)</TableCell>
              <TableCell style={{width: '40%'}}>子项</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {accounts.map(account => (
              <TableRow hover key={account.id}>
                <TableCell>{account.name}</TableCell>
                <TableCell>{account.typeName}</TableCell>
                <TableCell>
                  {account.balanceUsd !== 0 && (
                    <Typography variant="subtitle2" className={balanceColor(account.type, account.balanceUsd, classes)}>
                      $ {account.balanceUsd}
                    </Typography>
                  )}
                </TableCell>
                <TableCell>
                  {account.balanceRmb !== 0 && (
                    <Typography variant="subtitle2" className={balanceColor(account.type, account.balanceRmb, classes)}>
                      ¥ {account.balanceRmb}
                    </Typography>
                  )}
                </TableCell>
                <TableCell>
                  {account.activeEntries.map(entry => (
                    <Label variant="outlined" shape="rounded" className={classes.entryLabel}
                           color={balanceColorForEntry(account.type, entry.amount)} key={entry.id}>
                      {entry.name} | {entry.currencySymbol}{entry.amount}
                    </Label>
                  ))}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

export default Accounts;