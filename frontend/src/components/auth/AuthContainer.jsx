// components/auth/AuthContainer.jsx
import React, { useState } from 'react';
import {LoginForm, RegisterForm} from './'

const AuthContainer = ({ onLoginSuccess }) => {
  const [currentView, setCurrentView] = useState('login'); // 'login' or 'register'

  const switchToLogin = () => setCurrentView('login');
  const switchToRegister = () => setCurrentView('register');

  if (currentView === 'register') {
    return (
      <RegisterForm
        onSwitchToLogin={switchToLogin}
        onSuccess={() => {
          // Optional: do something when registration succeeds
          console.log('Registration completed');
        }}
      />
    );
  }

  return (
    <LoginForm
      onSwitchToRegister={switchToRegister}
      onLoginSuccess={onLoginSuccess}
    />
  );
};

export default AuthContainer;