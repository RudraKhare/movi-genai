import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load .env
backend_dir = Path(__file__).parent
env_path = backend_dir / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

from app.core.supabase_client import get_conn

async def test():
    pool = await get_conn()
    async with pool.acquire() as conn:
        trip = await conn.fetchrow("""
            SELECT dt.trip_id, dt.display_name, v.capacity, d.vehicle_id, v.registration_number
            FROM daily_trips dt 
            LEFT JOIN deployments d ON d.trip_id = dt.trip_id 
            LEFT JOIN vehicles v ON d.vehicle_id = v.vehicle_id 
            WHERE dt.trip_id = 5
        """)
        
        print(f"\n🚌 Trip 5 Raw Data:")
        print(f"  trip_id: {trip['trip_id']}")
        print(f"  display_name: {trip['display_name']}")
        print(f"  vehicle_id: {trip['vehicle_id']}")
        print(f"  vehicle registration: {trip['registration_number']}")
        print(f"  capacity: {trip['capacity']}")
        print(f"  capacity type: {type(trip['capacity'])}")

if __name__ == "__main__":
    asyncio.run(test())
