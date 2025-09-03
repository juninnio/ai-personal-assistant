// components/dashboard/PendingEvents.jsx
import React, { useState } from 'react';
import { Button } from '../ui';
import { emailService } from '../../services/email.service';

const PendingEvents = ({ events, onEventAddedToCalendar, onEventIgnored, onEventsUpdate }) => {
  const [loadingStates, setLoadingStates] = useState({});

  const setLoading = (eventId, isLoading) => {
    setLoadingStates(prev => ({
      ...prev,
      [eventId]: isLoading
    }));
  };


  const handleAddToCalendar = async (event) => {
    try {
      setLoading(event.id, true);
      
      // Optimistically remove from UI immediately
      onEventAddedToCalendar(event.email_id);
      
      // Make API call in background
      await emailService.addToCalendar(event.email_id);
      
    } catch (err) {
      console.error('Error adding to calendar:', err);
      alert('Failed to add event to calendar: ' + err.message);
      // Re-fetch data on error to restore correct state
      onEventsUpdate();
    } finally {
      setLoading(event.id, false);
    }
  };

  const handleIgnoreEvent = async (event) => {
    try {
      setLoading(event.id, true);
      
      // Optimistically remove from UI immediately
      onEventIgnored(event.email_id);
      
      
      // Make API call in background
      await emailService.ignoreEvent(event.email_id);
      
    } catch (err) {
      console.error('Error ignoring event:', err);
      alert('Failed to ignore event: ' + err.message);
      // Re-fetch data on error to restore correct state
      onEventsUpdate();
    } finally {
      setLoading(event.id, false);
    }
  };

  if (!events || events.length === 0) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          Pending Events
        </h3>
        <p className="text-gray-500 text-center py-8">
          No pending events found
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">
        Pending Events ({events.length})
      </h3>
      
      <div className="space-y-6">
        {events.map((event) => (
          <div key={event.id} className="border border-gray-200 rounded-lg p-4">
            <div className="flex justify-between items-start mb-3">
              <div className="flex-1">
                <h4 className="font-medium text-gray-900">
                  {event.subject || 'No Subject'}
                </h4>
                <p className="text-sm text-gray-600">
                  From: {event.sender}
                </p>
              </div>
              
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                Pending Event
              </span>
            </div>
            
            <div className="text-sm text-gray-700 mb-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <p><strong>Event:</strong> {event.content.event_name}</p>
                  <p><strong>Type:</strong> {event.content.event_type}</p>
                </div>
                <div>
                  <p><strong>Start:</strong> {new Date(event.content.event_start).toLocaleString()}</p>
                  <p><strong>End:</strong> {new Date(event.content.event_end).toLocaleString()}</p>
                </div>
              </div>
              <p className="mt-3 text-gray-600">{event.content.event_summary}</p>
            </div>
            
            <div className="flex justify-end space-x-3">
              <Button
                variant="outline"
                size="sm"
                loading={loadingStates[event.id]}
                onClick={() => handleIgnoreEvent(event)}
              >
                Ignore
              </Button>
              
              <Button
                variant="primary"
                size="sm"
                loading={loadingStates[event.id]}
                onClick={() => handleAddToCalendar(event)}
              >
                Add to Calendar
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default PendingEvents;