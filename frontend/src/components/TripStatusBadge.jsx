import { useState, useEffect } from 'react';
import { manualStatusUpdate } from '../api';

const TripStatusBadge = ({ trip, onStatusChange }) => {
  const [currentStatus, setCurrentStatus] = useState(trip.live_status);
  const [isUpdating, setIsUpdating] = useState(false);

  // Update local status when trip prop changes
  useEffect(() => {
    if (trip.live_status !== currentStatus) {
      setCurrentStatus(trip.live_status);
      if (onStatusChange) {
        onStatusChange(trip.trip_id, trip.live_status);
      }
    }
  }, [trip.live_status, currentStatus, onStatusChange, trip.trip_id]);

  // Manual status update function for dispatcher override
  const handleManualStatusUpdate = async (newStatus) => {
    if (currentStatus === newStatus) return;
    
    setIsUpdating(true);
    try {
      const response = await manualStatusUpdate(trip.trip_id, newStatus, 1);

      if (response.status === 200) {
        const result = response.data;
        setCurrentStatus(result.new_status);
        
        // Notify parent component of status change
        if (onStatusChange) {
          onStatusChange(trip.trip_id, result.new_status);
        }
        
        console.log(`✅ Status updated: Trip ${trip.trip_id} → ${result.new_status}`);
      } else {
        console.error('Failed to update status:', response.data);
      }
    } catch (error) {
      console.error('Error updating status:', error.response?.data || error.message);
    } finally {
      setIsUpdating(false);
    }
  };

  const getStatusStyle = (status) => {
    switch (status) {
      case 'COMPLETED':
        return 'bg-green-100 text-green-700 border border-green-200';
      case 'IN_PROGRESS':
        return 'bg-blue-100 text-blue-700 border border-blue-200';
      case 'SCHEDULED':
        return 'bg-yellow-100 text-yellow-700 border border-yellow-200';
      case 'CANCELLED':
        return 'bg-red-100 text-red-700 border border-red-200';
      default:
        return 'bg-gray-100 text-gray-700 border border-gray-200';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'COMPLETED':
        return '✅';
      case 'IN_PROGRESS':
        return '🚛';
      case 'SCHEDULED':
        return '📅';
      case 'CANCELLED':
        return '❌';
      default:
        return '❓';
    }
  };

  return (
    <div className="relative group">
      <span className={`text-xs px-2.5 py-1 rounded-full font-medium whitespace-nowrap flex items-center gap-1 ${getStatusStyle(currentStatus)} ${isUpdating ? 'opacity-50' : ''}`}>
        <span>{getStatusIcon(currentStatus)}</span>
        <span>{currentStatus}</span>
        {isUpdating && <span className="animate-spin">⟳</span>}
      </span>
      
      {/* Quick Status Change Dropdown (appears on hover - for dispatcher use) */}
      <div className="absolute top-full right-0 mt-1 hidden group-hover:block z-50 bg-white border rounded-lg shadow-lg p-2 min-w-[140px]">
        <div className="text-xs text-gray-600 mb-1 font-medium">Quick Update:</div>
        <div className="space-y-1">
          {['SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED'].map((status) => (
            <button
              key={status}
              onClick={(e) => {
                e.stopPropagation();
                handleManualStatusUpdate(status);
              }}
              disabled={status === currentStatus || isUpdating}
              className={`w-full text-left px-2 py-1 text-xs rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1 ${
                status === currentStatus ? 'bg-blue-50 text-blue-700' : ''
              }`}
            >
              <span>{getStatusIcon(status)}</span>
              <span>{status}</span>
            </button>
          ))}
        </div>
        <div className="border-t mt-2 pt-2">
          <div className="text-xs text-gray-500">
            💡 Auto-updates every minute
          </div>
        </div>
      </div>
    </div>
  );
};

export default TripStatusBadge;
