#!/usr/bin/env python3
"""
Check Trip 2 deployment status in detail
"""

import asyncio
import sys
import os

# Add backend to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(backend_dir)

async def check_trip_2_status():
    """Check exactly what's in the database for trip 2"""
    try:
        from langgraph.tools import tool_get_trip_status
        
        print("🔍 Checking Trip 2 detailed status...")
        print("="*50)
        
        # Check trip 2 status
        trip_status = await tool_get_trip_status(2)
        
        print("📋 TRIP 2 DATABASE STATUS:")
        print(f"   Trip ID: {trip_status.get('trip_id')}")
        print(f"   Display Name: {trip_status.get('display_name')}")
        print(f"   Live Status: {trip_status.get('live_status')}")
        print(f"   Vehicle ID: {trip_status.get('vehicle_id')} {'← NO VEHICLE' if not trip_status.get('vehicle_id') else '← HAS VEHICLE'}")
        print(f"   Driver ID: {trip_status.get('driver_id')} {'← NO DRIVER' if not trip_status.get('driver_id') else '← HAS DRIVER'}")
        print(f"   Deployment ID: {trip_status.get('deployment_id')} {'← NO DEPLOYMENT' if not trip_status.get('deployment_id') else '← HAS DEPLOYMENT'}")
        
        print("\n🎯 ANALYSIS:")
        
        if trip_status.get('deployment_id') and not trip_status.get('vehicle_id'):
            print("   ⚠️ ORPHANED DEPLOYMENT DETECTED!")
            print("   📝 What happened:")
            print("      1. Someone created a deployment (got deployment_id: 23)")
            print("      2. But never assigned a vehicle to it")
            print("      3. UI shows 'No vehicle assigned' (correct)")
            print("      4. But database has deployment record (blocks new assignments)")
            print("\n   💡 SOLUTION:")
            print("      Option 1: Delete the orphaned deployment first")
            print("      Option 2: Complete the existing deployment by assigning vehicle")
            print("      Option 3: Allow overwrite of incomplete deployments")
        
        elif not trip_status.get('deployment_id') and not trip_status.get('vehicle_id'):
            print("   ✅ CLEAN TRIP - No deployment, no vehicle")
            print("   Should allow new vehicle assignment")
        
        elif trip_status.get('deployment_id') and trip_status.get('vehicle_id'):
            print("   ✅ COMPLETE DEPLOYMENT - Has both deployment and vehicle")
            print("   Correctly blocks new vehicle assignment")
        
        return trip_status
            
    except Exception as e:
        print(f"❌ Error checking trip status: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(check_trip_2_status())
