// components/dashboard/GoogleConnect.jsx
import React, { useState, useEffect } from 'react';
import { Button } from '../ui';
import { authServices } from '../../services/auth.service';

const GoogleConnect = ({ onConnectionSuccess, onDisconnected }) => {
  const [isConnected, setIsConnected] = useState(false);
  const [loading, setLoading] = useState(false);
  const [checking, setChecking] = useState(true);
  const [error, setError] = useState('');

  // Check Google connection status on component mount
  useEffect(() => {
    checkGoogleStatus();
  }, []);

  // Check URL params for OAuth callback results
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const googleAuth = urlParams.get('google_auth');
    const message = urlParams.get('message');

    if (googleAuth === 'success') {
      setIsConnected(true);
      if (onConnectionSuccess) {
        onConnectionSuccess();
      }
      // Clean URL
      window.history.replaceState({}, document.title, window.location.pathname);
      
      // Force re-check status to ensure UI is updated
      setTimeout(() => {
        checkGoogleStatus();
      }, 1000);
      
    } else if (googleAuth === 'error') {
      setError(message || 'Google authentication failed');
      // Clean URL
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, [onConnectionSuccess]);

  const checkGoogleStatus = async () => {
    try {
      setChecking(true);
      setError(''); // Clear any existing errors
      const response = await authServices.getGoogleStatus();
      setIsConnected(response.connected);
    } catch (err) {
      console.error('Error checking Google status:', err);
      // Don't show error for status check failures - might be temporary
      setIsConnected(false);
    } finally {
      setChecking(false);
    }
  };

  const handleConnectGoogle = async () => {
    try {
      setLoading(true);
      setError('');
      
      const response = await authServices.getGoogleAuthUrl();
      
      // Redirect to Google OAuth
      window.location.href = response.authorization_url;
      
    } catch (err) {
      setError(err.message || 'Failed to initiate Google authentication');
      setLoading(false);
    }
  };

  const handleDisconnectGoogle = async () => {
    try {
      setLoading(true);
      setError('');
      
      await authServices.unlinkGoogle();
      setIsConnected(false);
      
      // Notify parent component
      if (onDisconnected) {
        onDisconnected();
      }
      
    } catch (err) {
      setError(err.message || 'Failed to disconnect Google account');
    } finally {
      setLoading(false);
    }
  };

  if (checking) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
          <div className="h-10 bg-gray-200 rounded w-32"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-medium text-gray-900">
            Google Account Connection
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            {isConnected 
              ? 'Your Google account is connected. You can now access Gmail and Calendar.'
              : 'Connect your Google account to access Gmail and Calendar features.'
            }
          </p>
        </div>

        <div className="flex items-center space-x-2">
          {isConnected ? (
            <>
              <div className="flex items-center text-green-600">
                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                Connected
              </div>
              <Button
                variant="outline"
                size="sm"
                loading={loading}
                onClick={handleDisconnectGoogle}
              >
                Disconnect
              </Button>
            </>
          ) : (
            <Button
              variant="primary"
              loading={loading}
              onClick={handleConnectGoogle}
            >
              <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
                <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              Connect Google Account
            </Button>
          )}
        </div>
      </div>

      {error && (
        <div className="mt-4 bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md text-sm">
          {error}
        </div>
      )}
    </div>
  );
};

export default GoogleConnect;