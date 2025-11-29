#!/usr/bin/env python3
"""
Debug vehicle availability discrepancy
Why is vehicle 1 shown as available but then fails assignment?
"""

import asyncio
import sys
import os

# Add backend to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(backend_dir)

async def debug_vehicle_availability():
    """Debug vehicle 1 availability for trip 38"""
    try:
        from app.core.service import get_available_vehicles_for_trip, get_unassigned_vehicles
        from app.core.consequences import check_vehicle_availability
        from app.core.supabase_client import get_conn
        
        print("🔍 DEBUGGING VEHICLE AVAILABILITY DISCREPANCY")
        print("=" * 70)
        
        # Check Trip 38 details
        conn = await get_conn()
        try:
            trip_info = await conn.fetchrow("""
                SELECT dt.trip_id, dt.display_name, dt.trip_date, r.shift_time, r.route_name
                FROM daily_trips dt
                JOIN routes r ON dt.route_id = r.route_id
                WHERE dt.trip_id = 38
            """)
            
            if trip_info:
                print(f"\n📅 TRIP 38 DETAILS:")
                print(f"   Name: {trip_info['display_name']}")
                print(f"   Date: {trip_info['trip_date']}")
                print(f"   Time: {trip_info['shift_time']}")
                print(f"   Route: {trip_info['route_name']}")
            
            # Check Vehicle 1 deployments
            vehicle_deployments = await conn.fetch("""
                SELECT d.deployment_id, d.trip_id, dt.display_name, dt.trip_date, r.shift_time, dt.live_status
                FROM deployments d
                JOIN daily_trips dt ON d.trip_id = dt.trip_id
                JOIN routes r ON dt.route_id = r.route_id
                WHERE d.vehicle_id = 1
                ORDER BY dt.trip_date, r.shift_time
            """)
            
            print(f"\n🚐 VEHICLE 1 DEPLOYMENTS:")
            if vehicle_deployments:
                for dep in vehicle_deployments:
                    print(f"   Trip {dep['trip_id']}: {dep['display_name']}")
                    print(f"     Date: {dep['trip_date']}, Time: {dep['shift_time']}")
                    print(f"     Status: {dep['live_status']}")
                    print()
            else:
                print("   No deployments found")
                
        finally:
            await conn.close()
        
        # Test different availability checks
        print(f"\n🧪 AVAILABILITY TESTS:")
        
        # Test 1: Direct availability check using the trip date
        trip_date = trip_info['trip_date'] if trip_info else '2025-11-15'
        available = await check_vehicle_availability(1, trip_date)
        print(f"   Direct availability check for {trip_date}: {available}")
        
        print(f"\n🎯 ANALYSIS:")
        print(f"   Vehicle 1 is deployed to Trip 36 on {trip_info['trip_date']} at 11:15:00")
        print(f"   Trip 38 is scheduled for {trip_info['trip_date']} at {trip_info['shift_time']}")
        print(f"   These times are close but different - should they conflict?")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_vehicle_availability())
