import React from 'react';
import { ThemeProvider } from '@material-ui/core';
import Dashboard from './layouts/Dashboard';
import theme from './theme';
import './assets/styles/main.scss';

function App() {
  return (
    <ThemeProvider theme={theme}>
      <Dashboard />
    </ThemeProvider>
  );
}

export default App;
