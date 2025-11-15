import asyncio
from app.core.supabase_client import get_conn

async def check():
    pool = await get_conn()
    async with pool.acquire() as conn:
        trips_with_deployments = await conn.fetch("""
            SELECT 
                t.trip_id, 
                t.display_name,
                d.vehicle_id,
                d.driver_id,
                COUNT(b.booking_id) as booking_count,
                t.live_status
            FROM daily_trips t
            LEFT JOIN deployments d ON t.trip_id = d.trip_id
            LEFT JOIN bookings b ON t.trip_id = b.trip_id
            WHERE d.deployment_id IS NOT NULL
            GROUP BY t.trip_id, t.display_name, d.vehicle_id, d.driver_id, t.live_status
            ORDER BY COUNT(b.booking_id) DESC
        """)
        
        print("Trips with deployments:")
        for trip in trips_with_deployments:
            print(f"  {trip['trip_id']}: {trip['display_name']} - Vehicle:{trip['vehicle_id']}, Driver:{trip['driver_id']}, {trip['booking_count']} bookings ({trip['live_status']})")

asyncio.run(check())
