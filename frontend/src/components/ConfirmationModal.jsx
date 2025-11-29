import { useState } from "react";

/**
 * ConfirmationModal - Professional confirmation dialog with consequences display
 * 
 * Props:
 * - isOpen: boolean - Whether modal is visible
 * - onClose: function - Called when modal is closed
 * - onConfirm: function - Called when user confirms action
 * - title: string - Modal title
 * - icon: string - Emoji icon for the header
 * - type: "warning" | "danger" | "info" - Styling type
 * - tripName: string - Name of the trip
 * - consequences: array - List of consequence items to display
 * - bookingsAffected: number - Number of bookings that will be affected
 * - bookingPercentage: number - Percentage of capacity booked
 * - confirmText: string - Text for confirm button
 * - cancelText: string - Text for cancel button
 * - loading: boolean - Whether action is in progress
 */
export default function ConfirmationModal({
  isOpen,
  onClose,
  onConfirm,
  title = "Confirm Action",
  icon = "⚠️",
  type = "warning",
  tripName = "",
  consequences = [],
  bookingsAffected = 0,
  bookingPercentage = 0,
  confirmText = "Proceed",
  cancelText = "Cancel",
  loading = false,
}) {
  if (!isOpen) return null;

  // Theme colors based on type
  const themes = {
    warning: {
      headerBg: "bg-gradient-to-r from-amber-500 to-orange-500",
      iconBg: "bg-amber-100",
      iconColor: "text-amber-600",
      confirmBg: "bg-amber-500 hover:bg-amber-600",
      border: "border-amber-200",
      highlight: "text-amber-600",
      lightBg: "bg-amber-50",
    },
    danger: {
      headerBg: "bg-gradient-to-r from-red-500 to-red-600",
      iconBg: "bg-red-100",
      iconColor: "text-red-600",
      confirmBg: "bg-red-500 hover:bg-red-600",
      border: "border-red-200",
      highlight: "text-red-600",
      lightBg: "bg-red-50",
    },
    info: {
      headerBg: "bg-gradient-to-r from-blue-500 to-blue-600",
      iconBg: "bg-blue-100",
      iconColor: "text-blue-600",
      confirmBg: "bg-blue-500 hover:bg-blue-600",
      border: "border-blue-200",
      highlight: "text-blue-600",
      lightBg: "bg-blue-50",
    },
  };

  const theme = themes[type] || themes.warning;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg overflow-hidden animate-in fade-in zoom-in duration-200">
        {/* Header */}
        <div className={`${theme.headerBg} text-white p-5`}>
          <div className="flex items-center gap-3">
            <span className="text-3xl">{icon}</span>
            <div>
              <h3 className="text-xl font-bold">{title}</h3>
              {tripName && (
                <p className="text-sm text-white/80 mt-0.5">Trip: {tripName}</p>
              )}
            </div>
          </div>
        </div>

        {/* Body */}
        <div className="p-6">
          {/* Bookings Impact Alert */}
          {bookingsAffected > 0 && (
            <div className={`mb-5 p-4 ${theme.lightBg} border ${theme.border} rounded-lg`}>
              <div className="flex items-start gap-3">
                <span className="text-2xl">📊</span>
                <div>
                  <p className={`font-semibold ${theme.highlight}`}>
                    Booking Impact Warning
                  </p>
                  <p className="text-gray-700 mt-1">
                    This trip is currently <strong>{bookingPercentage}% booked</strong> with{" "}
                    <strong>{bookingsAffected} confirmed booking(s)</strong>.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Consequences List */}
          {consequences.length > 0 && (
            <div className="mb-5">
              <p className="font-medium text-gray-700 mb-3">
                ⚠️ Please be aware of the following consequences:
              </p>
              <ul className="space-y-2">
                {consequences.map((consequence, index) => (
                  <li
                    key={index}
                    className="flex items-start gap-2 text-gray-600"
                  >
                    <span className="text-red-500 mt-0.5">•</span>
                    <span>{consequence}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Main Question */}
          <div className={`p-4 bg-gray-50 border border-gray-200 rounded-lg`}>
            <p className="text-gray-800 font-medium text-center">
              Do you want to proceed with this action?
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="bg-gray-50 px-6 py-4 flex justify-end gap-3 border-t">
          <button
            onClick={onClose}
            disabled={loading}
            className="px-5 py-2.5 bg-gray-200 hover:bg-gray-300 disabled:bg-gray-100 text-gray-700 rounded-lg font-medium transition-colors"
          >
            {cancelText}
          </button>
          <button
            onClick={onConfirm}
            disabled={loading}
            className={`px-5 py-2.5 ${theme.confirmBg} disabled:bg-gray-400 text-white rounded-lg font-medium transition-colors flex items-center gap-2`}
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                Processing...
              </>
            ) : (
              <>{confirmText}</>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
