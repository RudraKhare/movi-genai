import React, { useState, useEffect, useRef } from 'react';
import MessageList from './MessageList';
import ChatInput from './ChatInput';
import ConfirmationCard from './ConfirmationCard';
import ImageUploadButton from './ImageUploadButton';
import ImageBubble from './ImageBubble';
import { sendAgentMessage, confirmAgentAction, uploadAgentImage } from '../../api';

const MoviWidget = ({ context = {}, onRefresh }) => {
  // IMMEDIATE DEBUGGING: Log what we're receiving
  console.log('🔍 [MoviWidget] Component rendered with props:', {
    context: context,
    contextKeys: Object.keys(context),
    selectedTripId: context?.selectedTripId,
    selectedTrip: context?.selectedTrip,
    currentPage: context?.currentPage,
    timestamp: new Date().toISOString()
  });

  const [messages, setMessages] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [awaitingConfirm, setAwaitingConfirm] = useState(false);
  const [awaitingForceDelete, setAwaitingForceDelete] = useState(false);  // NEW: For force-delete confirmation
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isOpen, setIsOpen] = useState(false);

  // 🔥 DEBUG: Log sessionId changes
  useEffect(() => {
    console.log('🔑 [MoviWidget] sessionId changed:', sessionId);
  }, [sessionId]);
  const [persistedContext, setPersistedContext] = useState(null);
  const messagesEndRef = useRef(null);

  // Enhanced context management with persistence
  useEffect(() => {
    // Update persisted context when new context received
    if (context.selectedTripId) {
      setPersistedContext(context);
      localStorage.setItem('moviWidget_lastContext', JSON.stringify({
        selectedTripId: context.selectedTripId,
        selectedTrip: context.selectedTrip,
        currentPage: context.currentPage,
        timestamp: Date.now()
      }));
      console.log('[MoviWidget] ✅ Context updated and persisted:', context);
    }
  }, [context.selectedTripId, context.selectedTrip]);
  
  // Load persisted context on mount
  useEffect(() => {
    const stored = localStorage.getItem('moviWidget_lastContext');
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        // Only use persisted context if it's recent (within 1 hour) and current context is missing
        if (parsed.selectedTripId && !context.selectedTripId && 
            (Date.now() - parsed.timestamp < 3600000)) {
          console.log('[MoviWidget] 📂 Restored recent context from storage:', parsed);
          setPersistedContext(parsed);
        }
      } catch (e) {
        console.warn('[MoviWidget] Failed to parse stored context');
      }
    }
  }, [context.selectedTripId]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSendMessage = async (text) => {
    if (!text.trim() || loading || awaitingConfirm) return;

    // IMMEDIATE DEBUG: Log everything to understand the issue
    console.log("🔥 [MoviWidget] DEBUGGING CONTEXT ISSUE:");
    console.log("   Raw context prop:", context);
    console.log("   Persisted context:", persistedContext);
    console.log("   Context keys:", Object.keys(context || {}));
    console.log("   selectedTrip from context:", context?.selectedTrip);
    console.log("   selectedTripId from context:", context?.selectedTripId);
    console.log("   currentPage from context:", context?.currentPage);

    // Use current context or fallback to persisted context
    const effectiveContext = {
      ...context,
      ...(persistedContext && !context.selectedTripId ? persistedContext : {})
    };

    console.log("🎯 [MoviWidget] Effective context:", effectiveContext);

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
      // CRITICAL DEBUG: First check the effective context construction
      console.log("🔍 [MoviWidget] DEBUGGING PAYLOAD CONSTRUCTION:");
      console.log("   effectiveContext.selectedTrip:", effectiveContext.selectedTrip);
      console.log("   effectiveContext.selectedTrip?.trip_id:", effectiveContext.selectedTrip?.trip_id);
      console.log("   effectiveContext.selectedTripId:", effectiveContext.selectedTripId);
      console.log("   Final selectedTripId value:", effectiveContext.selectedTrip?.trip_id || effectiveContext.selectedTripId);

      const payload = {
        text: text.trim(),
        user_id: 1,
        session_id: sessionId,
        selectedTripId: effectiveContext.selectedTrip?.trip_id || effectiveContext.selectedTripId,
        from_image: false,
        currentPage: effectiveContext.currentPage || 'busDashboard',
        selectedRouteId: effectiveContext.selectedRoute?.route_id || effectiveContext.selectedRouteId,
        conversation_history: []
      };

      // CRITICAL DEBUG: Log exactly what's being sent to backend
      console.log("📤 [MoviWidget] PAYLOAD BEING SENT TO BACKEND:");
      console.log("   text:", payload.text);
      console.log("   🔑 session_id:", payload.session_id);  // <-- ADDED THIS
      console.log("   currentPage:", payload.currentPage);
      console.log("   selectedTripId:", payload.selectedTripId);
      console.log("   selectedRouteId:", payload.selectedRouteId);
      console.log("   Full payload:", payload);
      
      // Enhanced debugging with effective context
      console.debug('[MoviWidget] 🎯 Effective context used:', effectiveContext);
      console.debug('[MoviWidget] Original context received:', context);
      console.debug('[MoviWidget] Persisted context available:', persistedContext);
      
      // Warn about potential context issues
      const contextKeywords = ['this trip', 'this', 'here', 'it', 'current trip'];
      const hasContextReference = contextKeywords.some(keyword => text.toLowerCase().includes(keyword));
      
      if (hasContextReference && !payload.selectedTripId) {
        console.warn('[MoviWidget] ⚠️ CONTEXT ISSUE: User referenced context but selectedTripId is missing!');
        console.warn('[MoviWidget] Text:', text);
        console.warn('[MoviWidget] Effective context:', effectiveContext);
      } else if (hasContextReference && payload.selectedTripId) {
        console.log('[MoviWidget] ✅ Context reference detected and resolved:', payload.selectedTripId);
      }

      // FINAL DEBUG: Log payload just before sending
      console.log("🚀 [MoviWidget] FINAL PAYLOAD JUST BEFORE API CALL:", JSON.stringify(payload, null, 2));
      
      const response = await sendAgentMessage(payload);
      console.log('[MoviWidget] 📥 Full response.data:', response.data);
      console.log('[MoviWidget] 📥 response.data.session_id:', response.data.session_id);
      console.log('[MoviWidget] 📥 response.data.agent_output:', response.data.agent_output);

      // Extract session_id from top-level response (for wizard flows)
      const responseSessionId = response.data.session_id;
      if (responseSessionId) {
        console.log('[MoviWidget] 🔑✅ Setting sessionId from response:', responseSessionId);
        setSessionId(responseSessionId);
      } else {
        console.log('[MoviWidget] ⚠️ No session_id in response!');
      }

      // Extract agent_output from response
      const agentReply = response.data.agent_output || response.data;
      processAgentResponse(agentReply);
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
      const consequences = agentReply.consequences || {};
      const hasDependencies = consequences.can_force_delete && consequences.dependent_entities?.length > 0;
      
      console.log('[MoviWidget] Confirmation needed, consequences:', consequences);
      console.log('[MoviWidget] Has dependencies:', hasDependencies);
      
      const consequenceMessage = {
        id: Date.now(),
        type: 'consequence',
        action: agentReply.action,
        trip_id: agentReply.trip_id,
        consequences: consequences,
        message: agentReply.message,
        session_id: agentReply.session_id,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, consequenceMessage]);
      setSessionId(agentReply.session_id);
      setAwaitingConfirm(true);
      
      // If there are dependencies, set force delete mode from the start
      if (hasDependencies) {
        setAwaitingForceDelete(true);
      }
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

    // 4. Check for wizard active (stop creation, etc.)
    if (agentReply.status === 'wizard_active' || agentReply.wizard_active) {
      console.log('[MoviWidget] 🧙 Wizard active, preserving session_id:', agentReply.session_id);
      // Store session_id for subsequent messages
      if (agentReply.session_id) {
        setSessionId(agentReply.session_id);
      }
      
      const wizardMessage = {
        id: Date.now(),
        type: 'agent',
        text: agentReply.message || 'Please provide the requested information.',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, wizardMessage]);
      return;
    }

    // 5. Check for fallback
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

  const handleConfirm = async (confirm, forceDelete = false) => {
    if (!sessionId) return;

    setLoading(true);
    setError(null);

    try {
      const response = await confirmAgentAction({
        session_id: sessionId,
        confirmed: confirm,
        user_id: 1,
        force_delete: forceDelete,
      });

      const result = response.data;
      console.log('[MoviWidget] Confirm response:', JSON.stringify(result, null, 2));
      
      const agentOutput = result.agent_output || result;
      const executionResult = agentOutput.execution_result || {};

      if (confirm) {
        // Show result message
        const resultMessage = {
          id: Date.now(),
          type: executionResult.ok ? 'execution' : 'error',
          text: agentOutput.message || executionResult.message || 'Action completed.',
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, resultMessage]);

        // Trigger refresh on success
        if (onRefresh && executionResult.ok) {
          setTimeout(() => onRefresh(), 500);
        }
      } else {
        // User cancelled
        const cancelMessage = {
          id: Date.now(),
          type: 'agent',
          text: agentOutput.message || result.message || 'Action cancelled.',
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, cancelMessage]);
      }

      setSessionId(null);
      setAwaitingConfirm(false);
      setAwaitingForceDelete(false);
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
    
    // If option doesn't have an action (e.g., selecting from multiple trip candidates),
    // show action selection buttons instead of sending to agent
    if (option.trip_id && !option.action) {
      console.debug('[MoviWidget] Trip selected from candidates, showing action buttons');
      
      // Add user message showing their selection
      const userMessage = {
        id: Date.now(),
        type: 'user',
        text: option.name || option.text || `Selected: ${option.trip_id}`,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMessage]);
      
      // Show action selection prompt for this trip
      const actionPromptMessage = {
        id: Date.now() + 1,
        type: 'clarification',
        text: `Got it! What would you like to do with this trip?`,
        options: [
          {
            trip_id: option.trip_id,
            action: 'remove_vehicle',
            name: 'Remove Vehicle',
            text: 'Remove Vehicle',
          },
          {
            trip_id: option.trip_id,
            action: 'cancel_trip',
            name: 'Cancel Trip',
            text: 'Cancel Trip',
          },
        ],
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, actionPromptMessage]);
      return; // Don't send to agent yet
    }
    
    // Determine the text to send
    let messageText = option.name || option.text || `Trip ${option.trip_id}`;
    
    // If option has an action (from OCR action prompt), construct proper command
    if (option.action) {
      console.debug('[MoviWidget] Action button clicked:', option.action);
      // Convert action to natural language command
      if (option.action === 'remove_vehicle') {
        messageText = 'Remove vehicle';
      } else if (option.action === 'cancel_trip') {
        messageText = 'Cancel trip';
      } else if (option.action === 'assign_vehicle') {
        messageText = 'Assign vehicle';
      }
    }
    
    // Add user message
    const userMessage = {
      id: Date.now(),
      type: 'user',
      text: messageText,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    // Build payload with selectedTripId if available
    const payload = {
      text: messageText,
      user_id: 1,
      currentPage: context.currentPage || 'busDashboard',
      selectedTripId: option.trip_id || context.selectedTrip?.trip_id || context.selectedTripId,
      selectedRouteId: context.selectedRoute?.route_id || context.selectedRouteId,
    };

    console.debug('[MoviWidget] Sending message with payload:', payload);

    sendAgentMessage(payload)
      .then((response) => {
        console.debug('[MoviWidget] Agent reply:', response.data);
        // Extract agent_output from response
        const agentReply = response.data.agent_output || response.data;
        processAgentResponse(agentReply);
      })
      .catch((err) => {
        console.error('[MoviWidget] Error sending option:', err);
        setError('Failed to process selection.');
        const errorMessage = {
          id: Date.now(),
          type: 'error',
          text: 'Sorry, I encountered an error processing your selection.',
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, errorMessage]);
      })
      .finally(() => setLoading(false));
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
        console.debug('[MoviWidget] Single match detected, showing action prompt for trip_id:', ocrResult.trip_id);
        
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === imageMessage.id
              ? { ...msg, status: 'success', text: `Identified: ${ocrResult.display_name || 'Trip'}` }
              : msg
          )
        );

        // Show action selection prompt
        const actionPromptMessage = {
          id: Date.now() + 1,
          type: 'clarification',
          text: `I identified the trip: **${ocrResult.display_name}**${ocrResult.scheduled_time ? ` at ${ocrResult.scheduled_time}` : ''}. What would you like to do?`,
          options: [
            {
              trip_id: ocrResult.trip_id,
              action: 'remove_vehicle',
              name: 'Remove Vehicle',
              text: 'Remove Vehicle',
            },
            {
              trip_id: ocrResult.trip_id,
              action: 'cancel_trip',
              name: 'Cancel Trip',
              text: 'Cancel Trip',
            },
          ],
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, actionPromptMessage]);

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
          {(awaitingConfirm || awaitingForceDelete) && (
            <ConfirmationCard
              onConfirm={() => handleConfirm(true, awaitingForceDelete)}
              onCancel={() => handleConfirm(false)}
              disabled={loading}
              confirmText={awaitingForceDelete ? "Force Delete" : "Confirm"}
              confirmColor={awaitingForceDelete ? "red" : "green"}
            />
          )}

          {/* Input */}
          <ChatInput
            onSend={handleSendMessage}
            onImageSelect={handleImageUpload}
            disabled={loading || awaitingConfirm || awaitingForceDelete}
            placeholder={
              awaitingForceDelete
                ? 'Please confirm force delete or cancel'
                : awaitingConfirm
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
