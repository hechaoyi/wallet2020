import { applyMiddleware, combineReducers, createStore } from 'redux';
import thunk from 'redux-thunk';
import { accountsReducer } from './accounts';

export default createStore(combineReducers({
  accounts: accountsReducer,
}), applyMiddleware(thunk));