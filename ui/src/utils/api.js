import axios from 'axios';

export function createReducer(prefix, initialData, responseReducer) {
  const initialState = {loading: true, data: initialData, error: false};

  function reducer(state = initialState, action) {
    switch (action.type) {
      case prefix + '_LOADING':
        return state.loading ? state : {...state, loading: true};
      case prefix + '_SUCCESS':
        return {...state, loading: false, data: action.data, error: false};
      case prefix + '_FAILURE':
        return {...state, loading: false, data: initialData, error: true};
      default:
        return state;
    }
  }

  function fetch(query) {
    return dispatch => {
      let cancelled = false;
      dispatch({type: prefix + '_LOADING'});
      axios.post('/q', {query: query})
        .then(response => {
          if (!cancelled)
            dispatch({type: prefix + '_SUCCESS', data: responseReducer(response.data)});
        })
        .catch(() => {
          if (!cancelled)
            dispatch({type: prefix + '_FAILURE'});
        });
      return () => {
        cancelled = true;
      };
    };
  }

  return {reducer, fetch};
}