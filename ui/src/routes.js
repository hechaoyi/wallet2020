import React from 'react';
import { Redirect } from 'react-router-dom';
import Dashboard from './layouts/Dashboard';
import Home from './views/Home';
import Login from './views/Login';
import Error404 from './views/Error404';

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
    showNavBar: true,
    loginPath: '/u/login',
    routes: [
      {
        path: '/u/home',
        exact: true,
        component: Home
      },
      {component: Error404}
    ]
  },
  {component: Error404}
];