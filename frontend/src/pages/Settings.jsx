import React, { useState } from 'react';

function Settings() {
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [feedbackLevel, setFeedbackLevel] = useState("moderate");
  const [cameraResolution, setCameraResolution] = useState("720p");

  return (
    <div>
      <h1 className="text-3xl font-bold mb-8">Settings</h1>
      
      <div className="bg-gray-50 rounded p-6 shadow-sm mb-6">
        <h2 className="text-xl font-bold mb-4">Application Settings</h2>
        
        <div className="space-y-6">
          <div>
            <h3 className="font-bold mb-2">Notifications</h3>
            <div className="flex items-center">
              <label className="inline-flex items-center cursor-pointer">
                <input 
                  type="checkbox" 
                  className="sr-only"
                  checked={notificationsEnabled}
                  onChange={e => setNotificationsEnabled(e.target.checked)}
                />
                <div className={`relative w-11 h-6 rounded-full transition ${notificationsEnabled ? 'bg-purple-600' : 'bg-gray-300'}`}>
                  <div className={`absolute w-4 h-4 bg-white rounded-full top-1 transition-all ${notificationsEnabled ? 'left-6' : 'left-1'}`}></div>
                </div>
                <span className="ml-3">{notificationsEnabled ? 'Enabled' : 'Disabled'}</span>
              </label>
            </div>
          </div>
          
          <div>
            <h3 className="font-bold mb-2">Feedback Level</h3>
            <select 
              value={feedbackLevel}
              onChange={e => setFeedbackLevel(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded w-full max-w-xs focus:outline-none focus:border-purple-600"
            >
              <option value="minimal">Minimal</option>
              <option value="moderate">Moderate</option>
              <option value="detailed">Detailed</option>
            </select>
          </div>
          
          <div>
            <h3 className="font-bold mb-2">Camera Resolution</h3>
            <select 
              value={cameraResolution}
              onChange={e => setCameraResolution(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded w-full max-w-xs focus:outline-none focus:border-purple-600"
            >
              <option value="480p">480p</option>
              <option value="720p">720p (Recommended)</option>
              <option value="1080p">1080p</option>
            </select>
          </div>
        </div>
      </div>
      
      <div className="bg-gray-50 rounded p-6 shadow-sm">
        <h2 className="text-xl font-bold mb-4">Account</h2>
        <button className="bg-red-600 text-white px-4 py-2 rounded">
          Sign Out
        </button>
      </div>
    </div>
  );
}

export default Settings; 