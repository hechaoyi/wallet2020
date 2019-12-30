import { useDispatch, useSelector } from 'react-redux';
import { useEffect } from 'react';
import { createReducer } from '../utils/api';

const query = `
  {
    accounts {
      id
      name
      type
      typeName
      balanceUsd
      balanceRmb
      activeEntries {
        id
        name
        amount
        currency
        currencySymbol
      }
    }
  }`;
const {reducer, fetch} =
  createReducer('ACCOUNTS', [], data => data.data.accounts);

export { reducer as accountsReducer };
export default function useAccounts() {
  const dispatch = useDispatch();
  useEffect(() => dispatch(fetch(query)), [dispatch]);
  return useSelector(state => state.accounts);
}