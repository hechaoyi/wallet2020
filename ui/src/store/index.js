import { applyMiddleware, combineReducers, createStore } from 'redux';
import thunk from 'redux-thunk';
import { composeWithDevTools } from 'redux-devtools-extension';
import { accountsReducer } from './accounts';
import { categoriesReducer } from './categories';
import { transactionTemplatesReducer } from './templates';

export default createStore(combineReducers({
  accounts: accountsReducer,
  categories: categoriesReducer,
  transactionTemplates: transactionTemplatesReducer,
}), composeWithDevTools(applyMiddleware(thunk)));