#!/usr/bin/env python3
"""
Test context awareness directly by calling parse_intent_llm
"""

import asyncio
import sys
import os

# Add backend to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(backend_dir)

async def test_context_direct():
    """Test context handling directly"""
    try:
        from langgraph.nodes.parse_intent_llm import parse_intent_llm
        
        print("🔍 DIRECT CONTEXT TEST")
        print("=" * 50)
        
        # Test case 1: "this trip" with selectedTripId
        state = {
            'text': 'assign vehicle to this trip',
            'selectedTripId': 8,
            'user_id': 1
        }
        
        print(f"Input: {state}")
        result = await parse_intent_llm(state)
        
        print(f"\nResult:")
        print(f"   Action: {result.get('action')}")
        print(f"   Target Trip ID: {result.get('target_trip_id')}")
        print(f"   Confidence: {result.get('confidence')}")
        print(f"   Needs Clarification: {result.get('needs_clarification')}")
        print(f"   Explanation: {result.get('llm_explanation')}")
        
        if result.get('action') == 'assign_vehicle' and result.get('target_trip_id') == 8:
            print("\n   ✅ CONTEXT LOGIC WORKING!")
        else:
            print("\n   ❌ CONTEXT LOGIC FAILED")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_context_direct())
