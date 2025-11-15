import React from 'react';
import ChatBubble from './ChatBubble';
import ConsequenceCard from './ConsequenceCard';
import ImageBubble from './ImageBubble';

const MessageList = ({ messages, onOptionClick, onConfirm, awaitingConfirm }) => {
  return (
    <div className="space-y-4">
      {messages.map((message) => {
        // Handle different message types
        switch (message.type) {
          case 'user':
            return <ChatBubble key={message.id} message={message} isUser={true} />;

          case 'agent':
            return <ChatBubble key={message.id} message={message} isUser={false} />;

          case 'image':
            return <ImageBubble key={message.id} message={message} isUser={message.isUser} />;

          case 'consequence':
            return (
              <ConsequenceCard
                key={message.id}
                message={message}
                onConfirm={onConfirm}
                awaitingConfirm={awaitingConfirm}
              />
            );

          case 'clarification':
            return (
              <div key={message.id} className="flex flex-col gap-2">
                <ChatBubble message={{ ...message, text: message.text }} isUser={false} />
                <div className="flex flex-col gap-2 ml-2">
                  {message.options.map((option, idx) => (
                    <button
                      key={idx}
                      onClick={() => onOptionClick(option)}
                      className="bg-white border-2 border-blue-300 hover:border-blue-500 hover:bg-blue-50 text-blue-700 font-medium py-2 px-4 rounded-lg transition-all duration-200 text-left shadow-sm"
                    >
                      {option.name || option.text || `Trip ${option.trip_id}`}
                    </button>
                  ))}
                </div>
              </div>
            );

          case 'execution':
            return (
              <div key={message.id} className="bg-green-50 border-l-4 border-green-500 p-4 rounded-r-lg shadow-sm">
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0">
                    <svg className="w-6 h-6 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="flex-1">
                    <p className="font-semibold text-green-800 mb-1">Action Completed</p>
                    <p className="text-sm text-green-700">{message.text}</p>
                    {message.action && (
                      <p className="text-xs text-green-600 mt-2">
                        Action: <span className="font-mono">{message.action}</span>
                        {message.trip_id && ` • Trip ID: ${message.trip_id}`}
                      </p>
                    )}
                  </div>
                </div>
                <p className="text-xs text-green-600 mt-2">
                  {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
            );

          case 'fallback':
            return (
              <div key={message.id} className="bg-red-50 border-l-4 border-red-400 p-4 rounded-r-lg shadow-sm">
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0">
                    <svg className="w-6 h-6 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="flex-1">
                    <p className="font-semibold text-red-800 mb-1">Need More Information</p>
                    <p className="text-sm text-red-700">{message.text}</p>
                    <p className="text-xs text-red-600 mt-2">
                      Try being more specific or use a different format.
                    </p>
                  </div>
                </div>
                <p className="text-xs text-red-600 mt-2">
                  {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
            );

          case 'error':
            return (
              <div key={message.id} className="bg-red-100 border-l-4 border-red-600 p-4 rounded-r-lg shadow-sm">
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0">
                    <svg className="w-6 h-6 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="flex-1">
                    <p className="font-semibold text-red-900 mb-1">Error</p>
                    <p className="text-sm text-red-800">{message.text}</p>
                  </div>
                </div>
                <p className="text-xs text-red-700 mt-2">
                  {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
            );

          default:
            return <ChatBubble key={message.id} message={message} isUser={false} />;
        }
      })}
    </div>
  );
};

export default MessageList;
