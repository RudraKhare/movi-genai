import React from 'react';

const ImagePreview = ({ imageUrl, fileName, onClose }) => {
  return (
    <div className="bg-gray-100 border border-gray-300 rounded-lg p-3 mb-2 relative">
      {/* Close button */}
      <button
        onClick={onClose}
        className="absolute top-2 right-2 bg-red-500 hover:bg-red-600 text-white rounded-full w-6 h-6 flex items-center justify-center shadow-md transition-colors"
        title="Remove image"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>

      {/* Image preview */}
      <div className="flex items-center gap-3">
        <img
          src={imageUrl}
          alt={fileName || 'Preview'}
          className="w-20 h-20 object-cover rounded"
        />
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-800 truncate">
            {fileName || 'image.png'}
          </p>
          <p className="text-xs text-gray-500 mt-1">
            Ready to upload
          </p>
        </div>
      </div>
    </div>
  );
};

export default ImagePreview;
