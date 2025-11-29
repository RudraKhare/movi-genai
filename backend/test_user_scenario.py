#!/usr/bin/env python3
"""
Test the exact scenario from user logs to identify context passing issues
"""
import asyncio
import sys
sys.path.append('.')

from langgraph.nodes.parse_intent_llm import parse_intent_llm

async def test_user_scenario():
    """Test the exact scenario from the logs"""
    
    print("=== Testing User Scenario ===")
    
    # Test 1: User's failing case - "assign vehcile to this trip" with no context
    state1 = {
        "text": "assign vehcile to this trip",  # Note: user's typo included
        "selectedTripId": None,
        "currentPage": None,
        "selectedRouteId": None,
        "from_image": False,
        "conversation_history": [],
        "ui_context": {
            "selectedTripId": None, 
            "selectedRouteId": None, 
            "selectedPathId": None, 
            "currentTrip": None, 
            "lastAction": None, 
            "currentPage": None
        }
    }
    
    print("\n1. Testing failing case: 'assign vehcile to this trip' (no context):")
    result1 = await parse_intent_llm(state1)
    print(f"   Action: {result1.get('action')}")
    print(f"   Confidence: {result1.get('confidence')}")
    print(f"   Needs clarification: {result1.get('needs_clarification')}")
    print(f"   Clarify options: {result1.get('clarify_options')}")
    print(f"   Explanation: {result1.get('llm_explanation')}")
    
    # Test 2: User's working case - "assign vehcile to trip 38" with explicit ID
    state2 = {
        "text": "assign vehcile to trip 38",
        "selectedTripId": None,
        "currentPage": None,
        "conversation_history": [
            {"trip_id": 38, "action": "assign_vehicle", "message": "Previous interaction with trip 38"}
        ],
        "ui_context": {"selectedTripId": None}
    }
    
    print("\n2. Testing working case: 'assign vehcile to trip 38' (explicit ID):")
    result2 = await parse_intent_llm(state2)
    print(f"   Action: {result2.get('action')}")
    print(f"   Target Trip ID: {result2.get('target_trip_id')}")
    print(f"   Confidence: {result2.get('confidence')}")
    print(f"   Needs clarification: {result2.get('needs_clarification')}")
    
    # Test 3: What SHOULD happen - "assign vehicle to this trip" with proper context
    state3 = {
        "text": "assign vehicle to this trip",
        "selectedTripId": 38,
        "currentPage": "busDashboard",
        "ui_context": {"selectedTripId": 38, "currentPage": "busDashboard"}
    }
    
    print("\n3. Testing ideal case: 'assign vehicle to this trip' (with context):")
    result3 = await parse_intent_llm(state3)
    print(f"   Action: {result3.get('action')}")
    print(f"   Target Trip ID: {result3.get('target_trip_id')}")
    print(f"   Confidence: {result3.get('confidence')}")
    print(f"   Needs clarification: {result3.get('needs_clarification')}")
    print(f"   Explanation: {result3.get('llm_explanation')}")
    
    # Test 4: Smart fallback with conversation history
    state4 = {
        "text": "assign driver to this trip",
        "selectedTripId": None,
        "conversation_history": [
            {"trip_id": 38, "action": "assign_driver", "message": "Previous assignment"},
            {"action": "other", "message": "Other message"}
        ],
        "ui_context": {"selectedTripId": None}
    }
    
    print("\n4. Testing smart fallback with conversation history:")
    result4 = await parse_intent_llm(state4)
    print(f"   Action: {result4.get('action')}")
    print(f"   Confidence: {result4.get('confidence')}")
    print(f"   Clarify options: {result4.get('clarify_options')}")
    print(f"   Explanation: {result4.get('llm_explanation')}")

if __name__ == "__main__":
    asyncio.run(test_user_scenario())
