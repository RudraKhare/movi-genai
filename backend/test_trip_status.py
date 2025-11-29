#!/usr/bin/env python3
"""
Test trip status retrieval
"""

import asyncio
import sys
import os

# Add backend to path  
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(backend_dir)

async def test_trip_status():
    """Test getting trip status for trip 5"""
    try:
        from langgraph.tools import tool_get_trip_status
        
        print("🔧 Testing tool_get_trip_status for trip 5...")
        
        # Check trip 5 status
        trip_status = await tool_get_trip_status(5)
        
        print(f"📋 Trip 5 Status: {trip_status}")
        print(f"   Vehicle ID: {trip_status.get('vehicle_id')}")
        print(f"   Has vehicle: {bool(trip_status.get('vehicle_id'))}")
        
        if trip_status.get('vehicle_id'):
            print(f"\n✅ TRIP 5 HAS DEPLOYMENT!")
            print(f"   Vehicle ID: {trip_status.get('vehicle_id')}")
            print("   This should trigger deployment check in decision_router")
        else:
            print(f"\n❌ TRIP 5 HAS NO DEPLOYMENT")
            print("   No vehicle assigned - deployment check won't trigger")
            
    except Exception as e:
        print(f"❌ Error testing trip status: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_trip_status())
