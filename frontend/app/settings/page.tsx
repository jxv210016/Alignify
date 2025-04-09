'use client'

import React, { useState } from 'react'

interface AccountSettings {
  name: string;
  email: string;
  avatar: string;
}

interface PreferenceSettings {
  darkMode: boolean;
  notifications: boolean;
  sessionReminders: boolean;
  weeklyGoal: number;
  goalUnit: string;
}

interface PrivacySettings {
  shareProgress: boolean;
  publicProfile: boolean;
  anonymousData: boolean;
}

interface AppSettings {
  account: AccountSettings;
  preferences: PreferenceSettings;
  privacy: PrivacySettings;
}

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('account')
  
  const [settings, setSettings] = useState<AppSettings>({
    account: {
      name: 'Jane Doe',
      email: 'jane.doe@example.com',
      avatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?q=80&w=200'
    },
    preferences: {
      darkMode: false,
      notifications: true,
      sessionReminders: true,
      weeklyGoal: 3,
      goalUnit: 'sessions'
    },
    privacy: {
      shareProgress: false,
      publicProfile: false,
      anonymousData: true
    }
  })

  const handleToggle = (section: keyof AppSettings, setting: string) => {
    setSettings(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [setting]: !prev[section][setting as keyof typeof prev[typeof section]]
      }
    }))
  }

  const handleChange = (section: keyof AppSettings, setting: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [setting]: value
      }
    }))
  }

  return (
    <div className="p-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold">Settings</h1>
          <p className="text-gray-500 mt-1">Manage your account preferences and settings</p>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        {/* Tabs */}
        <div className="flex border-b">
          <button 
            className={`px-6 py-4 font-medium text-sm ${activeTab === 'account' ? 'border-b-2 border-indigo-600 text-indigo-600' : 'text-gray-500 hover:text-gray-700'}`}
            onClick={() => setActiveTab('account')}
          >
            Account
          </button>
          <button 
            className={`px-6 py-4 font-medium text-sm ${activeTab === 'preferences' ? 'border-b-2 border-indigo-600 text-indigo-600' : 'text-gray-500 hover:text-gray-700'}`}
            onClick={() => setActiveTab('preferences')}
          >
            Preferences
          </button>
          <button 
            className={`px-6 py-4 font-medium text-sm ${activeTab === 'privacy' ? 'border-b-2 border-indigo-600 text-indigo-600' : 'text-gray-500 hover:text-gray-700'}`}
            onClick={() => setActiveTab('privacy')}
          >
            Privacy
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Account Settings */}
          {activeTab === 'account' && (
            <div>
              <div className="flex items-center space-x-6 mb-6">
                <div className="w-20 h-20 rounded-full overflow-hidden">
                  <img 
                    src={settings.account.avatar}
                    alt="Profile" 
                    className="w-full h-full object-cover"
                  />
                </div>
                <div>
                  <h3 className="font-medium">{settings.account.name}</h3>
                  <p className="text-gray-500 text-sm">{settings.account.email}</p>
                  <button className="text-indigo-600 text-sm font-medium mt-2">
                    Change photo
                  </button>
                </div>
              </div>

              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Full Name
                  </label>
                  <input 
                    type="text" 
                    value={settings.account.name}
                    onChange={(e) => handleChange('account', 'name', e.target.value)}
                    className="w-full p-2 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email
                  </label>
                  <input 
                    type="email" 
                    value={settings.account.email}
                    onChange={(e) => handleChange('account', 'email', e.target.value)}
                    className="w-full p-2 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Password
                  </label>
                  <input 
                    type="password" 
                    value="••••••••"
                    readOnly
                    className="w-full p-2 border rounded-lg"
                  />
                  <button className="text-indigo-600 text-sm font-medium mt-2">
                    Change password
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Preferences Settings */}
          {activeTab === 'preferences' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium">Dark Mode</h3>
                  <p className="text-gray-500 text-sm">Use dark theme throughout the application</p>
                </div>
                <div className="relative inline-block w-12 align-middle select-none">
                  <input 
                    type="checkbox" 
                    checked={settings.preferences.darkMode}
                    onChange={() => handleToggle('preferences', 'darkMode')}
                    className="toggle-checkbox absolute block w-6 h-6 rounded-full bg-white border-4 appearance-none cursor-pointer"
                  />
                  <label 
                    className={`toggle-label block overflow-hidden h-6 rounded-full cursor-pointer ${settings.preferences.darkMode ? 'bg-indigo-600' : 'bg-gray-300'}`}
                  ></label>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium">Notifications</h3>
                  <p className="text-gray-500 text-sm">Receive notifications about your practice</p>
                </div>
                <div className="relative inline-block w-12 align-middle select-none">
                  <input 
                    type="checkbox" 
                    checked={settings.preferences.notifications}
                    onChange={() => handleToggle('preferences', 'notifications')}
                    className="toggle-checkbox absolute block w-6 h-6 rounded-full bg-white border-4 appearance-none cursor-pointer"
                  />
                  <label 
                    className={`toggle-label block overflow-hidden h-6 rounded-full cursor-pointer ${settings.preferences.notifications ? 'bg-indigo-600' : 'bg-gray-300'}`}
                  ></label>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium">Session Reminders</h3>
                  <p className="text-gray-500 text-sm">Get reminders for scheduled yoga sessions</p>
                </div>
                <div className="relative inline-block w-12 align-middle select-none">
                  <input 
                    type="checkbox" 
                    checked={settings.preferences.sessionReminders}
                    onChange={() => handleToggle('preferences', 'sessionReminders')}
                    className="toggle-checkbox absolute block w-6 h-6 rounded-full bg-white border-4 appearance-none cursor-pointer"
                  />
                  <label 
                    className={`toggle-label block overflow-hidden h-6 rounded-full cursor-pointer ${settings.preferences.sessionReminders ? 'bg-indigo-600' : 'bg-gray-300'}`}
                  ></label>
                </div>
              </div>

              <div>
                <h3 className="font-medium mb-2">Weekly Goal</h3>
                <div className="flex items-center space-x-4">
                  <input 
                    type="number" 
                    min="1" 
                    max="7" 
                    value={settings.preferences.weeklyGoal}
                    onChange={(e) => handleChange('preferences', 'weeklyGoal', parseInt(e.target.value))}
                    className="w-20 p-2 border rounded-lg"
                  />
                  <select 
                    value={settings.preferences.goalUnit}
                    onChange={(e) => handleChange('preferences', 'goalUnit', e.target.value)}
                    className="p-2 border rounded-lg"
                  >
                    <option value="sessions">Sessions</option>
                    <option value="minutes">Minutes</option>
                    <option value="poses">Poses</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* Privacy Settings */}
          {activeTab === 'privacy' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium">Share Progress</h3>
                  <p className="text-gray-500 text-sm">Allow sharing your progress on social media</p>
                </div>
                <div className="relative inline-block w-12 align-middle select-none">
                  <input 
                    type="checkbox" 
                    checked={settings.privacy.shareProgress}
                    onChange={() => handleToggle('privacy', 'shareProgress')}
                    className="toggle-checkbox absolute block w-6 h-6 rounded-full bg-white border-4 appearance-none cursor-pointer"
                  />
                  <label 
                    className={`toggle-label block overflow-hidden h-6 rounded-full cursor-pointer ${settings.privacy.shareProgress ? 'bg-indigo-600' : 'bg-gray-300'}`}
                  ></label>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium">Public Profile</h3>
                  <p className="text-gray-500 text-sm">Make your profile visible to other users</p>
                </div>
                <div className="relative inline-block w-12 align-middle select-none">
                  <input 
                    type="checkbox" 
                    checked={settings.privacy.publicProfile}
                    onChange={() => handleToggle('privacy', 'publicProfile')}
                    className="toggle-checkbox absolute block w-6 h-6 rounded-full bg-white border-4 appearance-none cursor-pointer"
                  />
                  <label 
                    className={`toggle-label block overflow-hidden h-6 rounded-full cursor-pointer ${settings.privacy.publicProfile ? 'bg-indigo-600' : 'bg-gray-300'}`}
                  ></label>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium">Anonymous Data Collection</h3>
                  <p className="text-gray-500 text-sm">Allow anonymous usage data to improve the app</p>
                </div>
                <div className="relative inline-block w-12 align-middle select-none">
                  <input 
                    type="checkbox" 
                    checked={settings.privacy.anonymousData}
                    onChange={() => handleToggle('privacy', 'anonymousData')}
                    className="toggle-checkbox absolute block w-6 h-6 rounded-full bg-white border-4 appearance-none cursor-pointer"
                  />
                  <label 
                    className={`toggle-label block overflow-hidden h-6 rounded-full cursor-pointer ${settings.privacy.anonymousData ? 'bg-indigo-600' : 'bg-gray-300'}`}
                  ></label>
                </div>
              </div>

              <div className="pt-4 border-t">
                <button className="text-red-600 text-sm font-medium">
                  Delete Account
                </button>
                <p className="text-gray-500 text-xs mt-1">
                  This will permanently delete your account and all associated data
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 flex justify-end">
          <button className="px-4 py-2 border border-gray-300 rounded-md text-sm mr-3">
            Cancel
          </button>
          <button className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm">
            Save Changes
          </button>
        </div>
      </div>
    </div>
  )
} 