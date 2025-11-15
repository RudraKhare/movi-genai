import React, { useRef } from 'react';

const ImageUploadButton = ({ onImageSelect, disabled }) => {
  const fileInputRef = useRef(null);

  const handleButtonClick = (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleFileChange = (event) => {
    console.log('[ImageUploadButton] File input changed');
    const file = event.target.files?.[0];
    console.log('[ImageUploadButton] Selected file:', file);
    
    if (file) {
      // Validate file type
      if (!file.type.startsWith('image/')) {
        console.warn('[ImageUploadButton] Invalid file type:', file.type);
        alert('Please select an image file (JPG, PNG)');
        return;
      }

      // Validate file size (max 10MB)
      const maxSize = 10 * 1024 * 1024; // 10MB
      if (file.size > maxSize) {
        console.warn('[ImageUploadButton] File too large:', file.size);
        alert('Image too large. Please select an image smaller than 10MB.');
        return;
      }

      console.log('[ImageUploadButton] File validation passed, calling onImageSelect');
      if (typeof onImageSelect === 'function') {
        onImageSelect(file);
      } else {
        console.error('[ImageUploadButton] onImageSelect is not a function!');
      }
    }

    // Reset input so same file can be selected again
    event.target.value = '';
  };

  return (
    <>
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleFileChange}
        style={{ display: 'none' }}
      />
      <button
        type="button"
        onClick={handleButtonClick}
        disabled={disabled}
        className="bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 p-2 rounded-lg transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0"
        style={{ height: '40px', width: '40px' }}
        title="Upload image"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      </button>
    </>
  );
};

export default ImageUploadButton;
