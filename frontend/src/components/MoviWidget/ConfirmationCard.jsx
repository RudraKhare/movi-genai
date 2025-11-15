import React from 'react';

const ConfirmationCard = ({ onConfirm, onCancel, disabled }) => {
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
          className="flex-1 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-md"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          Confirm
        </button>
      </div>
      <p className="text-xs text-center text-gray-600 mt-2">
        Click <span className="font-semibold">Confirm</span> to proceed or <span className="font-semibold">Cancel</span> to abort
      </p>
    </div>
  );
};

export default ConfirmationCard;
