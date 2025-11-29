#!/usr/bin/env python3
import asyncio
import sys
sys.path.append('.')

from langgraph.nodes.parse_intent_llm import parse_intent_llm

async def test_context_awareness_enhanced():
    """Test the enhanced context awareness with better debugging"""
    
    print("=== Testing Enhanced Context Awareness ===")
    
    # Test 1: "this trip" without selectedTripId (should provide helpful guidance)
    state1 = {
        "text": "assign vehicle to this trip",
        "selectedTripId": None,
        "ui_context": {
            "selectedTripId": None,
            "currentPage": "busDashboard"
        }
    }
    
    print("\n1. Testing 'this trip' without selectedTripId (should provide guidance):")
    try:
        result1 = await parse_intent_llm(state1)
        print(f"   Action: {result1.get('action')}")
        print(f"   Confidence: {result1.get('confidence')}")
        print(f"   Needs clarification: {result1.get('needs_clarification')}")
        print(f"   Clarify options: {result1.get('clarify_options')}")
        print(f"   Explanation: {result1.get('llm_explanation')}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 2: "this trip" with selectedTripId (should use context)
    state2 = {
        "text": "assign vehicle to this trip",
        "selectedTripId": 38,
        "ui_context": {
            "selectedTripId": 38,
            "currentPage": "busDashboard"
        }
    }
    
    print("\n2. Testing 'this trip' with selectedTripId=38 (should use context):")
    try:
        result2 = await parse_intent_llm(state2)
        print(f"   Action: {result2.get('action')}")
        print(f"   Target Trip ID: {result2.get('target_trip_id')}")
        print(f"   Confidence: {result2.get('confidence')}")
        print(f"   Needs clarification: {result2.get('needs_clarification')}")
        print(f"   Explanation: {result2.get('llm_explanation')}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: Ambiguous reference without context
    state3 = {
        "text": "allocate vehicle here",
        "selectedTripId": None,
        "ui_context": {"selectedTripId": None}
    }
    
    print("\n3. Testing ambiguous reference without context:")
    try:
        result3 = await parse_intent_llm(state3)
        print(f"   Action: {result3.get('action')}")
        print(f"   Confidence: {result3.get('confidence')}")
        print(f"   Clarify options: {result3.get('clarify_options')}")
        print(f"   Explanation: {result3.get('llm_explanation')}")
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_context_awareness_enhanced())
