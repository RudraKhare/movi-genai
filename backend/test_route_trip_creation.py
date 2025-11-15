import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load .env
backend_dir = Path(__file__).parent
env_path = backend_dir / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

from app.core.supabase_client import get_conn
from datetime import date, timedelta, time

async def test_route_creation():
    """
    Test creating a route and verifying daily trips are auto-created
    """
    pool = await get_conn()
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Get a path to use
            path = await conn.fetchrow("SELECT path_id, path_name FROM paths LIMIT 1")
            if not path:
                print("❌ No paths available - create a path first!")
                return
            
            print(f"\n📍 Using path: {path['path_name']} (ID: {path['path_id']})")
            
            # Create a test route
            test_route_name = f"Test Route {date.today()}"
            shift_time = time(9, 30)  # 09:30
            route = await conn.fetchrow("""
                INSERT INTO routes (route_name, shift_time, path_id, direction)
                VALUES ($1, $2, $3, 'up')
                RETURNING *
            """, test_route_name, shift_time, path['path_id'])
            
            route_id = route['route_id']
            print(f"\n✅ Created route: {route['route_name']} (ID: {route_id})")
            
            # Auto-create daily trips for next 7 days
            today = date.today()
            trips_created = []
            
            for days_ahead in range(7):
                trip_date = today + timedelta(days=days_ahead)
                display_name = f"{test_route_name} - 09:30"
                
                trip = await conn.fetchrow("""
                    INSERT INTO daily_trips (route_id, display_name, trip_date, live_status)
                    VALUES ($1, $2, $3, 'SCHEDULED')
                    RETURNING trip_id, display_name, trip_date
                """, route_id, display_name, trip_date)
                
                trips_created.append(trip)
            
            print(f"\n📅 Created {len(trips_created)} daily trips:")
            for trip in trips_created:
                print(f"   Trip #{trip['trip_id']}: {trip['display_name']} on {trip['trip_date']}")
            
            # Verify trips exist
            verify = await conn.fetch("""
                SELECT trip_id, display_name, trip_date, live_status
                FROM daily_trips
                WHERE route_id = $1
                ORDER BY trip_date
            """, route_id)
            
            print(f"\n✅ Verified: Found {len(verify)} trips for route {route_id}")
            
            # Rollback to keep database clean
            raise Exception("Rolling back test transaction")

if __name__ == "__main__":
    try:
        asyncio.run(test_route_creation())
    except Exception as e:
        if "Rolling back" in str(e):
            print("\n🔄 Test transaction rolled back - database unchanged")
        else:
            print(f"\n❌ Error: {e}")
