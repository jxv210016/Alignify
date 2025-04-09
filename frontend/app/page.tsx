import YogaInterface from '@/components/YogaInterface'

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Stats Cards */}
        <div className="p-6 bg-white rounded-xl shadow-sm">
          <h3 className="text-lg font-semibold mb-2">Total Sessions</h3>
          <p className="text-3xl font-bold">12</p>
        </div>
        <div className="p-6 bg-white rounded-xl shadow-sm">
          <h3 className="text-lg font-semibold mb-2">Minutes Practiced</h3>
          <p className="text-3xl font-bold">180</p>
        </div>
        <div className="p-6 bg-white rounded-xl shadow-sm">
          <h3 className="text-lg font-semibold mb-2">Perfect Poses</h3>
          <p className="text-3xl font-bold">24</p>
        </div>
      </div>
      
      {/* Recent Activity */}
      <div className="mt-8">
        <h2 className="text-2xl font-semibold mb-4">Recent Activity</h2>
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <div className="p-4 border-b">
            <p className="font-medium">Morning Yoga Session</p>
            <p className="text-sm text-gray-500">Today, 8:00 AM</p>
          </div>
          <div className="p-4 border-b">
            <p className="font-medium">Evening Stretches</p>
            <p className="text-sm text-gray-500">Yesterday, 6:30 PM</p>
          </div>
          <div className="p-4">
            <p className="font-medium">Warrior Pose Practice</p>
            <p className="text-sm text-gray-500">2 days ago</p>
          </div>
        </div>
      </div>
    </div>
  )
} 