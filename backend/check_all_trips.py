#!/usr/bin/env python3
"""
Check all trips to find deployment patterns
"""

import asyncio
import sys
import os

# Add backend to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(backend_dir)

async def check_all_trips():
    """Check deployment status of multiple trips"""
    try:
        from langgraph.tools import tool_get_trip_status
        
        print("🔍 Checking All Trip Deployment Status")
        print("="*60)
        
        # Check trips 1-10
        for trip_id in range(1, 11):
            try:
                trip_status = await tool_get_trip_status(trip_id)
                
                vehicle_id = trip_status.get('vehicle_id')
                deployment_id = trip_status.get('deployment_id')
                display_name = trip_status.get('display_name', f'Trip {trip_id}')
                
                # Determine status
                if vehicle_id and deployment_id:
                    status = "🔴 COMPLETE (vehicle + deployment)"
                    should_block = "YES"
                elif deployment_id and not vehicle_id:
                    status = "🟡 ORPHANED (deployment only)"  
                    should_block = "NO (allow assignment)"
                elif vehicle_id and not deployment_id:
                    status = "🟠 VEHICLE ONLY (unusual)"
                    should_block = "MAYBE"
                else:
                    status = "🟢 CLEAN (no deployment)"
                    should_block = "NO"
                
                print(f"Trip {trip_id:2d} ({display_name:15s}): vehicle_id={str(vehicle_id):4s} deployment_id={str(deployment_id):4s} → {status} | Block: {should_block}")
                
            except Exception as e:
                print(f"Trip {trip_id:2d}: Error - {e}")
        
        print("\n🎯 LEGEND:")
        print("🔴 COMPLETE = Has both vehicle and deployment → Should BLOCK new assignments")
        print("🟡 ORPHANED = Has deployment but no vehicle → Should ALLOW assignment (fix orphan)")
        print("🟢 CLEAN = No deployment, no vehicle → Should ALLOW assignment")
        print("🟠 UNUSUAL = Has vehicle but no deployment → Review needed")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_all_trips())
