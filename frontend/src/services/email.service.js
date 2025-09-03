// services/email.service.js

const API_BASE_URL = 'http://localhost:8000';

/**
 * Make authenticated API request
 */
const apiRequest = async (endpoint, options = {}) => {
  const token = localStorage.getItem('token');
  
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
  const data = await response.json();

  if (!response.ok) {
    if (response.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('username');
      localStorage.removeItem('user_id');
      throw new Error('Session expired. Please login again.');
    }
    throw new Error(data.detail || 'Request failed');
  }

  return data;
};

/**
 * Email service for handling email operations
 */
export const emailService = {
  /**
   * Fetch and process emails
   * @param {number} emailCount - Number of emails to fetch (default: 10)
   * @returns {Promise} - Processed emails data
   */
  fetchAndProcessEmails: async (emailCount = 10) => {
    return apiRequest('/fetch-emails', {
      method: 'POST',
      body: JSON.stringify({ email_count: emailCount }),
    });
  },

  /**
   * Add event to Google Calendar
   * @param {string} emailId - Email ID of the event
   * @returns {Promise} - Calendar event data
   */
  addToCalendar: async (emailId) => {
    return apiRequest(`/add-to-calendar/${emailId}`, {
      method: 'POST',
    });
  },

  /**
   * Ignore an event (won't show in pending events)
   * @param {string} emailId - Email ID to ignore
   * @returns {Promise} - Success message
   */
  ignoreEvent: async (emailId) => {
    return apiRequest(`/ignore-event/${emailId}`, {
      method: 'DELETE',
    });
  },

  /**
   * Get dashboard data (same as fetch emails but cleaner naming)
   * @returns {Promise} - Dashboard data
   */
  getDashboardData: async () => {
    return apiRequest('/dashboard-data');
  },

  /**
   * Get ignored events list
   * @returns {Promise} - List of ignored event IDs
   */
  getIgnoredEvents: async () => {
    return apiRequest('/ignored-events');
  },

  /**
   * Remove event from ignored list
   * @param {string} emailId - Email ID to remove from ignored list
   * @returns {Promise} - Success message
   */
  removeFromIgnored: async (emailId) => {
    return apiRequest(`/ignored-events/${emailId}`, {
      method: 'DELETE',
    });
  },
};