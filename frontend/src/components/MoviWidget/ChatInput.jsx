import React, { useState, useRef, useEffect } from 'react';
import ImageUploadButton from './ImageUploadButton';

const ChatInput = ({ onSend, onImageSelect, disabled, placeholder = 'Type a message...' }) => {
  const [text, setText] = useState('');
  const inputRef = useRef(null);

  useEffect(() => {
    if (!disabled) {
      inputRef.current?.focus();
    }
  }, [disabled]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (text.trim() && !disabled) {
      onSend(text);
      setText('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="border-t border-gray-200 bg-white p-4 rounded-b-lg">
      <div className="flex items-end gap-2">
        {/* Image upload button */}
        {onImageSelect && (
          <ImageUploadButton onImageSelect={onImageSelect} disabled={disabled} />
        )}
        
        <div className="flex-1 relative">
          <textarea
            ref={inputRef}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            placeholder={placeholder}
            rows={1}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed resize-none"
            style={{ minHeight: '40px', maxHeight: '120px' }}
            onInput={(e) => {
              e.target.style.height = 'auto';
              e.target.style.height = e.target.scrollHeight + 'px';
            }}
          />
          {disabled && (
            <div className="absolute inset-0 flex items-center justify-center bg-gray-100 bg-opacity-80 rounded-lg">
              <p className="text-xs text-gray-600">Please respond to the prompt above</p>
            </div>
          )}
        </div>
        <button
          type="submit"
          disabled={disabled || !text.trim()}
          className="bg-blue-600 hover:bg-blue-700 text-white p-2 rounded-lg transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0"
          style={{ height: '40px', width: '40px' }}
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
        </button>
      </div>
      <p className="text-xs text-gray-500 mt-2">
        Press <kbd className="px-1 py-0.5 bg-gray-200 rounded text-xs">Enter</kbd> to send, <kbd className="px-1 py-0.5 bg-gray-200 rounded text-xs">Shift+Enter</kbd> for new line
      </p>
    </form>
  );
};

export default ChatInput;
