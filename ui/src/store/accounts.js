import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
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
const {reducer, load, reset} =
  createReducer('ACCOUNTS', [], data => data.data.accounts);

export { reducer as accountsReducer };
export default function useAccounts() {
  const data = useSelector(state => state.accounts);
  const dispatch = useDispatch();
  useEffect(() => dispatch(load(query)), [data.requested, dispatch]);
  return {loading: data.loading, data: data.data, reset: () => dispatch(reset())};
}