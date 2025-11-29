#!/usr/bin/env python3
import asyncio
import sys
sys.path.append('.')

from langgraph.nodes.parse_intent_llm import parse_intent_llm

async def test_vehicle_assignment():
    """Test the exact scenario from the error log"""
    
    print("=== Testing 'assign vehicle to this trip' scenarios ===")
    
    # Test 1: Without selectedTripId (the failing case)
    state1 = {
        "text": "assign vehicle to this trip",
        "selectedTripId": None,
        "currentPage": None,
        "selectedRouteId": None,
        "selectedPathId": None,
        "conversation_history": [],
        "trip_details": None,
        "last_offered_options": None,
        "awaiting_selection": None,
        "ui_context": {
            "selectedTripId": None,
            "selectedRouteId": None,
            "selectedPathId": None,
            "currentTrip": None,
            "lastAction": None
        }
    }
    
    print("\n1. Testing without selectedTripId (should go to LLM):")
    try:
        result1 = await parse_intent_llm(state1)
        print(f"   Action: {result1.get('action')}")
        print(f"   Confidence: {result1.get('confidence')}")
        print(f"   Needs clarification: {result1.get('needs_clarification')}")
        print(f"   Explanation: {result1.get('llm_explanation')}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 2: With selectedTripId (should use context)
    state2 = {
        "text": "assign vehicle to this trip",
        "selectedTripId": 123,
        "currentPage": None,
        "selectedRouteId": None,
        "selectedPathId": None,
        "conversation_history": [],
        "trip_details": None,
        "last_offered_options": None,
        "awaiting_selection": None,
        "ui_context": {
            "selectedTripId": 123,
            "selectedRouteId": None,
            "selectedPathId": None,
            "currentTrip": None,
            "lastAction": None
        }
    }
    
    print("\n2. Testing with selectedTripId=123 (should use context):")
    try:
        result2 = await parse_intent_llm(state2)
        print(f"   Action: {result2.get('action')}")
        print(f"   Target Trip ID: {result2.get('target_trip_id')}")
        print(f"   Confidence: {result2.get('confidence')}")
        print(f"   Needs clarification: {result2.get('needs_clarification')}")
        print(f"   Explanation: {result2.get('llm_explanation')}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: Simple "assign vehicle" with selectedTripId
    state3 = {
        "text": "assign vehicle",
        "selectedTripId": 456,
    }
    
    print("\n3. Testing simple 'assign vehicle' with selectedTripId=456:")
    try:
        result3 = await parse_intent_llm(state3)
        print(f"   Action: {result3.get('action')}")
        print(f"   Target Trip ID: {result3.get('target_trip_id')}")
        print(f"   Confidence: {result3.get('confidence')}")
        print(f"   Explanation: {result3.get('llm_explanation')}")
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_vehicle_assignment())
