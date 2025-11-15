import { useState, useEffect } from "react";
import axios from "axios";
import TableCard from "./TableCard";
import ListCard from "./ListCard";
import ObjectCard from "./ObjectCard";
import HelpCard from "./HelpCard";

const API_BASE = "http://localhost:8000/api";
const API_KEY = "dev-key-change-in-production";

// Generate a valid UUID v4
function generateUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

export default function MoviWidget({ context }) {
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const fileInputRef = useState(null)[0]; // Create ref for file input

  // Generate session ID on mount
  useEffect(() => {
    const storedSessionId = localStorage.getItem('movi_session_id');
    if (storedSessionId) {
      setSessionId(storedSessionId);
    } else {
      const newSessionId = generateUUID();
      localStorage.setItem('movi_session_id', newSessionId);
      setSessionId(newSessionId);
    }
  }, []);

  const handleImageUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    console.log("[PHASE 1] Uploading image:", file.name);
    
    // Add user message showing image upload
    setMessages(prev => [...prev, {
      role: "user",
      content: `📸 Uploaded image: ${file.name}`,
      timestamp: new Date()
    }]);
    
    setLoading(true);

    try {
      // PHASE 1: OCR - Extract text from image
      const formData = new FormData();
      formData.append("file", file);

      console.log("[PHASE 1] Calling OCR endpoint...");
      const ocrResponse = await axios.post(
        `${API_BASE}/agent/image`,
        formData,
        {
          headers: {
            "x-api-key": API_KEY,
            "Content-Type": "multipart/form-data"
          }
        }
      );

      console.log("[PHASE 1] ✅ OCR response:", ocrResponse.data);

      const { match_type, ocr_text, confidence, error } = ocrResponse.data;

      if (match_type !== "text_extracted") {
        throw new Error("Unexpected OCR response format");
      }

      if (error) {
        throw new Error(error);
      }

      if (!ocr_text || ocr_text.trim().length === 0) {
        setMessages(prev => [...prev, {
          role: "agent",
          content: {
            message: "❌ No readable text found in image. Please try a clearer image.",
            success: false
          },
          timestamp: new Date()
        }]);
        setLoading(false);
        return;
      }

      // Show OCR extraction success
      const preview = ocr_text.length > 100 ? ocr_text.substring(0, 100) + "..." : ocr_text;
      setMessages(prev => [...prev, {
        role: "agent",
        content: {
          message: `✅ Extracted text from image\n📊 Confidence: ${(confidence * 100).toFixed(1)}%\n\n📝 Preview:\n"${preview}"\n\n⏳ Analyzing with AI...`,
          success: true
        },
        timestamp: new Date()
      }]);

      // PHASE 2-5: Send OCR text to agent with from_image flag
      // LLM + LangGraph will handle all intelligence
      console.log("[PHASE 2-5] Starting agent call...");
      console.log("[PHASE 2-5] Session ID:", sessionId);
      console.log("[PHASE 2-5] OCR text length:", ocr_text.length);
      
      const agentResponse = await axios.post(
        `${API_BASE}/agent/message`,
        {
          text: ocr_text,
          user_id: 1,
          session_id: sessionId,  // ✅ Use proper UUID session ID
          from_image: true,  // ✅ CRITICAL: Tells LangGraph this came from OCR
          currentPage: context?.page,
          selectedRouteId: context?.routeId
        },
        {
          headers: {
            "x-api-key": API_KEY,
            "Content-Type": "application/json"
          }
        }
      );

      console.log("[PHASE 2-5] ✅ Agent response:", agentResponse.data);
      console.log("[DEBUG] agent_output:", agentResponse.data.agent_output);
      console.log("[DEBUG] suggestions:", agentResponse.data.agent_output?.suggestions);

      // Add agent response to chat
      setMessages(prev => [...prev, {
        role: "agent",
        content: agentResponse.data.agent_output,  // ✅ FIX: Extract agent_output from response
        timestamp: new Date()
      }]);

    } catch (error) {
      console.error("[ERROR] Image processing failed:", error);
      
      setMessages(prev => [...prev, {
        role: "agent",
        content: {
          message: `❌ Error: ${error.response?.data?.detail || error.message}`,
          success: false
        },
        timestamp: new Date()
      }]);
    } finally {
      setLoading(false);
      // Reset file input
      event.target.value = null;
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

    try {
      // Call agent API
      const response = await axios.post(
        `${API_BASE}/agent/message`,
        {
          text: userMessage,
          user_id: 1,
          session_id: sessionId,  // ✅ Use proper UUID session ID
          currentPage: context?.currentPage || null,
          selectedRouteId: context?.selectedRouteId || null,
          selectedTripId: context?.selectedTripId || null,
          conversation_history: []
        },
        {
          headers: {
            "x-api-key": API_KEY,
            "Content-Type": "application/json"
          }
        }
      );

      console.log("Agent response:", response.data);

      // Add agent response to chat
      setMessages(prev => [...prev, {
        role: "agent",
        content: response.data.agent_output,
        timestamp: new Date()
      }]);

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

  // Handle suggestion button clicks (Phase 3)
  const handleSuggestionClick = (action, tripId) => {
    const actionText = actionToText(action, tripId);
    setMessage(actionText);
    handleSend();
  };

  // Convert action to natural language (Phase 3)
  const actionToText = (action, tripId) => {
    const tripRef = tripId ? ` ${tripId}` : "";
    const actionMap = {
      "get_trip_bookings": `Show me the bookings for trip${tripRef}`,
      "change_driver": `Change the driver for trip${tripRef}`,
      "duplicate_trip": `Duplicate trip${tripRef}`,
      "create_followup_trip": `Create a follow-up trip for trip${tripRef}`,
      "cancel_trip": `Cancel trip${tripRef}`,
      "remove_vehicle": `Remove the vehicle from trip${tripRef}`,
      "assign_vehicle": `Assign a vehicle to trip${tripRef}`,
      "update_trip_time": `Update the trip time for trip${tripRef}`,
      "get_trip_details": `Show me the details for trip${tripRef}`,
      "get_trip_status": `What's the status of trip${tripRef}?`,
      "create_trip_from_scratch": "Help me create a new trip",
      "show_trip_suggestions": "What can I do with this trip?",
    };
    return actionMap[action] || action;
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
                  I can help you with 16+ actions:
                </p>
                <div className="text-xs text-gray-700 mt-2 space-y-1">
                  <details className="cursor-pointer">
                    <summary className="font-semibold text-blue-600">📊 View Data (6 actions)</summary>
                    <ul className="ml-4 mt-1 space-y-0.5 list-disc">
                      <li>Get unassigned vehicles</li>
                      <li>Check trip status & details</li>
                      <li>List all stops, stops for path</li>
                      <li>Find routes using a path</li>
                    </ul>
                  </details>
                  <details className="cursor-pointer">
                    <summary className="font-semibold text-green-600">✏️ Create & Modify (5 actions)</summary>
                    <ul className="ml-4 mt-1 space-y-0.5 list-disc">
                      <li>Create stops, paths, routes</li>
                      <li>Rename stops</li>
                      <li>Duplicate routes</li>
                    </ul>
                  </details>
                  <details className="cursor-pointer">
                    <summary className="font-semibold text-orange-600">🚌 Trip Operations (4 actions)</summary>
                    <ul className="ml-4 mt-1 space-y-0.5 list-disc">
                      <li>Assign/remove vehicles</li>
                      <li>Cancel trips</li>
                      <li>Update trip times</li>
                    </ul>
                  </details>
                  <details className="cursor-pointer">
                    <summary className="font-semibold text-purple-600">💡 Help</summary>
                    <ul className="ml-4 mt-1 space-y-0.5 list-disc">
                      <li>Get route creation guide</li>
                    </ul>
                  </details>
                </div>
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
                      {msg.content.success === false ? (
                        <p className="text-sm text-red-600">❌ {msg.content.message}</p>
                      ) : (
                        <>
                          {/* Text message */}
                          {msg.content.message && (
                            <p className="text-sm text-gray-800 whitespace-pre-line mb-2">
                              {msg.content.message}
                            </p>
                          )}
                          
                          {/* DEBUG: Show raw suggestions data */}
                          {msg.content.suggestions && (
                            <div className="text-xs bg-yellow-100 p-2 rounded mb-2">
                              🐛 DEBUG: Found {msg.content.suggestions.length} suggestions
                            </div>
                          )}
                          
                          {/* Formatted output (table, list, object, help) */}
                          {msg.content.final_output && (
                            <div className="mt-2">
                              {msg.content.final_output.type === "table" && (
                                <TableCard 
                                  data={msg.content.final_output.data} 
                                  columns={msg.content.final_output.columns}
                                />
                              )}
                              {msg.content.final_output.type === "list" && (
                                <ListCard items={msg.content.final_output.data} />
                              )}
                              {msg.content.final_output.type === "object" && (
                                <ObjectCard data={msg.content.final_output.data} />
                              )}
                              {msg.content.final_output.type === "help" && (
                                <HelpCard data={msg.content.final_output.data} />
                              )}
                            </div>
                          )}
                          
                          {/* Consequences warning */}
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
                          
                          {/* Available Actions from Image OCR */}
                          {msg.content.available_actions && msg.content.available_actions.length > 0 && (
                            <div className="mt-3 p-3 bg-gray-50 border border-gray-200 rounded">
                              <p className="text-xs font-semibold text-gray-700 mb-2">📋 Available Actions:</p>
                              <div className="grid grid-cols-2 gap-2">
                                {msg.content.available_actions.map((action, idx) => (
                                  <button
                                    key={idx}
                                    onClick={() => {
                                      // Format action command with trip_id
                                      let command = "";
                                      if (action.action === "get_trip_status") {
                                        command = `Get status for trip ${msg.content.trip_id}`;
                                      } else if (action.action === "get_trip_details") {
                                        command = `Show details for trip ${msg.content.trip_id}`;
                                      } else if (action.action === "assign_vehicle") {
                                        command = `Assign vehicle to trip ${msg.content.trip_id}`;
                                      } else if (action.action === "remove_vehicle") {
                                        command = `Remove vehicle from trip ${msg.content.trip_id}`;
                                      } else if (action.action === "cancel_trip") {
                                        command = `Cancel trip ${msg.content.trip_id}`;
                                      } else if (action.action === "update_trip_time") {
                                        command = `Update time for trip ${msg.content.trip_id}`;
                                      } else {
                                        command = action.description;
                                      }
                                      
                                      // Send command to agent
                                      setMessage(command);
                                      handleSend(command);
                                    }}
                                    disabled={loading}
                                    className={`px-2 py-2 text-xs rounded transition-colors text-left ${
                                      action.warning 
                                        ? 'bg-red-50 hover:bg-red-100 text-red-700 border border-red-200' 
                                        : 'bg-white hover:bg-blue-50 text-gray-700 border border-gray-300'
                                    } disabled:opacity-50 disabled:cursor-not-allowed`}
                                    title={action.description}
                                  >
                                    <div className="font-medium">{action.label}</div>
                                    <div className="text-[10px] text-gray-500 mt-0.5">{action.description.slice(0, 40)}...</div>
                                  </button>
                                ))}
                              </div>
                            </div>
                          )}
                          
                          {/* Phase 3: Suggestion Buttons (from suggestion_provider node) */}
                          {msg.content.suggestions && msg.content.suggestions.length > 0 && (
                            <div className="mt-3 p-3 bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-lg">
                              <p className="text-xs font-semibold text-blue-800 mb-2 flex items-center gap-1">
                                <span>✨</span>
                                <span>Suggested Actions:</span>
                              </p>
                              <div className="grid grid-cols-2 gap-2">
                                {msg.content.suggestions.map((suggestion, idx) => (
                                  <button
                                    key={idx}
                                    onClick={() => handleSuggestionClick(suggestion.action, msg.content.trip_id)}
                                    disabled={loading}
                                    className={`px-3 py-2 text-xs rounded-lg transition-all transform hover:scale-105 text-left ${
                                      suggestion.warning 
                                        ? 'bg-red-50 hover:bg-red-100 text-red-800 border-2 border-red-300 shadow-md' 
                                        : 'bg-white hover:bg-blue-50 text-gray-800 border border-blue-300 shadow-sm'
                                    } disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none`}
                                    title={suggestion.description}
                                  >
                                    <div className="font-semibold">{suggestion.label}</div>
                                    {suggestion.description && (
                                      <div className="text-[10px] text-gray-600 mt-1">
                                        {suggestion.description.slice(0, 50)}{suggestion.description.length > 50 ? '...' : ''}
                                      </div>
                                    )}
                                  </button>
                                ))}
                              </div>
                            </div>
                          )}
                          
                          {/* Vehicle/Driver Selection UI (from vehicle_selection_provider node) */}
                          {msg.content.options && msg.content.options.length > 0 && msg.content.awaiting_selection && (
                            <div className="mt-3 p-3 bg-gradient-to-br from-green-50 to-blue-50 border border-green-200 rounded-lg">
                              <p className="text-xs font-semibold text-green-800 mb-2 flex items-center gap-1">
                                <span>🚗</span>
                                <span>Available {msg.content.selection_type === 'vehicle' ? 'Vehicles' : 'Options'}:</span>
                              </p>
                              <div className="grid grid-cols-1 gap-2 max-h-64 overflow-y-auto">
                                {msg.content.options.map((option, idx) => (
                                  <button
                                    key={idx}
                                    onClick={() => {
                                      // Send vehicle selection as structured command
                                      const command = `Assign vehicle ${option.vehicle_id} to trip ${msg.content.trip_id}`;
                                      setMessage(command);
                                      handleSend();
                                    }}
                                    disabled={loading}
                                    className="px-3 py-3 bg-white hover:bg-green-50 text-gray-800 text-sm rounded-lg border border-green-300 transition-all text-left disabled:opacity-50 shadow-sm hover:shadow-md"
                                  >
                                    <div className="flex items-center justify-between">
                                      <div className="flex-1">
                                        <div className="font-bold text-base">{option.label}</div>
                                        <div className="text-xs text-gray-600 mt-1">{option.description}</div>
                                      </div>
                                      <div className="text-2xl ml-2">→</div>
                                    </div>
                                  </button>
                                ))}
                              </div>
                            </div>
                          )}
                          
                          {/* Phase 3: Wizard UI (multi-step creation flow) */}
                          {msg.content.wizard_active && (
                            <div className="mt-3 p-4 bg-gradient-to-br from-purple-50 to-pink-50 border-2 border-purple-300 rounded-lg shadow-lg">
                              {/* Wizard Progress Bar */}
                              <div className="mb-3">
                                <div className="flex items-center justify-between text-xs text-purple-700 mb-1">
                                  <span className="font-semibold">🧙‍♂️ Creation Wizard</span>
                                  <span className="font-mono">
                                    Step {(msg.content.wizard_step || 0) + 1} / {msg.content.wizard_steps_total || '?'}
                                  </span>
                                </div>
                                <div className="w-full bg-purple-200 rounded-full h-2 overflow-hidden">
                                  <div 
                                    className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full transition-all duration-300"
                                    style={{ 
                                      width: `${((msg.content.wizard_step || 0) + 1) / (msg.content.wizard_steps_total || 1) * 100}%` 
                                    }}
                                  />
                                </div>
                              </div>
                              
                              {/* Wizard Question */}
                              <div className="mb-3">
                                <p className="text-sm font-semibold text-purple-900 mb-1">
                                  {msg.content.wizard_question || msg.content.message}
                                </p>
                                {msg.content.wizard_hint && (
                                  <p className="text-xs text-purple-600 italic">
                                    💡 {msg.content.wizard_hint}
                                  </p>
                                )}
                              </div>
                              
                              {/* Collected Data So Far */}
                              {msg.content.wizard_data && Object.keys(msg.content.wizard_data).length > 0 && (
                                <div className="bg-white bg-opacity-60 rounded p-2 border border-purple-200">
                                  <p className="text-xs font-semibold text-purple-800 mb-1">📝 Collected so far:</p>
                                  <ul className="text-xs text-gray-700 space-y-0.5">
                                    {Object.entries(msg.content.wizard_data).map(([key, val]) => (
                                      <li key={key} className="flex gap-1">
                                        <span className="font-medium text-purple-700">{key}:</span>
                                        <span className="text-gray-800">{val}</span>
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                              
                              {/* Options (if provided) */}
                              {msg.content.options && msg.content.options.length > 0 && (
                                <div className="mt-3">
                                  <p className="text-xs font-semibold text-purple-700 mb-2">Choose one:</p>
                                  <div className="grid grid-cols-2 gap-2 max-h-40 overflow-y-auto">
                                    {msg.content.options.map((option, idx) => (
                                      <button
                                        key={idx}
                                        onClick={() => {
                                          setMessage(option.name || option.id);
                                          handleSend();
                                        }}
                                        disabled={loading}
                                        className="px-2 py-2 bg-white hover:bg-purple-100 text-purple-900 text-xs rounded border border-purple-300 transition-colors text-left disabled:opacity-50"
                                      >
                                        <div className="font-medium">{option.name || option.id}</div>
                                        {option.description && (
                                          <div className="text-[10px] text-gray-600 mt-0.5">
                                            {option.description}
                                          </div>
                                        )}
                                      </button>
                                    ))}
                                  </div>
                                </div>
                              )}
                              
                              {/* Cancel Wizard Button */}
                              <div className="mt-3 pt-2 border-t border-purple-200">
                                <button
                                  onClick={() => {
                                    setMessage("cancel");
                                    handleSend();
                                  }}
                                  disabled={loading}
                                  className="w-full px-2 py-1 bg-red-100 hover:bg-red-200 text-red-700 text-xs rounded transition-colors disabled:opacity-50"
                                >
                                  ✗ Cancel Wizard
                                </button>
                              </div>
                            </div>
                          )}
                          
                          {/* Confirmation buttons */}
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
                          
                          {/* Success indicator */}
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
              <div className="text-center text-xs text-gray-400 py-4 space-y-1">
                <p className="font-semibold text-gray-500">💡 Try these commands:</p>
                <p>"Show me unassigned vehicles"</p>
                <p>"List all stops"</p>
                <p>"Remove vehicle from Bulk - 00:01"</p>
                <p>"Create stop Library at 12.34, 56.78"</p>
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
                placeholder="Type a message or use voice..."
              />
              <button
                onClick={handleSend}
                disabled={!message.trim()}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white px-4 rounded-lg font-medium transition-colors"
              >
                Send
              </button>
            </div>
            
            {/* Hidden file input */}
            <input
              type="file"
              accept="image/*"
              onChange={handleImageUpload}
              style={{ display: 'none' }}
              id="image-upload-input"
            />
            
            {/* Voice and Image Input */}
            <div className="flex items-center justify-center gap-4 mt-2">
              <button 
                className="text-xs text-gray-500 hover:text-blue-600 flex items-center gap-1 transition-colors"
                disabled
              >
                🎤 Voice
              </button>
              <button 
                onClick={() => document.getElementById('image-upload-input').click()}
                className="text-xs text-gray-600 hover:text-blue-600 flex items-center gap-1 transition-colors font-medium"
                disabled={loading}
              >
                📸 Image
              </button>
              <span className="text-xs text-gray-400">Upload trip screenshot for OCR</span>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
