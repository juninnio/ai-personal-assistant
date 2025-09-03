// components/dashboard/EmailList.jsx
import React from 'react';

const EmailList = ({ emails, title }) => {
  if (!emails || emails.length === 0) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">{title}</h3>
        <p className="text-gray-500 text-center py-8">
          No {title.toLowerCase()} found
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">
        {title} ({emails.length})
      </h3>
      
      <div className="space-y-4">
        {emails.map((email) => (
          <div key={email.id} className="border border-gray-200 rounded-lg p-4">
            <div className="flex justify-between items-start mb-2">
              <div className="flex-1">
                <h4 className="font-medium text-gray-900 truncate">
                  {email.subject || 'No Subject'}
                </h4>
                <p className="text-sm text-gray-600 truncate">
                  From: {email.sender}
                </p>
              </div>
              
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                {email.category}
              </span>
            </div>
            
            <div className="text-sm text-gray-700">
              {email.category === 'event' ? (
                <div>
                  <p><strong>Event:</strong> {email.content.event_name}</p>
                  <p><strong>Type:</strong> {email.content.event_type}</p>
                  <p><strong>Start:</strong> {new Date(email.content.event_start).toLocaleString()}</p>
                  <p><strong>End:</strong> {new Date(email.content.event_end).toLocaleString()}</p>
                  <p className="mt-2">{email.content.event_summary}</p>
                </div>
              ) : (
                <p>{email.content.email_summary}</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default EmailList;