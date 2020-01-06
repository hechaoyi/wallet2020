import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { createReducer } from '../utils/api';

const query = `
  {
    categories {
      id
      name
    }
  }`;
const {reducer, load} =
  createReducer('CATEGORIES', [], data => data.data.categories);

export { reducer as categoriesReducer };
export default function useCategories() {
  const data = useSelector(state => state.categories);
  const dispatch = useDispatch();
  useEffect(() => dispatch(load(query)), [data.requested, dispatch]);
  return {loading: data.loading, data: data.data};
}
