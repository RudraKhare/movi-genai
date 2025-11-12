export default function ManageRoute() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-lg px-6 py-4">
        <div className="flex items-center gap-4">
          <div className="text-3xl">⚙️</div>
          <div>
            <h1 className="text-2xl font-bold">Manage Routes</h1>
            <p className="text-sm text-blue-100">Route and path configuration</p>
          </div>
        </div>
      </div>

      <div className="p-8">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
          <div className="text-center">
            <div className="text-6xl mb-4">🗺️</div>
            <h2 className="text-2xl font-bold text-gray-800 mb-2">Coming in Day 6</h2>
            <p className="text-gray-600 max-w-xl mx-auto">
              This section will allow you to manage routes, configure paths, 
              and set up the geographic structure of your transport network.
            </p>
            
            <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
              <div className="bg-gray-50 p-6 rounded-lg border border-gray-200">
                <div className="text-3xl mb-3">📍</div>
                <h3 className="font-semibold text-gray-800 mb-2">Route Management</h3>
                <p className="text-sm text-gray-600">
                  Create, edit, and delete transport routes with pricing and timing
                </p>
              </div>
              
              <div className="bg-gray-50 p-6 rounded-lg border border-gray-200">
                <div className="text-3xl mb-3">🛣️</div>
                <h3 className="font-semibold text-gray-800 mb-2">Path Configuration</h3>
                <p className="text-sm text-gray-600">
                  Define pick-up/drop-off points and sequence for each route
                </p>
              </div>
              
              <div className="bg-gray-50 p-6 rounded-lg border border-gray-200">
                <div className="text-3xl mb-3">⏱️</div>
                <h3 className="font-semibold text-gray-800 mb-2">Timing Setup</h3>
                <p className="text-sm text-gray-600">
                  Configure shift times, stop durations, and travel estimates
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
