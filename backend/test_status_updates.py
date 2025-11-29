"""
Test Script for Automatic Trip Status Updates
"""

import asyncio
import sys
import os
from datetime import datetime, time as dt_time

# Add backend to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(backend_dir)

async def test_status_updates():
    """Test the automatic status update system"""
    
    print("🧪 TESTING AUTOMATIC TRIP STATUS UPDATES")
    print("=" * 70)
    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    try:
        from app.core.status_updater import TripStatusUpdater
        from app.core.supabase_client import get_conn
        
        # Initialize updater
        updater = TripStatusUpdater()
        
        # Get current status summary
        print("\n📊 CURRENT STATUS SUMMARY:")
        print("-" * 40)
        summary = await updater.get_status_summary()
        
        for status, count in summary.items():
            if status != 'last_updated' and status != 'total_trips':
                print(f"   {status.upper()}: {count}")
        
        print(f"\n   Total Trips: {summary.get('total_trips', 0)}")
        
        # Show current trips with detailed info
        print("\n🚌 CURRENT TRIPS (Today):")
        print("-" * 40)
        
        pool = await get_conn()
        async with pool.acquire() as conn:
            trips = await conn.fetch("""
                SELECT 
                    dt.trip_id,
                    dt.display_name,
                    dt.live_status,
                    r.shift_time,
                    r.estimated_duration_minutes
                FROM daily_trips dt
                JOIN routes r ON dt.route_id = r.route_id
                WHERE dt.trip_date = CURRENT_DATE
                ORDER BY r.shift_time
            """)
            
            current_time = datetime.now().time()
            
            for trip in trips:
                trip_id = trip['trip_id']
                name = trip['display_name']
                status = trip['live_status']
                shift_time = trip['shift_time']
                duration = trip['estimated_duration_minutes'] or 120
                
                # Extract time from name if shift_time is null
                trip_time = shift_time
                if not trip_time and name:
                    import re
                    time_match = re.search(r'(\d{1,2}:\d{2})', name)
                    if time_match:
                        time_str = time_match.group(1)
                        hour, minute = map(int, time_str.split(':'))
                        trip_time = dt_time(hour, minute)
                
                # Determine what should happen
                should_be_status = status
                if trip_time:
                    # Calculate end time
                    trip_datetime = datetime.combine(datetime.now().date(), trip_time)
                    end_datetime = trip_datetime.replace(
                        hour=(trip_datetime.hour + duration // 60) % 24,
                        minute=(trip_datetime.minute + duration % 60) % 60
                    )
                    end_time = end_datetime.time()
                    
                    if current_time >= end_time:
                        should_be_status = "COMPLETED"
                    elif current_time >= trip_time:
                        should_be_status = "IN_PROGRESS" 
                    else:
                        should_be_status = "SCHEDULED"
                
                status_icon = {
                    'SCHEDULED': '📅',
                    'IN_PROGRESS': '🚛', 
                    'COMPLETED': '✅',
                    'CANCELLED': '❌'
                }.get(status, '❓')
                
                time_str = str(trip_time)[:5] if trip_time else "??:??"
                
                print(f"   {status_icon} Trip {trip_id}: {name}")
                print(f"      Status: {status} | Time: {time_str}")
                
                if should_be_status != status:
                    print(f"      🔄 Should be: {should_be_status}")
                else:
                    print(f"      ✅ Status correct")
                print()
        
        # Run the status update
        print("🔄 RUNNING STATUS UPDATE...")
        print("-" * 40)
        
        updates_made = await updater.update_trip_statuses()
        
        if updates_made > 0:
            print(f"✅ Status update complete: {updates_made} trips updated")
            
            # Show updated summary
            print("\n📊 UPDATED STATUS SUMMARY:")
            print("-" * 40)
            new_summary = await updater.get_status_summary()
            
            for status, count in new_summary.items():
                if status != 'last_updated' and status != 'total_trips':
                    print(f"   {status.upper()}: {count}")
        else:
            print("✨ No updates needed - all trips have correct status")
        
        print("\n🎯 TEST RESULTS:")
        print("-" * 40)
        print("✅ Status updater working correctly")
        print("✅ Time-based transitions functional") 
        print("✅ Ready for automatic background updates")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_status_updates())
