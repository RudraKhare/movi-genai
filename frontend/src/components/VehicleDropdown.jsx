import React, { useState, useEffect, useRef } from 'react';
import { getAllVehicles, getVehicleDetails } from '../api';

const VehicleDropdown = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [vehicles, setVehicles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedVehicle, setSelectedVehicle] = useState(null);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [showOnlyAvailable, setShowOnlyAvailable] = useState(false);
  const dropdownRef = useRef(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
        setSelectedVehicle(null);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Fetch vehicles when dropdown opens
  useEffect(() => {
    if (isOpen && vehicles.length === 0) {
      fetchVehicles();
    }
  }, [isOpen]);

  const fetchVehicles = async () => {
    setLoading(true);
    try {
      const response = await getAllVehicles();
      setVehicles(response.data);
    } catch (error) {
      console.error('Error fetching vehicles:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleVehicleClick = async (vehicle) => {
    setDetailsLoading(true);
    try {
      const response = await getVehicleDetails(vehicle.vehicle_id);
      setSelectedVehicle(response.data);
    } catch (error) {
      console.error('Error fetching vehicle details:', error);
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
      maintenance: 'bg-orange-100 text-orange-800 border-orange-200',
    };
    
    const statusIcons = {
      available: '✅',
      unavailable: '🔴',
      available_upcoming: '🟡',
      maintenance: '🔧',
    };
    
    const statusLabels = {
      available: 'Available',
      unavailable: 'On Trip',
      available_upcoming: 'Upcoming',
      maintenance: 'Maintenance',
    };
    
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border ${statusColors[availability.status] || 'bg-gray-100 text-gray-800'}`}>
        {statusIcons[availability.status]} {statusLabels[availability.status] || availability.status}
      </span>
    );
  };

  const getVehicleTypeIcon = (type) => {
    return type === 'Bus' ? '🚌' : type === 'Cab' ? '🚕' : '🚗';
  };

  // Filter vehicles if showOnlyAvailable is true
  const filteredVehicles = showOnlyAvailable 
    ? vehicles.filter(v => v.availability?.status !== 'unavailable' && v.availability?.status !== 'maintenance')
    : vehicles;

  const availableCount = vehicles.filter(v => v.availability?.status === 'available' || v.availability?.status === 'available_upcoming').length;

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Dropdown Trigger */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 bg-blue-800 hover:bg-blue-900 rounded-lg transition-colors"
      >
        <span className="text-lg">🚌</span>
        <span className="font-medium">Vehicles</span>
        <span className="bg-green-500 text-white text-xs px-1.5 py-0.5 rounded-full">{availableCount}</span>
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
          <div className="bg-gradient-to-r from-green-600 to-green-700 px-4 py-3 text-white">
            <h3 className="font-semibold flex items-center gap-2">
              <span>🚌</span> Fleet Vehicles
            </h3>
            <p className="text-xs text-green-100 mt-1">Click on a vehicle to view details</p>
          </div>

          {/* Filter Toggle */}
          <div className="px-4 py-2 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
            <span className="text-sm text-gray-600">Show only available</span>
            <button
              onClick={() => setShowOnlyAvailable(!showOnlyAvailable)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                showOnlyAvailable ? 'bg-green-600' : 'bg-gray-300'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  showOnlyAvailable ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          {/* Vehicle List or Details */}
          <div className="max-h-96 overflow-y-auto">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
              </div>
            ) : selectedVehicle ? (
              /* Vehicle Details Panel */
              <div className="p-4">
                <button
                  onClick={() => setSelectedVehicle(null)}
                  className="flex items-center gap-1 text-green-600 hover:text-green-800 mb-4 text-sm font-medium"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                  Back to list
                </button>

                {detailsLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {/* Vehicle Info Header */}
                    <div className="flex items-center gap-4">
                      <div className="w-16 h-16 bg-gradient-to-br from-green-500 to-green-600 rounded-xl flex items-center justify-center text-3xl">
                        {getVehicleTypeIcon(selectedVehicle.vehicle_type)}
                      </div>
                      <div>
                        <h4 className="text-lg font-bold text-gray-900">{selectedVehicle.registration_number}</h4>
                        <p className="text-sm text-gray-500">{selectedVehicle.vehicle_type} • ID: {selectedVehicle.vehicle_id}</p>
                      </div>
                    </div>

                    {/* Availability Status */}
                    <div className={`p-3 rounded-lg ${
                      selectedVehicle.availability?.status === 'available' ? 'bg-green-50 border border-green-200' :
                      selectedVehicle.availability?.status === 'unavailable' ? 'bg-red-50 border border-red-200' :
                      selectedVehicle.availability?.status === 'maintenance' ? 'bg-orange-50 border border-orange-200' :
                      'bg-yellow-50 border border-yellow-200'
                    }`}>
                      <p className={`font-medium ${
                        selectedVehicle.availability?.status === 'available' ? 'text-green-800' :
                        selectedVehicle.availability?.status === 'unavailable' ? 'text-red-800' :
                        selectedVehicle.availability?.status === 'maintenance' ? 'text-orange-800' :
                        'text-yellow-800'
                      }`}>
                        {selectedVehicle.availability?.message || 'Status unknown'}
                      </p>
                    </div>

                    {/* Vehicle Details Grid */}
                    <div className="grid grid-cols-2 gap-3">
                      <div className="bg-gray-50 p-3 rounded-lg">
                        <p className="text-xs text-gray-500 mb-1">Registration</p>
                        <p className="font-medium text-gray-900">{selectedVehicle.registration_number}</p>
                      </div>
                      <div className="bg-gray-50 p-3 rounded-lg">
                        <p className="text-xs text-gray-500 mb-1">Capacity</p>
                        <p className="font-medium text-gray-900">{selectedVehicle.capacity} seats</p>
                      </div>
                      <div className="bg-gray-50 p-3 rounded-lg">
                        <p className="text-xs text-gray-500 mb-1">Type</p>
                        <p className="font-medium text-gray-900">{selectedVehicle.vehicle_type}</p>
                      </div>
                      <div className="bg-gray-50 p-3 rounded-lg">
                        <p className="text-xs text-gray-500 mb-1">Status</p>
                        <p className="font-medium text-gray-900 capitalize">{selectedVehicle.status}</p>
                      </div>
                    </div>

                    {/* Assigned Driver */}
                    {selectedVehicle.assigned_driver && (
                      <div className="bg-blue-50 p-3 rounded-lg border border-blue-200">
                        <p className="text-xs text-blue-600 mb-1 font-medium">Assigned Driver</p>
                        <div className="flex items-center gap-2">
                          <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold text-sm">
                            {selectedVehicle.assigned_driver.driver_name?.charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <p className="font-medium text-gray-900">{selectedVehicle.assigned_driver.driver_name}</p>
                            <p className="text-xs text-gray-500">{selectedVehicle.assigned_driver.driver_phone}</p>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Today's Trips */}
                    {selectedVehicle.todays_trips && selectedVehicle.todays_trips.length > 0 && (
                      <div>
                        <h5 className="font-medium text-gray-700 mb-2 flex items-center gap-2">
                          <span>📋</span> Today's Trips
                        </h5>
                        <div className="space-y-2">
                          {selectedVehicle.todays_trips.map((trip, idx) => (
                            <div key={idx} className="flex items-center justify-between p-2 bg-gray-50 rounded-lg text-sm">
                              <div>
                                <p className="font-medium text-gray-900">{trip.display_name}</p>
                                <p className="text-xs text-gray-500">
                                  {trip.shift_time ? String(trip.shift_time).slice(0, 5) : 'Time TBD'}
                                  {trip.driver_name && ` • ${trip.driver_name}`}
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
              /* Vehicle List */
              <div className="divide-y divide-gray-100">
                {filteredVehicles.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <span className="text-3xl">🚌</span>
                    <p className="mt-2">{showOnlyAvailable ? 'No available vehicles' : 'No vehicles found'}</p>
                  </div>
                ) : (
                  filteredVehicles.map((vehicle) => (
                    <div
                      key={vehicle.vehicle_id}
                      onClick={() => handleVehicleClick(vehicle)}
                      className="flex items-center justify-between px-4 py-3 hover:bg-gray-50 cursor-pointer transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-green-600 rounded-lg flex items-center justify-center text-xl">
                          {getVehicleTypeIcon(vehicle.vehicle_type)}
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">{vehicle.registration_number}</p>
                          <p className="text-xs text-gray-500">{vehicle.vehicle_type} • {vehicle.capacity} seats</p>
                        </div>
                      </div>
                      {getAvailabilityBadge(vehicle.availability)}
                    </div>
                  ))
                )}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="bg-gray-50 px-4 py-2 border-t border-gray-200">
            <p className="text-xs text-gray-500 text-center">
              {filteredVehicles.length} of {vehicles.length} vehicle{vehicles.length !== 1 ? 's' : ''}
              {showOnlyAvailable && ' (available only)'}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default VehicleDropdown;
