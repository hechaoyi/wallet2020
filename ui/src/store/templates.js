import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { createReducer } from '../utils/api';

const query = '{transactionTemplates}';
const {reducer, load, reset} =
  createReducer('TRANSACTION_TEMPLATES', [],
    data => JSON.parse(data.data.transactionTemplates));

export { reducer as transactionTemplatesReducer };
export default function useTransactionTemplates() {
  const data = useSelector(state => state.transactionTemplates);
  const dispatch = useDispatch();
  useEffect(() => dispatch(load(query)), [data.requested, dispatch]);
  return {loading: data.loading, data: data.data, reset: () => dispatch(reset())};
}