import React from 'react';

function Dashboard() {
  return (
    <div>
      <h1 className="text-3xl font-bold mb-8">Dashboard</h1>
      <div className="grid grid-cols-2 gap-6">
        <div className="bg-gray-50 rounded p-6 shadow-sm">
          <h2 className="text-xl font-bold mb-4">Recent Workouts</h2>
          <p>You haven't completed any workouts yet.</p>
        </div>
        <div className="bg-gray-50 rounded p-6 shadow-sm">
          <h2 className="text-xl font-bold mb-4">Progress</h2>
          <p>Start a workout to track your progress.</p>
        </div>
      </div>
    </div>
  );
}

export default Dashboard; 