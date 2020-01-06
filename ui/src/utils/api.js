import axios from 'axios';

export function createReducer(prefix, initialData, responseReducer) {
  const initialState = {loading: false, data: initialData, error: false, requested: false};

  function reducer(state = initialState, action) {
    switch (action.type) {
      case prefix + '_LOAD':
        if (state.requested)
          return state;
        fetch(action.query, action.dispatch);
        return {...state, loading: true, requested: true};
      case prefix + '_SUCCESS':
        return {...state, loading: false, data: action.data, error: false};
      case prefix + '_FAILURE':
        return {...state, loading: false, data: initialData, error: true};
      case prefix + '_RESET':
        return {...state, loading: false, requested: false};
      default:
        return state;
    }
  }

  function fetch(query, dispatch) {
    axios.post('/q', {query})
      .then(response => {
        dispatch({type: prefix + '_SUCCESS', data: responseReducer(response.data)});
      })
      .catch(error => {
        dispatch({
          type: error.response.status === 401 ? prefix + '_RESET' : prefix + '_FAILURE'
        });
      });
  }

  function load(query) {
    return dispatch => {
      dispatch({type: prefix + '_LOAD', query, dispatch});
    };
  }

  function reset() {
    return dispatch => {
      dispatch({type: prefix + '_RESET'});
    };
  }

  return {reducer, load, reset};
}
