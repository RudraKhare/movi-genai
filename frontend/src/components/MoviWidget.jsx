import { useState, useRef, useEffect } from "react";
import axios from "axios";
import { makeUserCommand, validateOption, getSelectionIcon, getSelectionLabel } from "./MoviWidget/utils";
import ObjectCard from "./ObjectCard";
import TableCard from "./TableCard";

// Use environment variable for API base, fallback to localhost for development
const API_BASE = import.meta.env.VITE_API_URL 
  ? `${import.meta.env.VITE_API_URL}/api` 
  : "http://localhost:8000/api";
const API_KEY = "dev-key-change-in-production";

export default function MoviWidget({ context }) {
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);  // Track session for wizard/confirmation flows
  
  // Voice state
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  
  // Image upload ref
  const fileInputRef = useRef(null);
  
  // OCR context - persists trip info from image upload for subsequent text commands
  const [ocrContext, setOcrContext] = useState(null);
  const recognitionRef = useRef(null);
  const synthRef = useRef(window.speechSynthesis);

  // Initialize Speech Recognition
  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = 'en-US';

      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        console.log("🎤 Voice input:", transcript);
        setMessage(transcript);
        setIsListening(false);
      };

      recognitionRef.current.onerror = (event) => {
        console.error("Speech recognition error:", event.error);
        setIsListening(false);
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
      };
    }
  }, []);

  // Text-to-Speech function
  const speakText = (text) => {
    if (!voiceEnabled || !synthRef.current) return;
    
    // Cancel any ongoing speech
    synthRef.current.cancel();
    
    // Clean text for speech (remove emojis and markdown)
    const cleanText = text
      .replace(/[🎤📸💡✅❌⚠️🔄👤🚛📅❓🔧]/g, '')
      .replace(/\*\*/g, '')
      .replace(/\n+/g, '. ')
      .trim();
    
    if (!cleanText) return;
    
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;
    
    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);
    
    synthRef.current.speak(utterance);
  };

  // Toggle voice listening
  const toggleListening = () => {
    if (!recognitionRef.current) {
      alert("Speech recognition is not supported in your browser. Try Chrome or Edge.");
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      recognitionRef.current.start();
      setIsListening(true);
    }
  };

  // Stop speaking
  const stopSpeaking = () => {
    if (synthRef.current) {
      synthRef.current.cancel();
      setIsSpeaking(false);
    }
  };

  // Image upload handler
  const handleImageUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file (JPG, PNG)');
      return;
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      alert('Image too large. Please select an image smaller than 10MB.');
      return;
    }

    console.log('[MoviWidget] Uploading image:', file.name);
    
    // Add uploading message
    const uploadingMsg = {
      role: "user",
      content: `📸 Uploading image: ${file.name}...`,
      type: "image_upload",
      status: "uploading"
    };
    setMessages(prev => [...prev, uploadingMsg]);
    setLoading(true);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(`${API_BASE}/agent/image`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'x-api-key': API_KEY
        }
      });

      console.log('[MoviWidget] OCR Response:', response.data);
      const ocrResult = response.data;

      // Debug log the match conditions
      console.log('[MoviWidget] OCR match_type:', ocrResult.match_type, 'auto_forward:', ocrResult.auto_forward);

      // Update uploading message to success
      setMessages(prev => prev.map(msg => 
        msg === uploadingMsg ? { ...msg, content: `📸 Uploaded image: ${file.name}`, status: "success" } : msg
      ));

      // Handle match types
      if (ocrResult.match_type === 'single') {
        // Save OCR context for subsequent text commands
        const tripContext = {
          trip_id: ocrResult.trip_id,
          display_name: ocrResult.display_name,
          scheduled_time: ocrResult.scheduled_time,
          route_name: ocrResult.route_name,
          from_ocr: true,
          timestamp: Date.now()
        };
        setOcrContext(tripContext);
        console.log('[MoviWidget] 📸 OCR context saved:', tripContext);

        // Single confident match - show ALL 6 action options
        setMessages(prev => [...prev, {
          role: "assistant",
          content: {
            message: `✅ I identified the trip: **${ocrResult.display_name}**${ocrResult.scheduled_time ? ` at ${ocrResult.scheduled_time}` : ''}.\n\n📌 Trip context saved! You can click an action below OR type any command - I'll remember this trip.\n\nWhat would you like to do?`,
            success: true,
            options: [
              { label: "🚛 Assign Vehicle", action: "assign_vehicle", trip_id: ocrResult.trip_id },
              { label: "🚛❌ Remove Vehicle", action: "remove_vehicle", trip_id: ocrResult.trip_id },
              { label: "👤 Assign Driver", action: "assign_driver", trip_id: ocrResult.trip_id },
              { label: "👤❌ Remove Driver", action: "remove_driver", trip_id: ocrResult.trip_id },
              { label: "❌ Cancel Trip", action: "cancel_trip", trip_id: ocrResult.trip_id },
              { label: "� Update Status", action: "update_trip_status", trip_id: ocrResult.trip_id }
            ],
            awaiting_selection: true,
            selection_type: "ocr_action",
            trip_id: ocrResult.trip_id,
            ocr_context: tripContext
          }
        }]);
      } else if (ocrResult.match_type === 'multiple' && ocrResult.candidates) {
        // Multiple matches - show options
        setMessages(prev => [...prev, {
          role: "assistant",
          content: {
            message: ocrResult.message || "I found multiple possible trips. Which one did you mean?",
            success: true,
            options: ocrResult.candidates.map(c => ({
              label: `${c.display_name} (${(c.confidence * 100).toFixed(0)}% match)`,
              trip_id: c.trip_id,
              display_name: c.display_name
            })),
            awaiting_selection: true,
            selection_type: "ocr_trip_select"
          }
        }]);
      } else if (ocrResult.match_type === 'none' || !ocrResult.match_type) {
        // No match
        setMessages(prev => [...prev, {
          role: "assistant",
          content: {
            message: ocrResult.message || "Sorry, I couldn't identify a trip from this image. Please try typing the trip details or upload a clearer image.",
            success: false
          }
        }]);
      } else {
        // Unexpected response - log and show friendly message
        console.warn('[MoviWidget] Unexpected OCR response:', ocrResult);
        setMessages(prev => [...prev, {
          role: "assistant",
          content: {
            message: `Received response: ${ocrResult.message || JSON.stringify(ocrResult)}`,
            success: false
          }
        }]);
      }
    } catch (err) {
      console.error('[MoviWidget] Image upload error:', err);
      setMessages(prev => prev.map(msg => 
        msg === uploadingMsg ? { ...msg, content: `❌ Failed to process image: ${file.name}`, status: "error" } : msg
      ));
      setMessages(prev => [...prev, {
        role: "assistant",
        content: "Sorry, I encountered an error processing your image. Please try again.",
        type: "error"
      }]);
    } finally {
      setLoading(false);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleSend = async () => {
    if (!message.trim()) return;

    const userMessage = message.trim();
    console.log("Sending message:", userMessage, "with context:", context);
    
    // Add user message to chat
    setMessages(prev => [...prev, {
      role: "user",
      content: userMessage,
      timestamp: new Date()
    }]);
    
    setMessage("");
    setLoading(true);

    await handleSendCommand(userMessage);
  };

  const handleSendCommand = async (command) => {
    try {
      console.log("📤 Sending command with session_id:", sessionId);
      console.log("📸 OCR context available:", ocrContext);
      
      // Determine selectedTripId - prioritize OCR context if recent (within 10 minutes)
      let selectedTripId = context?.selectedTripId || context?.selectedTrip?.trip_id || null;
      let fromImage = false;
      
      // If OCR context exists and is recent, use it
      if (ocrContext && (Date.now() - ocrContext.timestamp < 600000)) {
        selectedTripId = ocrContext.trip_id;
        fromImage = true;
        console.log("📸 Using OCR context trip_id:", selectedTripId);
      }
      
      // Call agent API with correct backend payload structure
      const response = await axios.post(
        `${API_BASE}/agent/message`,
        {
          text: command,
          user_id: 1,
          session_id: sessionId,  // Use stored session_id for wizard continuity
          selectedTripId: selectedTripId,
          from_image: fromImage,
          currentPage: context?.currentPage || 'busDashboard',
          selectedRouteId: context?.selectedRouteId || context?.selectedRoute?.route_id || null,
          conversation_history: [],
          // Include OCR context for backend reference
          ocr_context: ocrContext
        },
        {
          headers: {
            "x-api-key": API_KEY,
            "Content-Type": "application/json"
          }
        }
      );

      console.log("Agent response:", response.data);
      
      // Extract and store session_id for wizard/confirmation flows
      const responseSessionId = response.data.session_id;
      if (responseSessionId) {
        console.log("🔑 Storing session_id:", responseSessionId);
        setSessionId(responseSessionId);
      }

      // Add agent response to chat
      setMessages(prev => [...prev, {
        role: "agent",
        content: response.data.agent_output,
        timestamp: new Date()
      }]);

      // Text-to-Speech for agent response
      const agentMessage = response.data.agent_output?.message || 
                          response.data.agent_output?.summary ||
                          (typeof response.data.agent_output === 'string' ? response.data.agent_output : '');
      if (agentMessage && voiceEnabled) {
        speakText(agentMessage);
      }

    } catch (error) {
      console.error("Agent API error:", error);
      
      // Add error message to chat
      setMessages(prev => [...prev, {
        role: "agent",
        content: {
          message: `Error: ${error.response?.data?.detail || error.message}`,
          success: false
        },
        timestamp: new Date()
      }]);
    } finally {
      setLoading(false);
    }
  };

  // Handle confirmation of pending action
  const handleConfirm = async (sessionId) => {
    console.log("Confirming action for session:", sessionId);
    setLoading(true);

    try {
      const response = await axios.post(
        `${API_BASE}/agent/confirm`,
        {
          session_id: sessionId,
          confirmed: true,
          user_id: 1
        },
        {
          headers: {
            "x-api-key": API_KEY,
            "Content-Type": "application/json"
          }
        }
      );

      console.log("Confirmation response:", response.data);

      // Add confirmation result to chat
      setMessages(prev => [...prev, {
        role: "agent",
        content: response.data.agent_output,
        timestamp: new Date()
      }]);

    } catch (error) {
      console.error("Confirmation error:", error);
      
      setMessages(prev => [...prev, {
        role: "agent",
        content: {
          message: `Error confirming action: ${error.response?.data?.detail || error.message}`,
          success: false
        },
        timestamp: new Date()
      }]);
    } finally {
      setLoading(false);
    }
  };

  // Handle cancellation of pending action
  const handleCancel = async (sessionId) => {
    console.log("Cancelling action for session:", sessionId);
    setLoading(true);

    try {
      const response = await axios.post(
        `${API_BASE}/agent/confirm`,
        {
          session_id: sessionId,
          confirmed: false,
          user_id: 1
        },
        {
          headers: {
            "x-api-key": API_KEY,
            "Content-Type": "application/json"
          }
        }
      );

      console.log("Cancellation response:", response.data);

      // Add cancellation message to chat
      setMessages(prev => [...prev, {
        role: "agent",
        content: response.data.agent_output,
        timestamp: new Date()
      }]);

    } catch (error) {
      console.error("Cancellation error:", error);
      
      setMessages(prev => [...prev, {
        role: "agent",
        content: {
          message: `Error cancelling action: ${error.response?.data?.detail || error.message}`,
          success: false
        },
        timestamp: new Date()
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Floating Action Button */}
      <div
        className="fixed bottom-6 right-6 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-full w-16 h-16 flex items-center justify-center shadow-xl cursor-pointer hover:shadow-2xl hover:scale-110 transition-all duration-300 z-40"
        onClick={() => setOpen(!open)}
        title="Chat with Movi"
      >
        <span className="text-3xl">💬</span>
      </div>

      {/* Chat Widget */}
      {open && (
        <div className="fixed bottom-24 right-6 bg-white w-96 h-[32rem] rounded-2xl shadow-2xl border border-gray-200 flex flex-col z-50 animate-slide-up">
          {/* Header */}
          <div className="p-4 bg-gradient-to-r from-blue-600 to-blue-700 text-white font-semibold rounded-t-2xl flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-2xl">🤖</span>
              <div>
                <h3 className="font-bold">Movi Assistant</h3>
                <p className="text-xs text-blue-100">AI Transport Operations Agent</p>
              </div>
            </div>
            <button
              onClick={() => setOpen(false)}
              className="text-white hover:bg-blue-800 rounded-full w-8 h-8 flex items-center justify-center transition-colors"
            >
              ✕
            </button>
          </div>

          {/* Messages Area */}
          <div className="flex-1 p-4 overflow-y-auto bg-gray-50 space-y-3">
            {/* Welcome Message */}
            <div className="flex gap-2">
              <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                🤖
              </div>
              <div className="bg-white rounded-lg rounded-tl-none p-3 shadow-sm max-w-[80%]">
                <p className="text-sm text-gray-800">
                  Hi! I'm <strong>Movi</strong>, your AI transport operations assistant. 
                </p>
                <p className="text-sm text-gray-800 mt-2">
                  I can help you with:
                </p>
                <ul className="text-sm text-gray-700 mt-1 space-y-1 ml-4 list-disc">
                  <li>Removing vehicles from trips</li>
                  <li>Cancelling trips</li>
                  <li>Assigning vehicles to trips</li>
                  <li>Checking trip status and bookings</li>
                </ul>
              </div>
            </div>

            {/* Context Info */}
            {context?.selectedTrip && (
              <div className="flex gap-2">
                <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                  📋
                </div>
                <div className="bg-blue-50 border border-blue-200 rounded-lg rounded-tl-none p-3 max-w-[80%]">
                  <p className="text-xs text-blue-800 font-semibold mb-1">Current Context:</p>
                  <p className="text-xs text-blue-700">
                    <strong>Trip:</strong> {context.selectedTrip.route_name}<br/>
                    <strong>Status:</strong> {context.selectedTrip.live_status}<br/>
                    <strong>Bookings:</strong> {context.selectedTrip.booked_count}
                  </p>
                </div>
              </div>
            )}

            {/* OCR Context Indicator - Shows when trip is saved from image upload */}
            {ocrContext && (Date.now() - ocrContext.timestamp < 600000) && (
              <div className="flex gap-2">
                <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center flex-shrink-0">
                  📸
                </div>
                <div className="bg-purple-50 border border-purple-200 rounded-lg rounded-tl-none p-3 max-w-[80%]">
                  <div className="flex items-center justify-between mb-1">
                    <p className="text-xs text-purple-800 font-semibold">📌 Saved from Image:</p>
                    <button 
                      onClick={() => {
                        setOcrContext(null);
                        console.log('[MoviWidget] OCR context cleared');
                      }}
                      className="text-xs text-purple-500 hover:text-purple-700 hover:bg-purple-100 px-1 rounded"
                      title="Clear saved context"
                    >
                      ✕ Clear
                    </button>
                  </div>
                  <p className="text-xs text-purple-700">
                    <strong>Trip:</strong> {ocrContext.display_name}<br/>
                    {ocrContext.scheduled_time && <><strong>Time:</strong> {ocrContext.scheduled_time}<br/></>}
                    <span className="text-purple-500 italic">Text commands will use this trip</span>
                  </p>
                </div>
              </div>
            )}

            {/* Conversation Messages */}
            {messages.map((msg, idx) => (
              <div key={idx} className="flex gap-2">
                {msg.role === "user" ? (
                  <>
                    <div className="flex-1" />
                    <div className="bg-blue-600 text-white rounded-lg rounded-tr-none p-3 shadow-sm max-w-[80%]">
                      <p className="text-sm">{msg.content}</p>
                    </div>
                    <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0 text-white font-bold">
                      U
                    </div>
                  </>
                ) : (
                  <>
                    <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                      🤖
                    </div>
                    <div className="bg-white rounded-lg rounded-tl-none p-3 shadow-sm max-w-[80%]">
                      {/* Handle string content (simple messages) */}
                      {typeof msg.content === 'string' ? (
                        <p className="text-sm text-gray-800 whitespace-pre-line">{msg.content}</p>
                      ) : msg.content.success === false ? (
                        <p className="text-sm text-red-600">❌ {msg.content.message}</p>
                      ) : (
                        <>
                          <p className="text-sm text-gray-800 whitespace-pre-line">
                            {msg.content.message}
                          </p>
                          
                          {/* Render formatted data (tables, objects, etc.) */}
                          {msg.content.final_output && msg.content.final_output.type === "object" && msg.content.final_output.data && (
                            <div className="mt-3">
                              <ObjectCard data={msg.content.final_output.data} title="Trip Details" />
                            </div>
                          )}
                          
                          {msg.content.final_output && msg.content.final_output.type === "table" && msg.content.final_output.data && (
                            <div className="mt-3">
                              <TableCard 
                                data={msg.content.final_output.data} 
                                columns={msg.content.final_output.columns}
                                title={msg.content.message}
                              />
                            </div>
                          )}
                          
                          {/* Input Required UI (e.g., passenger count) */}
                          {msg.content.final_output && msg.content.final_output.type === "input_required" && (
                            <div className="mt-3 p-3 bg-gradient-to-br from-blue-50 to-purple-50 border border-blue-200 rounded-lg">
                              <p className="text-xs font-semibold text-blue-800 mb-2">
                                {msg.content.final_output.prompt || msg.content.final_output.data?.prompt || "Please enter a value:"}
                              </p>
                              <div className="flex gap-2">
                                <input
                                  type={msg.content.final_output.input_type || msg.content.final_output.data?.input_type || "text"}
                                  placeholder="Enter number..."
                                  className="flex-1 px-3 py-2 text-sm border border-blue-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                  onKeyDown={(e) => {
                                    if (e.key === 'Enter' && e.target.value) {
                                      const value = e.target.value;
                                      const tripId = msg.content.final_output.trip_id || msg.content.final_output.data?.trip_id || msg.content.trip_id;
                                      
                                      // Add user message
                                      setMessages(prev => [...prev, {
                                        role: "user",
                                        content: `${value} passengers`,
                                        timestamp: new Date()
                                      }]);
                                      
                                      // Send the command with passenger count - include full context
                                      setLoading(true);
                                      handleSendCommand(`I need a vehicle for ${value} passengers for trip ${tripId}`);
                                      e.target.value = '';
                                    }
                                  }}
                                />
                                <button
                                  onClick={(e) => {
                                    const input = e.target.parentElement.querySelector('input');
                                    if (input && input.value) {
                                      const value = input.value;
                                      const tripId = msg.content.final_output.trip_id || msg.content.final_output.data?.trip_id || msg.content.trip_id;
                                      
                                      setMessages(prev => [...prev, {
                                        role: "user",
                                        content: `${value} passengers`,
                                        timestamp: new Date()
                                      }]);
                                      
                                      setLoading(true);
                                      handleSendCommand(`I need a vehicle for ${value} passengers for trip ${tripId}`);
                                      input.value = '';
                                    }
                                  }}
                                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors"
                                >
                                  Submit
                                </button>
                              </div>
                            </div>
                          )}
                          
                          {msg.content.consequences && (
                            <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded text-xs">
                              <p className="font-semibold text-yellow-800">⚠️ Impact:</p>
                              <ul className="mt-1 space-y-1 text-yellow-700">
                                {msg.content.consequences.booking_count > 0 && (
                                  <li>• {msg.content.consequences.booking_count} bookings affected</li>
                                )}
                                {msg.content.consequences.booking_percentage > 0 && (
                                  <li>• {msg.content.consequences.booking_percentage}% capacity</li>
                                )}
                              </ul>
                            </div>
                          )}
                          
                          {/* Driver/Vehicle Selection UI */}
                          {msg.content.options && msg.content.options.length > 0 && msg.content.awaiting_selection && (
                            <div className="mt-3 p-3 bg-gradient-to-br from-green-50 to-blue-50 border border-green-200 rounded-lg">
                              <p className="text-xs font-semibold text-green-800 mb-2 flex items-center gap-1">
                                <span>{getSelectionIcon(msg.content.selection_type)}</span>
                                <span>{getSelectionLabel(msg.content.selection_type)}:</span>
                              </p>
                              <div className="grid grid-cols-1 gap-2 max-h-64 overflow-y-auto">
                                {msg.content.options.map((option, idx) => (
                                  <button
                                    key={idx}
                                    onClick={() => {
                                      try {
                                        // Validate option before generating command
                                        if (!validateOption(option, msg.content.selection_type)) {
                                          console.error("Invalid option data", option, msg.content.selection_type);
                                          setMessages(prev => [...prev, {
                                            role: "agent",
                                            content: { message: "Invalid option selected. Please try again.", success: false },
                                            timestamp: new Date()
                                          }]);
                                          return;
                                        }
                                        
                                        // Generate command using utility function
                                        const commandObj = makeUserCommand(option, msg.content.selection_type, msg.content.trip_id);
                                        
                                        console.debug(`[MoviWidget] Generated command: ${commandObj.backend_command}`);
                                        
                                        // Add user message showing the selection (user-friendly message)
                                        setMessages(prev => [...prev, {
                                          role: "user",
                                          content: commandObj.user_message,
                                          timestamp: new Date()
                                        }]);
                                        
                                        // Send the backend command to backend
                                        setLoading(true);
                                        handleSendCommand(commandObj.backend_command);
                                        
                                      } catch (error) {
                                        console.error("Error generating command:", error);
                                        setMessages(prev => [...prev, {
                                          role: "agent", 
                                          content: { message: error.message || "Failed to process selection. Please try again.", success: false },
                                          timestamp: new Date()
                                        }]);
                                      }
                                    }}
                                    disabled={loading}
                                    className="px-3 py-3 bg-white hover:bg-green-50 text-gray-800 text-sm rounded-lg border border-green-300 transition-all text-left disabled:opacity-50 shadow-sm hover:shadow-md"
                                  >
                                    <div className="flex items-center justify-between">
                                      <div className="flex-1">
                                        <div className="font-bold text-base">{option.label || option.name || `${msg.content.selection_type} ${idx + 1}`}</div>
                                        <div className="text-xs text-gray-600 mt-1">{option.description || option.reason || 'Available for assignment'}</div>
                                      </div>
                                      <div className="text-2xl ml-2">→</div>
                                    </div>
                                  </button>
                                ))}
                              </div>
                            </div>
                          )}
                          
                          {msg.content.needs_confirmation && (
                            <div className="mt-2 flex gap-2">
                              <button 
                                onClick={() => handleConfirm(msg.content.session_id)}
                                disabled={loading}
                                className="px-3 py-1 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white text-xs rounded transition-colors"
                              >
                                ✓ Confirm
                              </button>
                              <button 
                                onClick={() => handleCancel(msg.content.session_id)}
                                disabled={loading}
                                className="px-3 py-1 bg-red-600 hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white text-xs rounded transition-colors"
                              >
                                ✗ Cancel
                              </button>
                            </div>
                          )}
                          
                          {msg.content.success && !msg.content.needs_confirmation && (
                            <p className="text-xs text-green-600 mt-2">✅ Action completed</p>
                          )}
                        </>
                      )}
                    </div>
                  </>
                )}
              </div>
            ))}

            {/* Loading Indicator */}
            {loading && (
              <div className="flex gap-2">
                <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                  🤖
                </div>
                <div className="bg-white rounded-lg rounded-tl-none p-3 shadow-sm">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                    <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                    <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                  </div>
                </div>
              </div>
            )}

            {/* Placeholder when no messages */}
            {messages.length === 0 && !loading && (
              <div className="text-center text-xs text-gray-400 py-4">
                💡 Try: "Remove vehicle from Bulk - 00:01"
              </div>
            )}
          </div>

          {/* Input Area */}
          <div className="p-3 border-t bg-white rounded-b-2xl">
            <div className="flex gap-2">
              <input
                type="text"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && handleSend()}
                className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder={isListening ? "🎤 Listening..." : "Type a message or use voice..."}
              />
              <button
                onClick={handleSend}
                disabled={!message.trim() || isListening}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white px-4 rounded-lg font-medium transition-colors"
              >
                Send
              </button>
            </div>
            
            {/* Voice Controls */}
            <div className="flex items-center justify-center gap-4 mt-2">
              {/* Voice Input Button */}
              <button 
                onClick={toggleListening}
                className={`text-xs flex items-center gap-1 transition-colors px-2 py-1 rounded ${
                  isListening 
                    ? 'bg-red-100 text-red-600 animate-pulse' 
                    : 'text-gray-500 hover:text-blue-600 hover:bg-blue-50'
                }`}
              >
                🎤 {isListening ? 'Stop' : 'Voice'}
              </button>
              
              {/* TTS Toggle */}
              <button 
                onClick={() => {
                  if (isSpeaking) {
                    stopSpeaking();
                  } else {
                    setVoiceEnabled(!voiceEnabled);
                  }
                }}
                className={`text-xs flex items-center gap-1 transition-colors px-2 py-1 rounded ${
                  isSpeaking 
                    ? 'bg-blue-100 text-blue-600 animate-pulse' 
                    : voiceEnabled 
                      ? 'text-gray-500 hover:text-blue-600 hover:bg-blue-50'
                      : 'text-gray-300'
                }`}
              >
                � {isSpeaking ? 'Stop' : voiceEnabled ? 'Sound On' : 'Sound Off'}
              </button>
              
              {/* Image Upload Button */}
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleImageUpload}
                style={{ display: 'none' }}
              />
              <button 
                onClick={() => fileInputRef.current?.click()}
                disabled={loading}
                className={`text-xs flex items-center gap-1 transition-colors px-2 py-1 rounded ${
                  loading 
                    ? 'text-gray-300 cursor-not-allowed' 
                    : 'text-gray-500 hover:text-blue-600 hover:bg-blue-50'
                }`}
              >
                📸 Image
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
