import asyncio
import sys
sys.path.insert(0, 'C:/Users/rudra/Desktop/movi/backend')
from app.core.supabase_client import get_conn

async def get_trips():
    pool = await get_conn()
    async with pool.acquire() as conn:
        rows = await conn.fetch('SELECT trip_id, display_name FROM daily_trips LIMIT 10')
        print('\nTrips in database:')
        for r in rows:
            print(f'{r["trip_id"]}: {r["display_name"]}')

asyncio.run(get_trips())
