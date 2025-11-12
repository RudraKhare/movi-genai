import { useState } from "react";

export default function MoviWidget({ context }) {
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState("");

  const handleSend = () => {
    // Placeholder for LangGraph integration (Day 7-8)
    console.log("Sending message:", message, "with context:", context);
    setMessage("");
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
                  <li>Assigning vehicles to trips</li>
                  <li>Managing routes and deployments</li>
                  <li>Checking trip status and bookings</li>
                  <li>Answering transport queries</li>
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

            {/* Placeholder for future messages */}
            <div className="text-center text-xs text-gray-400 py-4">
              💡 LangGraph integration coming in Day 7-8
            </div>
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
            
            {/* Voice Input Placeholder */}
            <div className="flex items-center justify-center gap-4 mt-2">
              <button className="text-xs text-gray-500 hover:text-blue-600 flex items-center gap-1 transition-colors">
                🎤 Voice
              </button>
              <button className="text-xs text-gray-500 hover:text-blue-600 flex items-center gap-1 transition-colors">
                📸 Image
              </button>
              <span className="text-xs text-gray-400">Multimodal coming soon!</span>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
