import asyncio
from app.core.supabase_client import get_conn

async def check():
    pool = await get_conn()
    async with pool.acquire() as conn:
        cols = await conn.fetch("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'bookings'
        """)
        print('Bookings columns:', [c['column_name'] for c in cols])

asyncio.run(check())
