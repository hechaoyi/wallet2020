import React from 'react';
import { Provider as StoreProvider } from 'react-redux';
import { BrowserRouter as Router } from 'react-router-dom';
import { renderRoutes } from 'react-router-config';
import { ThemeProvider } from '@material-ui/core';
import store from './store';
import theme from './theme';
import routes from './routes';
import './assets/styles/main.scss';

function App() {
  return (
    <StoreProvider store={store}>
      <ThemeProvider theme={theme}>
        <Router>
          {renderRoutes(routes)}
        </Router>
      </ThemeProvider>
    </StoreProvider>
  );
}

export default App;
