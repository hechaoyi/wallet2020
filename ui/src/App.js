import React from 'react';
import { Provider as StoreProvider } from 'react-redux';
import { ThemeProvider } from '@material-ui/core';
import Dashboard from './layouts/Dashboard';
import store from './store';
import theme from './theme';
import './assets/styles/main.scss';

function App() {
  return (
    <StoreProvider store={store}>
      <ThemeProvider theme={theme}>
        <Dashboard />
      </ThemeProvider>
    </StoreProvider>
  );
}

export default App;
