import asyncio
from app.core.supabase_client import get_conn

async def check_drivers():
    pool = await get_conn()
    async with pool.acquire() as conn:
        # Get all drivers with their status
        drivers = await conn.fetch("""
            SELECT driver_id, name, phone, status 
            FROM drivers 
            ORDER BY driver_id
        """)
        print("=== ALL DRIVERS ===")
        for d in drivers:
            print(f"  ID: {d['driver_id']}, Name: {d['name']}, Status: {d['status']}")
        
        print(f"\nTotal: {len(drivers)} drivers")
        
        # Count by status - case insensitive
        available = [d for d in drivers if d['status'].lower() == 'available']
        unavailable = [d for d in drivers if d['status'].lower() != 'available']
        print(f"Available: {len(available)}")
        print(f"Unavailable: {len(unavailable)}")

if __name__ == "__main__":
    asyncio.run(check_drivers())
