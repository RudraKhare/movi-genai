import { useState } from 'react';
import { forceStatusUpdate as forceUpdate, getStatusInfo as getInfo } from '../api';

const StatusControlPanel = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);

  const forceStatusUpdate = async () => {
    setIsUpdating(true);
    try {
      const response = await forceUpdate();

      if (response.status === 200) {
        const result = response.data;
        setLastUpdate(new Date().toLocaleTimeString());
        console.log('✅ Forced status update completed');
        
        // Trigger a refresh of the dashboard
        window.location.reload();
      } else {
        console.error('Failed to force update:', response.data);
      }
    } catch (error) {
      console.error('Error forcing update:', error.response?.data || error.message);
    } finally {
      setIsUpdating(false);
    }
  };

  const getStatusInfo = async () => {
    try {
      const response = await getInfo();
      if (response.status === 200) {
        const info = response.data;
        console.log('📊 Status Updater Info:', info);
        
        const message = `
Status Updater: ${info.status_updater_running ? '✅ Running' : '❌ Stopped'}
Update Interval: ${info.update_interval_seconds}s
Trip Duration: ${info.trip_duration_hours}h
Valid Statuses: ${info.valid_statuses?.join(', ')}

Auto Transitions:
• SCHEDULED → IN_PROGRESS: ${info.automatic_transitions?.SCHEDULED_to_IN_PROGRESS}
• IN_PROGRESS → COMPLETED: ${info.automatic_transitions?.IN_PROGRESS_to_COMPLETED}
        `.trim();
        
        alert(message);
      }
    } catch (error) {
      console.error('Error getting status info:', error.response?.data || error.message);
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="bg-blue-800 hover:bg-blue-900 px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-1"
        title="Status Control Panel"
      >
        <span>⚡</span>
        <span className="hidden sm:inline">Status</span>
      </button>
    );
  }

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(false)}
        className="bg-blue-800 hover:bg-blue-900 px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-1"
      >
        <span>⚡</span>
        <span className="hidden sm:inline">Status</span>
        <span>▼</span>
      </button>
      
      <div className="absolute top-full right-0 mt-2 bg-white text-gray-900 border rounded-lg shadow-xl p-4 min-w-[280px] z-50">
        <div className="mb-3">
          <h3 className="font-bold text-gray-800 flex items-center gap-2">
            <span>⚡</span>
            Status Control Panel
          </h3>
          <p className="text-xs text-gray-600 mt-1">Manage automatic trip status updates</p>
        </div>
        
        <div className="space-y-3">
          <button
            onClick={forceStatusUpdate}
            disabled={isUpdating}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-3 py-2 rounded font-medium transition-colors flex items-center justify-center gap-2"
          >
            {isUpdating ? (
              <>
                <span className="animate-spin">⟳</span>
                <span>Updating...</span>
              </>
            ) : (
              <>
                <span>🔄</span>
                <span>Force Update Now</span>
              </>
            )}
          </button>
          
          <button
            onClick={getStatusInfo}
            className="w-full bg-gray-600 hover:bg-gray-700 text-white px-3 py-2 rounded font-medium transition-colors flex items-center justify-center gap-2"
          >
            <span>📊</span>
            <span>View Status Info</span>
          </button>
          
          <div className="border-t pt-3">
            <div className="text-xs text-gray-600 space-y-1">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                <span>Auto-updates every 60s</span>
              </div>
              {lastUpdate && (
                <div>Last manual update: {lastUpdate}</div>
              )}
              <div className="text-gray-500 mt-2">
                💡 Hover over status badges for manual override
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StatusControlPanel;
