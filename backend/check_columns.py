import asyncio
from app.core.supabase_client import get_conn

async def check():
    pool = await get_conn()
    async with pool.acquire() as conn:
        # Get column names
        cols = await conn.fetch("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'daily_trips'
            ORDER BY ordinal_position
        """)
        
        print("Columns in daily_trips table:")
        for col in cols:
            print(f"  - {col['column_name']} ({col['data_type']})")
        
        # Also check a sample row
        sample = await conn.fetchrow("SELECT * FROM daily_trips LIMIT 1")
        if sample:
            print("\nSample row keys:")
            for key in sample.keys():
                print(f"  - {key}")

asyncio.run(check())
