import React from 'react';
import { Redirect } from 'react-router-dom';
import Dashboard from './layouts/Dashboard';
import Home from './views/Home';
import Login from './views/Login';

export default [
  {
    path: '/',
    exact: true,
    component: () => <Redirect to="/u/home" />
  },
  {
    path: '/u/login',
    exact: true,
    component: Dashboard,
    routes: [{component: Login}]
  },
  {
    path: '/u',
    component: Dashboard,
    routes: [
      {
        path: '/u/home',
        exact: true,
        component: Home
      },
      {
        component: () => <p>404</p>
      }
    ]
  },
  {
    component: () => <p>404</p>
  }
];