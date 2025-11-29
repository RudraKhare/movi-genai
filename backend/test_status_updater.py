#!/usr/bin/env python3
"""
Test Automatic Trip Status Updater

This script tests the automatic status updater functionality:
1. Creates test trips with different times
2. Forces status updates
3. Verifies status transitions work correctly
"""

import asyncio
import sys
import os
from datetime import datetime, time as dt_time, timedelta

# Add backend to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(backend_dir)

from app.core.supabase_client import get_conn

async def test_status_updater():
    """Test the automatic status updater functionality"""
    try:
        from app.core.status_updater import force_update_trip_statuses, manually_update_trip_status
        
        print("🧪 Testing Automatic Trip Status Updater")
        print("=" * 60)
        
        # Get current time for testing
        current_time = datetime.now()
        current_time_only = current_time.time()
        current_date = current_time.date()
        
        print(f"⏰ Current time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📅 Testing with date: {current_date}")
        
        # Create test scenario trips if needed
        await create_test_trips(current_date, current_time_only)
        
        print("\n🔍 BEFORE Status Update:")
        await check_trip_statuses(current_date)
        
        print("\n🚀 Running forced status update...")
        await force_update_trip_statuses()
        
        print("\n✅ AFTER Status Update:")
        await check_trip_statuses(current_date)
        
        print("\n🧪 Testing manual status override...")
        await test_manual_override(current_date)
        
        print("\n✅ Status updater test completed!")
        
    except Exception as e:
        print(f"❌ Error testing status updater: {e}")
        import traceback
        traceback.print_exc()

async def create_test_trips(current_date, current_time):
    """Create test trips with specific times for testing"""
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            
            # Check if we have trips for today
            existing_trips = await conn.fetch("""
                SELECT trip_id, display_name, live_status FROM daily_trips 
                WHERE trip_date = $1 
                ORDER BY trip_id
            """, current_date)
            
            if existing_trips:
                print(f"📋 Found {len(existing_trips)} existing trips for today")
                for trip in existing_trips:
                    print(f"   Trip {trip['trip_id']}: {trip['display_name']} - {trip['live_status']}")
                return
            
            print("📝 Creating test trips...")
            
            # Get a route to use
            route = await conn.fetchrow("SELECT route_id FROM routes LIMIT 1")
            if not route:
                print("❌ No routes found - please create routes first")
                return
            
            route_id = route['route_id']
            
            # Create test trips with different times
            test_trips = [
                {
                    "name": "Early Morning - 06:00",
                    "time": "06:00",
                    "status": "COMPLETED"  # Past time
                },
                {
                    "name": "Morning Rush - 08:30", 
                    "time": "08:30",
                    "status": "SCHEDULED"  # Will depend on current time
                },
                {
                    "name": "Evening - 18:00",
                    "time": "18:00", 
                    "status": "SCHEDULED"  # Future time
                }
            ]
            
            for trip_data in test_trips:
                await conn.execute("""
                    INSERT INTO daily_trips (route_id, display_name, trip_date, live_status)
                    VALUES ($1, $2, $3, $4)
                """, route_id, trip_data["name"], current_date, "SCHEDULED")
                
                print(f"   ✅ Created: {trip_data['name']}")
                
    except Exception as e:
        print(f"❌ Error creating test trips: {e}")

async def check_trip_statuses(current_date):
    """Check and display current trip statuses"""
    try:
        pool = await get_conn()
        async with pool.acquire() as conn:
            trips = await conn.fetch("""
                SELECT 
                    trip_id,
                    display_name,
                    live_status,
                    trip_date
                FROM daily_trips
                WHERE trip_date = $1
                ORDER BY trip_id
            """, current_date)
            
            if not trips:
                print("   📭 No trips found for today")
                return
            
            print(f"   📋 Found {len(trips)} trips:")
            for trip in trips:
                status_icon = {
                    'SCHEDULED': '📅',
                    'IN_PROGRESS': '🚛', 
                    'COMPLETED': '✅',
                    'CANCELLED': '❌'
                }.get(trip['live_status'], '❓')
                
                print(f"      {status_icon} Trip {trip['trip_id']}: {trip['display_name']} → {trip['live_status']}")
                
    except Exception as e:
        print(f"❌ Error checking trip statuses: {e}")

async def test_manual_override(current_date):
    """Test manual status override functionality"""
    try:
        from app.core.status_updater import manually_update_trip_status
        pool = await get_conn()
        async with pool.acquire() as conn:
            # Get a trip to test with
            trip = await conn.fetchrow("""
                SELECT trip_id, display_name, live_status 
                FROM daily_trips 
                WHERE trip_date = $1 
                LIMIT 1
            """, current_date)
            
            if not trip:
                print("   📭 No trips available for manual override test")
                return
            
            trip_id = trip['trip_id']
            old_status = trip['live_status']
            new_status = 'IN_PROGRESS' if old_status != 'IN_PROGRESS' else 'COMPLETED'
            
            print(f"   🔧 Testing manual override: Trip {trip_id}")
            print(f"      {trip['display_name']}")
            print(f"      {old_status} → {new_status}")
            
            # Test manual update
            result = await manually_update_trip_status(trip_id, new_status, user_id=999)
            
            if result['success']:
                print(f"   ✅ Manual override successful!")
                print(f"      Trip {trip_id}: {result['old_status']} → {result['new_status']}")
                
                # Revert back for cleanliness
                await manually_update_trip_status(trip_id, old_status, user_id=999)
                print(f"   🔄 Reverted back to: {old_status}")
            else:
                print(f"   ❌ Manual override failed")
                
    except Exception as e:
        print(f"❌ Error testing manual override: {e}")

if __name__ == "__main__":
    asyncio.run(test_status_updater())
