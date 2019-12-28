import { useEffect, useReducer } from 'react';
import axios from 'axios';

function reducer(state, action) {
  switch (action.type) {
    case 'LOADING':
      return state.loading ? state : {...state, loading: true};
    case 'SUCCESS':
      return {...state, loading: false, data: action.data};
    case 'FAILURE':
      return {...state, loading: false, error: true};
    default:
      return state;
  }
}

function useApi(query, initialData) {
  const [state, dispatch] = useReducer(reducer, initialData, data => ({
    loading: true,
    data: data,
    error: false,
  }));
  useEffect(() => {
    let mounted = true;
    dispatch({type: 'LOADING'});
    axios.post('/graphql', {query: query})
      .then(response => {
        if (mounted)
          dispatch({type: 'SUCCESS', data: response.data.data});
      })
      .catch(() => {
        if (mounted)
          dispatch({type: 'FAILURE'});
      });
    return () => {
      mounted = false;
    };
  }, [query]);
  return state;
}

export default useApi;