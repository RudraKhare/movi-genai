import { useState, useEffect } from 'react'

export default function BusDashboard() {
  const [apiHealth, setApiHealth] = useState(null)

  useEffect(() => {
    // Test API connection
    fetch('http://localhost:8000/health')
      .then(res => res.json())
      .then(data => setApiHealth(data))
      .catch(err => console.error('API connection failed:', err))
  }, [])

  return (
    <div className="px-4 py-6 sm:px-0" data-testid="bus-dashboard-page">
      <div className="bg-white shadow rounded-lg p-6">
        <div className="border-b border-gray-200 pb-4 mb-4">
          <h2 className="text-2xl font-bold text-gray-900">Bus Dashboard</h2>
          <p className="mt-1 text-sm text-gray-600">
            Daily operations and trip management (Bootstrap placeholder)
          </p>
        </div>

        {/* API Status Indicator */}
        <div className="mb-6">
          <div className="flex items-center space-x-2">
            <div className={`h-3 w-3 rounded-full ${apiHealth ? 'bg-green-500' : 'bg-gray-300'}`}></div>
            <span className="text-sm text-gray-600">
              Backend API: {apiHealth ? 'Connected' : 'Connecting...'}
            </span>
          </div>
          {apiHealth && (
            <p className="text-xs text-gray-500 mt-1">
              {apiHealth.service} v{apiHealth.version}
            </p>
          )}
        </div>

        {/* Placeholder Content */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="border border-gray-200 rounded-lg p-4">
            <h3 className="font-semibold text-gray-700 mb-2">Daily Trips</h3>
            <p className="text-sm text-gray-500">
              TODO: Display list of trips (e.g., "Bulk - 00:01")
            </p>
            <div className="mt-4 space-y-2">
              <div className="bg-gray-50 p-3 rounded">
                <div className="flex justify-between">
                  <span className="text-sm font-medium">Bulk - 00:01</span>
                  <span className="text-xs text-gray-500">25% booked</span>
                </div>
              </div>
              <div className="bg-gray-50 p-3 rounded">
                <div className="flex justify-between">
                  <span className="text-sm font-medium">Path Path - 00:02</span>
                  <span className="text-xs text-gray-500">10% booked</span>
                </div>
              </div>
            </div>
          </div>

          <div className="border border-gray-200 rounded-lg p-4">
            <h3 className="font-semibold text-gray-700 mb-2">Vehicle Deployments</h3>
            <p className="text-sm text-gray-500">
              TODO: Display vehicles assigned to trips
            </p>
            <div className="mt-4 space-y-2">
              <div className="bg-gray-50 p-3 rounded">
                <div className="text-sm font-medium">MH-12-3456</div>
                <div className="text-xs text-gray-500">Assigned to: Bulk - 00:01</div>
              </div>
              <div className="bg-gray-50 p-3 rounded">
                <div className="text-sm font-medium">KA-01-7890</div>
                <div className="text-xs text-gray-500">Unassigned</div>
              </div>
            </div>
          </div>
        </div>

        {/* Movi Assistant Placeholder */}
        <div className="mt-6 border-t border-gray-200 pt-6">
          <div className="flex items-center space-x-2 text-sm text-gray-600">
            <svg className="h-5 w-5 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
            <span className="font-medium">Movi Assistant</span>
            <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">Coming Soon</span>
          </div>
          <p className="mt-2 text-xs text-gray-500">
            The AI assistant will be integrated here to help with trip management, vehicle assignments, and more.
          </p>
        </div>
      </div>
    </div>
  )
}
