import React, { useState, useEffect, useRef } from 'react';
import MessageList from './MessageList';
import ChatInput from './ChatInput';
import ConfirmationCard from './ConfirmationCard';
import ImageUploadButton from './ImageUploadButton';
import ImageBubble from './ImageBubble';
import { sendAgentMessage, confirmAgentAction, uploadAgentImage } from '../../api';

const MoviWidget = ({ context = {}, onRefresh }) => {
  const [messages, setMessages] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [awaitingConfirm, setAwaitingConfirm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isOpen, setIsOpen] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSendMessage = async (text) => {
    if (!text.trim() || loading || awaitingConfirm) return;

    // Add user message to chat
    const userMessage = {
      id: Date.now(),
      type: 'user',
      text: text.trim(),
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setError(null);
    setLoading(true);

    try {
      const payload = {
        text: text.trim(),
        user_id: 1,
        currentPage: context.currentPage || 'busDashboard',
        selectedRouteId: context.selectedRoute?.route_id || context.selectedRouteId,
        selectedTripId: context.selectedTrip?.trip_id || context.selectedTripId,
      };

      console.debug('[MoviWidget] Sending message:', payload);
      const agentReply = await sendAgentMessage(payload);
      console.debug('[MoviWidget] Agent reply:', agentReply.data);

      processAgentResponse(agentReply.data);
    } catch (err) {
      console.error('[MoviWidget] Error sending message:', err);
      setError('Sorry, something went wrong. Please try again.');
      
      const errorMessage = {
        id: Date.now(),
        type: 'error',
        text: 'Sorry, I encountered an error processing your message.',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const processAgentResponse = (agentReply) => {
    // Detect response type and add appropriate message
    
    // 1. Check for clarification needed (ambiguous target)
    if (agentReply.needs_clarification && agentReply.options) {
      const clarificationMessage = {
        id: Date.now(),
        type: 'clarification',
        text: agentReply.message || 'Which trip did you mean?',
        options: agentReply.options,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, clarificationMessage]);
      return;
    }

    // 2. Check for consequence evaluation (awaiting confirmation)
    if (agentReply.awaiting_confirmation || agentReply.needs_confirmation) {
      const consequenceMessage = {
        id: Date.now(),
        type: 'consequence',
        action: agentReply.action,
        trip_id: agentReply.trip_id,
        consequences: agentReply.consequences,
        message: agentReply.message,
        session_id: agentReply.session_id,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, consequenceMessage]);
      setSessionId(agentReply.session_id);
      setAwaitingConfirm(true);
      return;
    }

    // 3. Check for execution result
    if (agentReply.executed_action) {
      const executionMessage = {
        id: Date.now(),
        type: 'execution',
        action: agentReply.executed_action,
        trip_id: agentReply.trip_id,
        text: agentReply.message,
        new_state: agentReply.new_state,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, executionMessage]);
      
      // Trigger refresh and reset session
      if (onRefresh) {
        setTimeout(() => onRefresh(), 500);
      }
      setSessionId(null);
      setAwaitingConfirm(false);
      return;
    }

    // 4. Check for fallback
    if (agentReply.fallback) {
      const fallbackMessage = {
        id: Date.now(),
        type: 'fallback',
        text: agentReply.message || "I couldn't understand that. Could you rephrase?",
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, fallbackMessage]);
      return;
    }

    // 5. Normal text response
    const normalMessage = {
      id: Date.now(),
      type: 'agent',
      text: agentReply.message || agentReply.text || 'I processed your request.',
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, normalMessage]);
  };

  const handleConfirm = async (confirm) => {
    if (!sessionId) return;

    setLoading(true);
    setError(null);

    try {
      const response = await confirmAgentAction({
        session_id: sessionId,
        confirm: confirm,
      });

      const result = response.data;

      if (confirm) {
        // User confirmed - show success
        const successMessage = {
          id: Date.now(),
          type: 'execution',
          text: result.message || 'Action executed successfully.',
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, successMessage]);

        // Trigger refresh
        if (onRefresh) {
          setTimeout(() => onRefresh(), 500);
        }
      } else {
        // User cancelled
        const cancelMessage = {
          id: Date.now(),
          type: 'agent',
          text: result.message || 'Action cancelled.',
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, cancelMessage]);
      }

      setSessionId(null);
      setAwaitingConfirm(false);
    } catch (err) {
      console.error('Error confirming action:', err);
      setError('Failed to confirm action. Please try again.');

      const errorMessage = {
        id: Date.now(),
        type: 'error',
        text: 'Sorry, I encountered an error processing your confirmation.',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleOptionClick = (option) => {
    console.debug('[MoviWidget] Option clicked:', option);
    // When user clicks an ambiguous option, send it as a new message with trip_id
    const optionText = option.name || option.text || `Trip ${option.trip_id}`;
    
    // If option has trip_id, include it in context
    if (option.trip_id) {
      const userMessage = {
        id: Date.now(),
        type: 'user',
        text: optionText,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMessage]);
      setLoading(true);

      const payload = {
        text: optionText,
        user_id: 1,
        currentPage: context.currentPage || 'busDashboard',
        selectedTripId: option.trip_id,
        selectedRouteId: context.selectedRoute?.route_id || context.selectedRouteId,
      };

      console.debug('[MoviWidget] Sending option with trip_id:', payload);

      sendAgentMessage(payload)
        .then((agentReply) => {
          console.debug('[MoviWidget] Agent reply:', agentReply.data);
          processAgentResponse(agentReply.data);
        })
        .catch((err) => {
          console.error('[MoviWidget] Error sending option:', err);
          setError('Failed to process selection.');
        })
        .finally(() => setLoading(false));
    } else {
      handleSendMessage(optionText);
    }
  };

  const handleClearChat = () => {
    setMessages([]);
    setSessionId(null);
    setAwaitingConfirm(false);
    setError(null);
  };

  const handleImageUpload = async (file) => {
    console.debug('[MoviWidget] handleImageUpload called with file:', file);
    console.debug('[MoviWidget] Current state - loading:', loading, 'awaitingConfirm:', awaitingConfirm);
    
    if (!file || loading || awaitingConfirm) {
      console.debug('[MoviWidget] Aborting upload - file:', !!file, 'loading:', loading, 'awaitingConfirm:', awaitingConfirm);
      return;
    }

    console.debug('[MoviWidget] Creating object URL and image message');
    const imageUrl = URL.createObjectURL(file);
    const imageMessage = {
      id: Date.now(),
      type: 'image',
      isUser: true,
      imageUrl,
      fileName: file.name,
      status: 'uploading',
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, imageMessage]);
    setError(null);
    setLoading(true);

    try {
      console.debug('[MoviWidget] Creating FormData and uploading...');
      const formData = new FormData();
      formData.append('file', file);
      console.debug('[MoviWidget] Calling uploadAgentImage API...');
      const response = await uploadAgentImage(formData);
      console.debug('[MoviWidget] OCR Response:', response.data);
      const ocrResult = response.data;

      console.debug('[MoviWidget] Updating message status to processing');
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === imageMessage.id ? { ...msg, status: 'processing' } : msg
        )
      );

      // Handle different match types
      if (ocrResult.match_type === 'single' && ocrResult.auto_forward) {
        console.debug('[MoviWidget] Single match detected, auto-forwarding with trip_id:', ocrResult.trip_id);
        
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === imageMessage.id
              ? { ...msg, status: 'success', text: `Identified: ${ocrResult.display_name || 'Trip'}` }
              : msg
          )
        );

        // Auto-forward to agent with resolved trip_id
        const autoPayload = {
          text: '<image>',
          user_id: 1,
          currentPage: context.currentPage || 'busDashboard',
          selectedTripId: ocrResult.trip_id,
          selectedRouteId: context.selectedRoute?.route_id || context.selectedRouteId,
        };

        console.debug('[MoviWidget] Auto-forwarding to agent:', autoPayload);
        const agentResponse = await sendAgentMessage(autoPayload);
        console.debug('[MoviWidget] Auto-forward response:', agentResponse.data);
        processAgentResponse(agentResponse.data);

      } else if (ocrResult.match_type === 'multiple' && ocrResult.needs_clarification) {
        console.debug('[MoviWidget] Multiple matches detected, showing candidates:', ocrResult.candidates);
        
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === imageMessage.id ? { ...msg, status: 'success', text: 'Image processed' } : msg
          )
        );

        // Show clarification options
        const clarificationMessage = {
          id: Date.now() + 1,
          type: 'clarification',
          text: ocrResult.message || 'I found multiple trips matching your image. Which one did you mean?',
          options: ocrResult.candidates.map(c => ({
            trip_id: c.trip_id,
            name: c.display_name,
            text: `${c.display_name} (${(c.confidence * 100).toFixed(0)}% match)`,
            confidence: c.confidence,
          })),
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, clarificationMessage]);

      } else {
        console.debug('[MoviWidget] No match or fallback case');
        
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === imageMessage.id ? { ...msg, status: 'error', text: 'Could not identify trip' } : msg
          )
        );

        // Show fallback message
        const fallbackMessage = {
          id: Date.now() + 1,
          type: 'fallback',
          text: ocrResult.message || 'Sorry, I couldn\'t identify the trip from the image. Please try typing the trip details or upload a clearer image.',
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, fallbackMessage]);
      }
    } catch (err) {
      console.error('[MoviWidget] Error uploading image:', err);
      console.error('[MoviWidget] Error details:', err.response?.data || err.message);
      setError('Failed to process image. Please try again.');

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === imageMessage.id ? { ...msg, status: 'error', text: 'Upload failed' } : msg
        )
      );

      // Add error message to chat
      const errorMessage = {
        id: Date.now() + 1,
        type: 'error',
        text: 'Sorry, I encountered an error processing your image. Please try again.',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
      URL.revokeObjectURL(imageUrl);
    }
  };

  return (
    <>
      {/* Toggle Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 bg-blue-600 hover:bg-blue-700 text-white rounded-full p-4 shadow-lg transition-all duration-300 z-50 flex items-center justify-center"
          aria-label="Open MOVI Assistant"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
        </button>
      )}

      {/* Widget Container */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 w-96 h-[600px] bg-white rounded-lg shadow-2xl flex flex-col z-50 overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-4 flex justify-between items-center">
            <div className="flex items-center gap-2">
              <div className="bg-white bg-opacity-20 p-2 rounded-lg">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
              </div>
              <div>
                <h3 className="font-semibold text-lg">MOVI Assistant</h3>
                <p className="text-xs text-blue-100">AI-powered bus management</p>
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleClearChat}
                className="p-2 hover:bg-white hover:bg-opacity-20 rounded transition-colors"
                title="Clear chat"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="p-2 hover:bg-white hover:bg-opacity-20 rounded transition-colors"
                title="Close"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          {/* Error Banner */}
          {error && (
            <div className="bg-red-50 border-l-4 border-red-500 p-3">
              <div className="flex items-center">
                <svg className="w-5 h-5 text-red-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <p className="text-sm text-red-700">{error}</p>
              </div>
            </div>
          )}

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 bg-gray-50">
            {messages.length === 0 ? (
              <div className="text-center text-gray-500 mt-8">
                <svg className="w-16 h-16 mx-auto mb-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
                <p className="text-sm">Start a conversation with MOVI</p>
                <p className="text-xs mt-2">Try: "Show me trip bulk-00:01" or upload an image</p>
              </div>
            ) : (
              <MessageList messages={messages} onOptionClick={handleOptionClick} />
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Confirmation Card */}
          {awaitingConfirm && (
            <ConfirmationCard
              onConfirm={() => handleConfirm(true)}
              onCancel={() => handleConfirm(false)}
              disabled={loading}
            />
          )}

          {/* Input */}
          <ChatInput
            onSend={handleSendMessage}
            onImageSelect={handleImageUpload}
            disabled={loading || awaitingConfirm}
            placeholder={
              awaitingConfirm
                ? 'Please confirm or cancel the action above'
                : 'Type a message...'
            }
          />
        </div>
      )}
    </>
  );
};

export default MoviWidget;
