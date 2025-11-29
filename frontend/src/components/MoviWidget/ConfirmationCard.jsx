import React from 'react';

const ConfirmationCard = ({ onConfirm, onCancel, disabled, confirmText = "Confirm", confirmColor = "blue" }) => {
  // Dynamic button styling based on confirmColor
  const confirmButtonClass = confirmColor === "red"
    ? "flex-1 bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-md"
    : "flex-1 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-md";

  return (
    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border-t-2 border-blue-200 p-4">
      <div className="flex items-center justify-center gap-3">
        <button
          onClick={onCancel}
          disabled={disabled}
          className="flex-1 bg-white border-2 border-gray-300 hover:border-red-400 hover:bg-red-50 text-gray-700 hover:text-red-700 font-semibold py-3 px-6 rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-sm"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
          Cancel
        </button>
        <button
          onClick={onConfirm}
          disabled={disabled}
          className={confirmButtonClass}
        >
          {confirmColor === "red" ? (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          ) : (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          )}
          {confirmText}
        </button>
      </div>
      <p className="text-xs text-center text-gray-600 mt-2">
        Click <span className="font-semibold">{confirmText}</span> to proceed or <span className="font-semibold">Cancel</span> to abort
      </p>
    </div>
  );
};

export default ConfirmationCard;
