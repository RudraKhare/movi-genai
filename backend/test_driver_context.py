#!/usr/bin/env python3
"""
Test driver context awareness directly
"""

import asyncio
import sys
import os

# Add backend to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(backend_dir)

async def test_driver_context():
    """Test driver context handling directly"""
    try:
        from langgraph.nodes.parse_intent_llm import parse_intent_llm
        
        print("🔍 DRIVER CONTEXT TEST")
        print("=" * 50)
        
        # Test case: "assign driver to this trip" with selectedTripId
        state = {
            'text': 'assign driver to this trip',
            'selectedTripId': 5,  # Should trigger context detection
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
        
        if (result.get('action') == 'assign_driver' and 
            result.get('target_trip_id') == 5 and 
            result.get('confidence') == 0.95):
            print("\n   ✅ DRIVER CONTEXT LOGIC WORKING!")
            return True
        else:
            print("\n   ❌ DRIVER CONTEXT LOGIC FAILED")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_driver_context())
