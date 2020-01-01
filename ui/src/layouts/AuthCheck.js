import React, { useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import { Redirect } from 'react-router-dom';
import axios from 'axios';

function AuthCheck({loginPath}) {
  const [unauthorized, setUnauthorized] = useState(false);
  useEffect(() => {
    axios.post('/q', {query: '{healthCheck}'}).catch(() => setUnauthorized(true));
  }, []);
  return unauthorized && <Redirect to={loginPath} />;
}

AuthCheck.propTypes = {
  loginPath: PropTypes.string.isRequired
};

export default AuthCheck;