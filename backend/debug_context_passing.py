#!/usr/bin/env python3
"""
Diagnostic script to help identify context passing issues between frontend and backend
"""
import asyncio
import sys
sys.path.append('.')

from app.api.agent import AgentMessageRequest
from langgraph.nodes.parse_intent_llm import parse_intent_llm

async def simulate_frontend_request():
    """Simulate what frontend should be sending"""
    
    print("=== Frontend Context Debugging ===")
    
    # Simulate the exact request that should work
    request_data = {
        "text": "assign vehicle to this trip",
        "user_id": 1,
        "selectedTripId": 38,  # This should be coming from frontend
        "currentPage": "busDashboard",
        "selectedRouteId": None,
        "from_image": False,
        "conversation_history": []
    }
    
    print(f"Simulating frontend request: {request_data}")
    
    # Create the request object
    request = AgentMessageRequest(**request_data)
    
    print(f"AgentMessageRequest created: selectedTripId={request.selectedTripId}")
    
    # Simulate what the API handler does
    ui_context = {
        "selectedTripId": request.selectedTripId,
        "selectedRouteId": request.selectedRouteId,
        "currentPage": request.currentPage
    }
    
    input_state = {
        "text": request.text,
        "user_id": request.user_id,
        "selectedTripId": request.selectedTripId,
        "currentPage": request.currentPage,
        "selectedRouteId": request.selectedRouteId,
        "from_image": request.from_image,
        "conversation_history": request.conversation_history,
        "ui_context": ui_context
    }
    
    print(f"Input state created: {input_state}")
    
    # Test the parse_intent_llm node directly
    result = await parse_intent_llm(input_state)
    
    print(f"\nResult:")
    print(f"  Action: {result.get('action')}")
    print(f"  Target Trip ID: {result.get('target_trip_id')}")
    print(f"  Confidence: {result.get('confidence')}")
    print(f"  Needs clarification: {result.get('needs_clarification')}")
    print(f"  Explanation: {result.get('llm_explanation')}")
    
    return result

if __name__ == "__main__":
    result = asyncio.run(simulate_frontend_request())
    
    print("\n=== Diagnosis ===")
    if result.get('target_trip_id') == 38:
        print("✅ SUCCESS: Context passing works correctly")
        print("❓ Issue is likely in frontend state management")
        print("   - Check if selectedTrip is actually set in BusDashboard")
        print("   - Check browser console for MoviWidget context logs")
        print("   - Verify trip selection is maintained between commands")
    else:
        print("❌ FAILURE: Backend context processing has issues")
        print("   - Check parse_intent_llm node implementation")
        print("   - Verify context awareness logic")
