import asyncio
from app.core.supabase_client import get_conn

async def check():
    pool = await get_conn()
    async with pool.acquire() as conn:
        trips_with_bookings = await conn.fetch("""
            SELECT 
                t.trip_id, 
                t.display_name,
                COUNT(b.booking_id) as booking_count,
                t.live_status
            FROM daily_trips t
            LEFT JOIN bookings b ON t.trip_id = b.trip_id
            GROUP BY t.trip_id, t.display_name, t.live_status
            HAVING COUNT(b.booking_id) > 0
            ORDER BY COUNT(b.booking_id) DESC
        """)
        
        print("Trips with bookings:")
        for trip in trips_with_bookings:
            print(f"  {trip['trip_id']}: {trip['display_name']} - {trip['booking_count']} bookings (Status: {trip['live_status']})")

asyncio.run(check())
