import React from 'react';

const ConsequenceCard = ({ message, onConfirm, awaitingConfirm }) => {
  const { action, trip_id, consequences, message: msgText } = message;

  // Generate human-readable consequence description
  const getConsequenceDescription = () => {
    if (!consequences) return null;

    const items = [];

    if (consequences.booked_count !== undefined || consequences.booking_count !== undefined) {
      const count = consequences.booked_count || consequences.booking_count;
      items.push({
        icon: (
          <svg className="w-5 h-5 text-orange-500" fill="currentColor" viewBox="0 0 20 20">
            <path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z" />
          </svg>
        ),
        text: `${count} passenger${count !== 1 ? 's' : ''} with active bookings`,
        highlight: count > 0,
      });
    }

    if (consequences.booking_percentage !== undefined) {
      const pct = consequences.booking_percentage;
      items.push({
        icon: (
          <svg className="w-5 h-5 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
            <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z" />
          </svg>
        ),
        text: `${pct}% capacity filled`,
        highlight: pct > 50,
      });
    }

    if (consequences.is_deployed !== undefined || consequences.has_deployment !== undefined) {
      const deployed = consequences.is_deployed || consequences.has_deployment;
      if (deployed) {
        items.push({
          icon: (
            <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
            </svg>
          ),
          text: 'Vehicle is currently deployed',
          highlight: true,
        });
      }
    }

    if (consequences.vehicle_id) {
      items.push({
        icon: (
          <svg className="w-5 h-5 text-purple-500" fill="currentColor" viewBox="0 0 20 20">
            <path d="M8 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0zM15 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0z" />
            <path d="M3 4a1 1 0 00-1 1v10a1 1 0 001 1h1.05a2.5 2.5 0 014.9 0H10a1 1 0 001-1V5a1 1 0 00-1-1H3zM14 7a1 1 0 00-1 1v6.05A2.5 2.5 0 0115.95 16H17a1 1 0 001-1v-5a1 1 0 00-.293-.707l-2-2A1 1 0 0015 7h-1z" />
          </svg>
        ),
        text: `Vehicle ID: ${consequences.vehicle_id}`,
        highlight: false,
      });
    }

    if (consequences.driver_id) {
      items.push({
        icon: (
          <svg className="w-5 h-5 text-indigo-500" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
          </svg>
        ),
        text: `Driver ID: ${consequences.driver_id}`,
        highlight: false,
      });
    }

    if (consequences.live_status) {
      const status = consequences.live_status;
      const isActive = status === 'in_transit' || status === 'SCHEDULED';
      items.push({
        icon: (
          <svg className="w-5 h-5 text-yellow-500" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
          </svg>
        ),
        text: `Status: ${status}`,
        highlight: isActive,
      });
    }

    return items;
  };

  const consequenceItems = getConsequenceDescription();

  // Determine risk level
  const getRiskLevel = () => {
    if (!consequences) return 'low';
    
    const bookingCount = consequences.booked_count || consequences.booking_count || 0;
    const bookingPct = consequences.booking_percentage || 0;
    const liveStatus = consequences.live_status || '';
    
    if (bookingCount > 5 || bookingPct > 70 || liveStatus === 'in_transit') {
      return 'high';
    } else if (bookingCount > 0 || bookingPct > 30) {
      return 'medium';
    }
    return 'low';
  };

  const riskLevel = getRiskLevel();

  const riskColors = {
    high: 'border-red-500 bg-red-50',
    medium: 'border-orange-500 bg-orange-50',
    low: 'border-yellow-500 bg-yellow-50',
  };

  const riskIcons = {
    high: (
      <svg className="w-6 h-6 text-red-500" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
      </svg>
    ),
    medium: (
      <svg className="w-6 h-6 text-orange-500" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
      </svg>
    ),
    low: (
      <svg className="w-6 h-6 text-yellow-500" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
      </svg>
    ),
  };

  return (
    <div className={`border-l-4 ${riskColors[riskLevel]} rounded-r-lg p-4 shadow-md mb-4`}>
      {/* Header */}
      <div className="flex items-start gap-3 mb-3">
        <div className="flex-shrink-0">{riskIcons[riskLevel]}</div>
        <div className="flex-1">
          <h4 className="font-bold text-gray-900 text-lg mb-1">
            ⚠️ Confirmation Required
          </h4>
          <p className="text-sm text-gray-700 mb-2">
            {msgText || `This action will ${action?.replace('_', ' ')} for Trip ${trip_id}.`}
          </p>
        </div>
      </div>

      {/* Consequence Details */}
      {consequenceItems && consequenceItems.length > 0 && (
        <div className="bg-white rounded-lg p-3 mb-3 border border-gray-200">
          <p className="text-xs font-semibold text-gray-600 uppercase mb-2">Impact Analysis</p>
          <div className="space-y-2">
            {consequenceItems.map((item, idx) => (
              <div
                key={idx}
                className={`flex items-center gap-2 ${
                  item.highlight ? 'font-semibold' : ''
                }`}
              >
                {item.icon}
                <span className="text-sm text-gray-700">{item.text}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Action Info */}
      <div className="bg-white rounded-lg p-3 mb-3 border border-gray-200">
        <div className="flex items-center justify-between text-xs">
          <span className="text-gray-600">Action:</span>
          <span className="font-mono font-semibold text-gray-900">{action}</span>
        </div>
        <div className="flex items-center justify-between text-xs mt-1">
          <span className="text-gray-600">Trip ID:</span>
          <span className="font-mono font-semibold text-gray-900">{trip_id}</span>
        </div>
      </div>

      {/* Warning Message */}
      <div className="bg-white rounded-lg p-3 mb-3 border border-gray-200">
        <p className="text-xs text-gray-700">
          <span className="font-semibold">⚡ Please review carefully:</span> This action cannot be undone. 
          {riskLevel === 'high' && ' This is a high-impact operation.'}
        </p>
      </div>

      {/* Timestamp */}
      <p className="text-xs text-gray-500 mb-3">
        {new Date(message.timestamp).toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit',
        })}
      </p>

      {/* Note about buttons */}
      <p className="text-xs text-gray-600 italic text-center">
        Use the buttons below to confirm or cancel
      </p>
    </div>
  );
};

export default ConsequenceCard;
