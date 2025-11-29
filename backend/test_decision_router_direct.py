#!/usr/bin/env python3
"""
Direct test of decision_router logic
"""

import asyncio
import sys
import os

# Add backend to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(backend_dir)

async def test_decision_router():
    """Test decision_router directly"""
    try:
        from langgraph.nodes.decision_router import decision_router
        
        # Simulate the state that would reach decision_router for structured command
        test_state = {
            "action": "assign_vehicle",
            "trip_id": 5,
            "from_image": False,
            "resolve_result": "found",
            "parsed_params": {
                "trip_id": 5,
                "vehicle_id": 8,
                "vehicle_name": "Honda",
                "context": "selection_ui"
            }
        }
        
        print("🔧 Testing decision_router directly...")
        print(f"Input state: {test_state}")
        print()
        
        # Call decision_router
        result_state = await decision_router(test_state)
        
        print("🎯 Result:")
        print(f"  Next node: {result_state.get('next_node')}")
        print(f"  Status: {result_state.get('status')}")
        print(f"  Error: {result_state.get('error')}")
        print(f"  Message: {result_state.get('message', '')}")
        
        if result_state.get('error') == 'already_deployed':
            print("\n✅ DEPLOYMENT CHECK WORKING!")
            print("   decision_router properly caught deployment conflict")
        else:
            print("\n❌ DEPLOYMENT CHECK NOT WORKING")
            print(f"   Expected error='already_deployed', got error='{result_state.get('error')}'")
            print(f"   Next node: {result_state.get('next_node')}")
        
    except Exception as e:
        print(f"❌ Error testing decision_router: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_decision_router())
