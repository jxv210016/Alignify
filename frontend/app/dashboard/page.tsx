'use client';

import React from 'react';

interface TrendData {
  value: string;
  positive: boolean;
}

interface StatCardProps {
  title: string;
  value: string;
  icon: React.ReactNode;
  trend?: TrendData;
}

// Dashboard stat card component
const StatCard = ({ title, value, icon, trend }: StatCardProps) => (
  <div className="bg-white p-6 rounded-xl shadow-sm">
    <div className="flex justify-between items-start">
      <div>
        <p className="text-gray-500 text-sm">{title}</p>
        <h3 className="text-2xl font-bold mt-1">{value}</h3>
        {trend && (
          <p className={`text-xs mt-2 ${trend.positive ? 'text-green-500' : 'text-red-500'}`}>
            {trend.value} {trend.positive ? '↑' : '↓'} from last week
          </p>
        )}
      </div>
      <div className="p-3 bg-indigo-50 rounded-lg">
        {icon}
      </div>
    </div>
  </div>
);

interface ActivityItemProps {
  time: string;
  title: string;
  description: string;
}

// Recent activity item component
const ActivityItem = ({ time, title, description }: ActivityItemProps) => (
  <div className="py-3 border-b border-gray-100 last:border-b-0">
    <div className="flex justify-between mb-1">
      <p className="font-medium">{title}</p>
      <span className="text-xs text-gray-500">{time}</span>
    </div>
    <p className="text-sm text-gray-500">{description}</p>
  </div>
);

export default function Dashboard() {
  return (
    <div className="p-6">
      {/* Page Title */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-gray-500 mt-1">Welcome back! Here's your yoga practice overview</p>
        </div>
        <div className="mt-4 md:mt-0">
          <button className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700">
            Start New Session
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard 
          title="Total Sessions" 
          value="24" 
          trend={{ value: "14%", positive: true }}
          icon={<svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>}
        />
        <StatCard 
          title="Streak" 
          value="5 days" 
          trend={{ value: "2 days", positive: true }}
          icon={<svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>}
        />
        <StatCard 
          title="Perfect Poses" 
          value="86%" 
          trend={{ value: "3%", positive: true }}
          icon={<svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>}
        />
        <StatCard 
          title="Minutes Practiced" 
          value="346" 
          trend={{ value: "12%", positive: false }}
          icon={<svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>}
        />
      </div>

      {/* Activity Feed */}
      <div className="bg-white rounded-xl shadow-sm p-6 mb-8">
        <h2 className="text-xl font-bold mb-4">Recent Activity</h2>
        <div>
          <ActivityItem 
            time="Today" 
            title="Morning Flow Session" 
            description="Completed 20 minute session with 95% accuracy"
          />
          <ActivityItem 
            time="Yesterday" 
            title="Evening Relaxation" 
            description="Completed 15 minute session with 88% accuracy"
          />
          <ActivityItem 
            time="2 days ago" 
            title="Beginner's Flow" 
            description="Completed 25 minute session with 79% accuracy"
          />
          <ActivityItem 
            time="3 days ago" 
            title="Warrior Sequence" 
            description="Completed 30 minute session with 91% accuracy"
          />
        </div>
      </div>

      {/* Recommended Poses */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <h2 className="text-xl font-bold mb-4">Recommended Poses</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {['Warrior I', 'Tree Pose', 'Downward Dog', 'Triangle'].map((pose) => (
            <div key={pose} className="bg-gray-50 rounded-lg p-4 text-center hover:bg-indigo-50 transition-colors cursor-pointer">
              <div className="h-24 w-full bg-gray-200 rounded-lg mb-3 flex items-center justify-center">
                <span className="text-gray-400">Pose Image</span>
              </div>
              <p className="font-medium">{pose}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
} 