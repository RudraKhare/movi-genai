import asyncio
import sys
sys.path.insert(0, 'C:/Users/rudra/Desktop/movi/backend')
from app.core.supabase_client import get_conn

async def check_display_names():
    pool = await get_conn()
    async with pool.acquire() as conn:
        # Check if display_name is populated
        trips = await conn.fetch("""
            SELECT trip_id, route_id, display_name 
            FROM daily_trips 
            LIMIT 10
        """)
        
        print('\n=== Trip display_name values ===')
        for trip in trips:
            print(f'ID {trip["trip_id"]}: route_id={trip["route_id"]}, display_name="{trip["display_name"]}"')
        
        # Check routes
        print('\n=== Route names ===')
        routes = await conn.fetch("""
            SELECT route_id, route_name, shift_time 
            FROM routes 
            LIMIT 10
        """)
        for route in routes:
            print(f'Route {route["route_id"]}: {route["route_name"]} @ {route["shift_time"]}')

asyncio.run(check_display_names())
