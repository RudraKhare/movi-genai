#!/usr/bin/env python3
"""
Test the updated deployment logic with different scenarios
"""

import asyncio
import sys
import os

# Add backend to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(backend_dir)

async def test_deployment_scenarios():
    """Test different deployment scenarios"""
    try:
        from langgraph.nodes.decision_router import decision_router
        from langgraph.tools import tool_get_trip_status
        
        print("🧪 Testing Updated Deployment Logic")
        print("="*60)
        
        # Test Trip 2 (orphaned deployment)
        print("\n🔍 TEST 1: Trip 2 (Orphaned Deployment)")
        print("-" * 40)
        
        trip2_status = await tool_get_trip_status(2)
        print(f"Trip 2 Status: vehicle_id={trip2_status.get('vehicle_id')}, deployment_id={trip2_status.get('deployment_id')}")
        
        test_state_2 = {
            "action": "assign_vehicle",
            "trip_id": 2,
            "from_image": False,
            "resolve_result": "found",
            "parsed_params": {
                "trip_id": 2,
                "vehicle_id": 8,
                "vehicle_name": "Honda"
            }
        }
        
        result_2 = await decision_router(test_state_2)
        print(f"Result: next_node={result_2.get('next_node')}, error={result_2.get('error')}")
        
        if result_2.get('next_node') == 'check_consequences':
            print("✅ PASS: Orphaned deployment allows vehicle assignment")
        else:
            print("❌ FAIL: Orphaned deployment should allow assignment")
        
        # Test Trip 5 (complete deployment)
        print("\n🔍 TEST 2: Trip 5 (Complete Deployment)")
        print("-" * 40)
        
        trip5_status = await tool_get_trip_status(5)
        print(f"Trip 5 Status: vehicle_id={trip5_status.get('vehicle_id')}, deployment_id={trip5_status.get('deployment_id')}")
        
        test_state_5 = {
            "action": "assign_vehicle",
            "trip_id": 5,
            "from_image": False,
            "resolve_result": "found",
            "parsed_params": {
                "trip_id": 5,
                "vehicle_id": 8,
                "vehicle_name": "Honda"
            }
        }
        
        result_5 = await decision_router(test_state_5)
        print(f"Result: next_node={result_5.get('next_node')}, error={result_5.get('error')}")
        
        if result_5.get('error') == 'already_deployed':
            print("✅ PASS: Complete deployment blocks vehicle assignment")
        else:
            print("❌ FAIL: Complete deployment should block assignment")
        
        print("\n" + "="*60)
        print("🎯 SUMMARY:")
        print("✅ Orphaned deployments (deployment_id but no vehicle_id) → Allow assignment")
        print("❌ Complete deployments (both deployment_id and vehicle_id) → Block assignment")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_deployment_scenarios())
