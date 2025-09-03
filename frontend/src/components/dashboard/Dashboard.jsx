import React, { useState, useEffect } from 'react';
import GoogleConnect from './GoogleConnect';
import EmailList from './EmailList';
import PendingEvents from './PendingEvents';
import { Button } from '../ui';
import { authServices } from '../../services/auth.service';
import { emailService } from '../../services/email.service';

const Dashboard = ({ user, onLogout }) => {
  const [googleConnected, setGoogleConnected] = useState(false);
  const [checkingGoogleStatus, setCheckingGoogleStatus] = useState(true);
  const [emailData, setEmailData] = useState(null);
  const [loadingEmails, setLoadingEmails] = useState(false);
  const [emailCount, setEmailCount] = useState(10);

  // Check Google connection status when component mounts
  useEffect(() => {
    checkInitialGoogleStatus();
  }, []);

  const checkInitialGoogleStatus = async () => {
    try {
      const response = await authServices.getGoogleStatus();
      setGoogleConnected(response.connected);
    } catch (err) {
      console.error('Error checking initial Google status:', err);
      setGoogleConnected(false);
    } finally {
      setCheckingGoogleStatus(false);
    }
  };

  const handleGoogleConnectionSuccess = () => {
    setGoogleConnected(true);
    fetchEmails();
  };

  const handleGoogleDisconnected = () => {
    setGoogleConnected(false);
    setEmailData(null);
  };

  const fetchEmails = async () => {
    try {
      setLoadingEmails(true);
      const data = await emailService.fetchAndProcessEmails(emailCount);
      setEmailData(data);
    } catch (err) {
      console.error('Error fetching emails:', err);
      alert('Failed to fetch emails: ' + err.message);
    } finally {
      setLoadingEmails(false);
    }
  };

  // Optimistic update functions
  const removeEventOptimistically = (emailId) => {
    if (emailData) {
      setEmailData(prev => ({
        ...prev,
        pending_events: prev.pending_events.filter(event => event.email_id !== emailId)
      }));
    }
  };

  const addEventToEmailsOptimistically = (event) => {
    if (emailData) {
      setEmailData(prev => ({
        ...prev,
        summarized_emails: [...prev.summarized_emails, event],
        pending_events: prev.pending_events.filter(e => e.email_id !== event.email_id)
      }));
    }
  };

  // Updated event handlers
  const handleEventAddedToCalendar = (emailId) => {
    // Optimistically remove from pending events
    removeEventOptimistically(emailId);
  };

  const handleEventIgnored = (emailId) => {
    // Optimistically remove from pending events
    removeEventOptimistically(emailId);
  };

  const handleEventsUpdate = () => {
    // Still keep this for error recovery - only call if needed
    fetchEmails();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header - unchanged */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <h1 className="text-2xl font-bold text-gray-900">
              Email Assistant
            </h1>
            <div className="flex items-center space-x-4">
              <span className="text-gray-700">Welcome, {user.username}</span>
              <Button
                variant="outline"
                size="sm"
                onClick={onLogout}
              >
                Logout
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        <div className="space-y-6">
          <GoogleConnect 
            onConnectionSuccess={handleGoogleConnectionSuccess}
            onDisconnected={handleGoogleDisconnected}
          />

          {checkingGoogleStatus ? (
            <div className="bg-white shadow rounded-lg p-6">
              <div className="animate-pulse">
                <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
                <div className="h-4 bg-gray-200 rounded w-2/3"></div>
              </div>
            </div>
          ) : (
            googleConnected ? (
              <div className="space-y-6">
                <div className="bg-white shadow rounded-lg p-6">
                  <div className="flex justify-between items-center mb-4">
                    <h2 className="text-lg font-medium text-gray-900">
                      Email Processing
                    </h2>
                    <div className="flex items-center space-x-4">
                      <div className="flex items-center space-x-2">
                        <label htmlFor="email-count" className="text-sm text-gray-600">
                          Emails to fetch:
                        </label>
                        <select
                          id="email-count"
                          value={emailCount}
                          onChange={(e) => setEmailCount(parseInt(e.target.value))}
                          className="border border-gray-300 rounded-md px-3 py-1 text-sm"
                        >
                          <option value={10}>10</option>
                          <option value={25}>25</option>
                          <option value={50}>50</option>
                          <option value={100}>100</option>
                        </select>
                      </div>
                      <Button
                        variant="primary"
                        loading={loadingEmails}
                        onClick={fetchEmails}
                      >
                        {emailData ? 'Refresh Emails' : 'Fetch Emails'}
                      </Button>
                    </div>
                  </div>
                  
                  {emailData && (
                    <div className="text-sm text-gray-600">
                      Processed {emailData.total_emails_processed} emails • 
                      Found {emailData.summarized_emails?.length || 0} important emails • 
                      Found {emailData.pending_events?.length || 0} pending events
                    </div>
                  )}
                </div>

                {emailData && (
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <PendingEvents 
                      events={emailData.pending_events}
                      onEventAddedToCalendar={handleEventAddedToCalendar}
                      onEventIgnored={handleEventIgnored}
                      onEventsUpdate={handleEventsUpdate}
                    />
                    
                    <EmailList 
                      emails={emailData.summarized_emails}
                      title="Important Emails"
                    />
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-white shadow rounded-lg p-6">
                <h2 className="text-lg font-medium text-gray-900 mb-4">
                  Getting Started
                </h2>
                <p className="text-gray-600">
                  Please connect your Google account above to start using the email assistant features.
                </p>
              </div>
            )
          )}
        </div>
      </main>
    </div>
  );
};

export default Dashboard;