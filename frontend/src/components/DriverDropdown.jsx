import React, { useState, useEffect, useRef } from 'react';
import { getAllDrivers, getDriverDetails } from '../api';

const DriverDropdown = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [drivers, setDrivers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedDriver, setSelectedDriver] = useState(null);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const dropdownRef = useRef(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
        setSelectedDriver(null);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Fetch drivers when dropdown opens
  useEffect(() => {
    if (isOpen && drivers.length === 0) {
      fetchDrivers();
    }
  }, [isOpen]);

  const fetchDrivers = async () => {
    setLoading(true);
    try {
      const response = await getAllDrivers();
      setDrivers(response.data);
    } catch (error) {
      console.error('Error fetching drivers:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDriverClick = async (driver) => {
    setDetailsLoading(true);
    try {
      const response = await getDriverDetails(driver.driver_id);
      setSelectedDriver(response.data);
    } catch (error) {
      console.error('Error fetching driver details:', error);
    } finally {
      setDetailsLoading(false);
    }
  };

  const getAvailabilityBadge = (availability) => {
    if (!availability) return null;
    
    const statusColors = {
      available: 'bg-green-100 text-green-800 border-green-200',
      unavailable: 'bg-red-100 text-red-800 border-red-200',
      available_upcoming: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    };
    
    const statusIcons = {
      available: '✅',
      unavailable: '🔴',
      available_upcoming: '🟡',
    };
    
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border ${statusColors[availability.status] || 'bg-gray-100 text-gray-800'}`}>
        {statusIcons[availability.status]} {availability.status === 'available' ? 'Available' : availability.status === 'unavailable' ? 'Busy' : 'Upcoming'}
      </span>
    );
  };

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Dropdown Trigger */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 bg-blue-800 hover:bg-blue-900 rounded-lg transition-colors"
      >
        <span className="text-lg">👤</span>
        <span className="font-medium">Drivers</span>
        <svg
          className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-96 bg-white rounded-xl shadow-2xl border border-gray-200 z-50 overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-4 py-3 text-white">
            <h3 className="font-semibold flex items-center gap-2">
              <span>👥</span> All Drivers
            </h3>
            <p className="text-xs text-blue-100 mt-1">Click on a driver to view details</p>
          </div>

          {/* Driver List or Details */}
          <div className="max-h-96 overflow-y-auto">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            ) : selectedDriver ? (
              /* Driver Details Panel */
              <div className="p-4">
                <button
                  onClick={() => setSelectedDriver(null)}
                  className="flex items-center gap-1 text-blue-600 hover:text-blue-800 mb-4 text-sm font-medium"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                  Back to list
                </button>

                {detailsLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {/* Driver Info Header */}
                    <div className="flex items-center gap-4">
                      <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center text-white text-2xl font-bold">
                        {selectedDriver.name?.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <h4 className="text-lg font-bold text-gray-900">{selectedDriver.name}</h4>
                        <p className="text-sm text-gray-500">Driver ID: {selectedDriver.driver_id}</p>
                      </div>
                    </div>

                    {/* Availability Status */}
                    <div className={`p-3 rounded-lg ${
                      selectedDriver.availability?.status === 'available' ? 'bg-green-50 border border-green-200' :
                      selectedDriver.availability?.status === 'unavailable' ? 'bg-red-50 border border-red-200' :
                      'bg-yellow-50 border border-yellow-200'
                    }`}>
                      <p className={`font-medium ${
                        selectedDriver.availability?.status === 'available' ? 'text-green-800' :
                        selectedDriver.availability?.status === 'unavailable' ? 'text-red-800' :
                        'text-yellow-800'
                      }`}>
                        {selectedDriver.availability?.message || 'Status unknown'}
                      </p>
                    </div>

                    {/* Driver Details Grid */}
                    <div className="grid grid-cols-2 gap-3">
                      <div className="bg-gray-50 p-3 rounded-lg">
                        <p className="text-xs text-gray-500 mb-1">Phone</p>
                        <p className="font-medium text-gray-900">{selectedDriver.phone || 'N/A'}</p>
                      </div>
                      <div className="bg-gray-50 p-3 rounded-lg">
                        <p className="text-xs text-gray-500 mb-1">License</p>
                        <p className="font-medium text-gray-900">{selectedDriver.license_number || 'N/A'}</p>
                      </div>
                      <div className="bg-gray-50 p-3 rounded-lg">
                        <p className="text-xs text-gray-500 mb-1">Status</p>
                        <p className="font-medium text-gray-900 capitalize">{selectedDriver.status || 'N/A'}</p>
                      </div>
                      <div className="bg-gray-50 p-3 rounded-lg">
                        <p className="text-xs text-gray-500 mb-1">Trips Today</p>
                        <p className="font-medium text-gray-900">{selectedDriver.todays_trips?.length || 0}</p>
                      </div>
                    </div>

                    {/* Today's Trips */}
                    {selectedDriver.todays_trips && selectedDriver.todays_trips.length > 0 && (
                      <div>
                        <h5 className="font-medium text-gray-700 mb-2 flex items-center gap-2">
                          <span>🚌</span> Today's Trips
                        </h5>
                        <div className="space-y-2">
                          {selectedDriver.todays_trips.map((trip, idx) => (
                            <div key={idx} className="flex items-center justify-between p-2 bg-gray-50 rounded-lg text-sm">
                              <div>
                                <p className="font-medium text-gray-900">{trip.display_name}</p>
                                <p className="text-xs text-gray-500">
                                  {trip.shift_time ? String(trip.shift_time).slice(0, 5) : 'Time TBD'}
                                </p>
                              </div>
                              <span className={`px-2 py-1 rounded text-xs font-medium ${
                                trip.live_status === 'COMPLETED' ? 'bg-green-100 text-green-700' :
                                trip.live_status === 'IN_PROGRESS' ? 'bg-blue-100 text-blue-700' :
                                trip.live_status === 'CANCELLED' ? 'bg-red-100 text-red-700' :
                                'bg-gray-100 text-gray-700'
                              }`}>
                                {trip.live_status}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ) : (
              /* Driver List */
              <div className="divide-y divide-gray-100">
                {drivers.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <span className="text-3xl">👤</span>
                    <p className="mt-2">No drivers found</p>
                  </div>
                ) : (
                  drivers.map((driver) => (
                    <div
                      key={driver.driver_id}
                      onClick={() => handleDriverClick(driver)}
                      className="flex items-center justify-between px-4 py-3 hover:bg-gray-50 cursor-pointer transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center text-white font-bold">
                          {driver.name?.charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">{driver.name}</p>
                          <p className="text-xs text-gray-500">{driver.phone || 'No phone'}</p>
                        </div>
                      </div>
                      {getAvailabilityBadge(driver.availability)}
                    </div>
                  ))
                )}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="bg-gray-50 px-4 py-2 border-t border-gray-200">
            <p className="text-xs text-gray-500 text-center">
              {drivers.length} driver{drivers.length !== 1 ? 's' : ''} total
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default DriverDropdown;
