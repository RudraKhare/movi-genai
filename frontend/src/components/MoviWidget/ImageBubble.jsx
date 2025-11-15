import React from 'react';

const ImageBubble = ({ message, isUser }) => {
  const { imageUrl, fileName, status, text } = message;

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-2`}>
      <div
        className={`max-w-[80%] rounded-lg px-4 py-2 shadow-sm ${
          isUser
            ? 'bg-blue-600 text-white rounded-br-none'
            : 'bg-white text-gray-800 rounded-bl-none border border-gray-200'
        }`}
      >
        {/* Image preview */}
        {imageUrl && (
          <div className="mb-2">
            <img
              src={imageUrl}
              alt={fileName || 'Uploaded image'}
              className="rounded-lg max-w-full h-auto"
              style={{ maxHeight: '200px', objectFit: 'contain' }}
            />
          </div>
        )}

        {/* Status/Text */}
        {text && (
          <p className={`text-sm ${isUser ? 'text-white' : 'text-gray-800'}`}>
            {text}
          </p>
        )}

        {/* Status indicator */}
        {status && (
          <div className="flex items-center gap-2 mt-1">
            {status === 'uploading' && (
              <>
                <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white"></div>
                <span className="text-xs">Uploading...</span>
              </>
            )}
            {status === 'processing' && (
              <>
                <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white"></div>
                <span className="text-xs">Reading image...</span>
              </>
            )}
            {status === 'success' && (
              <>
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="text-xs">Processed</span>
              </>
            )}
            {status === 'error' && (
              <>
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <span className="text-xs">Failed</span>
              </>
            )}
          </div>
        )}

        {/* Filename */}
        {fileName && (
          <p className={`text-xs mt-1 ${isUser ? 'text-blue-100' : 'text-gray-400'}`}>
            📎 {fileName}
          </p>
        )}

        {/* Timestamp */}
        <p
          className={`text-xs mt-1 ${
            isUser ? 'text-blue-100' : 'text-gray-400'
          }`}
        >
          {new Date(message.timestamp).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </p>
      </div>
    </div>
  );
};

export default ImageBubble;
