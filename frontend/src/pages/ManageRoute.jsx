import { useState, useEffect } from 'react'

export default function ManageRoute() {
  const [apiHealth, setApiHealth] = useState(null)

  useEffect(() => {
    // Test API connection
    fetch('http://localhost:8000/health')
      .then(res => res.json())
      .then(data => setApiHealth(data))
      .catch(err => console.error('API connection failed:', err))
  }, [])

  return (
    <div className="px-4 py-6 sm:px-0" data-testid="manage-route-page">
      <div className="bg-white shadow rounded-lg p-6">
        <div className="border-b border-gray-200 pb-4 mb-4">
          <h2 className="text-2xl font-bold text-gray-900">Manage Routes</h2>
          <p className="mt-1 text-sm text-gray-600">
            Configure stops, paths, and routes (Bootstrap placeholder)
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
        </div>

        {/* Data Flow Explanation */}
        <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-semibold text-blue-900 mb-2">Data Flow: Stop → Path → Route</h3>
          <ol className="text-sm text-blue-800 space-y-1 list-decimal list-inside">
            <li><strong>Stops</strong> are individual locations (e.g., "Gavipuram", "Peenya")</li>
            <li><strong>Paths</strong> are ordered sequences of stops</li>
            <li><strong>Routes</strong> are paths with specific times and schedules</li>
          </ol>
        </div>

        {/* Placeholder Content */}
        <div className="space-y-6">
          {/* Stops Section */}
          <div className="border border-gray-200 rounded-lg p-4">
            <h3 className="font-semibold text-gray-700 mb-2">Stops</h3>
            <p className="text-sm text-gray-500 mb-4">
              TODO: Display and manage stops
            </p>
            <div className="space-y-2">
              <div className="bg-gray-50 p-3 rounded flex justify-between items-center">
                <div>
                  <div className="text-sm font-medium">Gavipuram</div>
                  <div className="text-xs text-gray-500">12.9352° N, 77.5847° E</div>
                </div>
                <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">Active</span>
              </div>
              <div className="bg-gray-50 p-3 rounded flex justify-between items-center">
                <div>
                  <div className="text-sm font-medium">Peenya</div>
                  <div className="text-xs text-gray-500">13.0358° N, 77.5200° E</div>
                </div>
                <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">Active</span>
              </div>
            </div>
          </div>

          {/* Paths Section */}
          <div className="border border-gray-200 rounded-lg p-4">
            <h3 className="font-semibold text-gray-700 mb-2">Paths</h3>
            <p className="text-sm text-gray-500 mb-4">
              TODO: Display and manage paths (ordered stop sequences)
            </p>
            <div className="space-y-2">
              <div className="bg-gray-50 p-3 rounded">
                <div className="text-sm font-medium mb-1">Path-1</div>
                <div className="text-xs text-gray-500">
                  Gavipuram → Temple → Peenya (3 stops)
                </div>
              </div>
              <div className="bg-gray-50 p-3 rounded">
                <div className="text-sm font-medium mb-1">Path-2</div>
                <div className="text-xs text-gray-500">
                  Peenya → Industrial Area → Gavipuram (3 stops)
                </div>
              </div>
            </div>
          </div>

          {/* Routes Section */}
          <div className="border border-gray-200 rounded-lg p-4">
            <h3 className="font-semibold text-gray-700 mb-2">Routes</h3>
            <p className="text-sm text-gray-500 mb-4">
              TODO: Display and manage routes (paths + time)
            </p>
            <div className="space-y-2">
              <div className="bg-gray-50 p-3 rounded">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="text-sm font-medium">Path-1 - 09:00</div>
                    <div className="text-xs text-gray-500 mt-1">
                      Morning shift | Gavipuram → Peenya
                    </div>
                  </div>
                  <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">Active</span>
                </div>
              </div>
              <div className="bg-gray-50 p-3 rounded">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="text-sm font-medium">Path-2 - 19:45</div>
                    <div className="text-xs text-gray-500 mt-1">
                      Evening shift | Peenya → Gavipuram
                    </div>
                  </div>
                  <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">Active</span>
                </div>
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
            Ask Movi to create routes, add stops, or explain the path configuration.
          </p>
        </div>
      </div>
    </div>
  )
}
