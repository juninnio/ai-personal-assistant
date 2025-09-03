// App.jsx
import React, { useState, useEffect } from 'react';
import { AuthContainer } from './components/auth';
import { Dashboard } from './components/dashboard';
import { authServices } from './services/auth.service';

const App = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Check if user is already logged in when app starts
  useEffect(() => {
    const currentUser = authServices.getCurrentUser();
    if (currentUser) {
      setUser(currentUser);
    }
    setLoading(false);
  }, []);
  


  const handleLoginSuccess = (userData) => {
    setUser(userData);
  };

  const handleLogout = () => {
    authServices.logout();
    setUser(null);
  };

  // Show loading spinner while checking auth status
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  // If user is logged in, show dashboard
  if (user) {
    return (
      <Dashboard 
        user={user} 
        onLogout={handleLogout} 
      />
    );
  }

  // If not logged in, show auth forms
  return (
    <AuthContainer onLoginSuccess={handleLoginSuccess} />
  );
};

export default App;