import asyncio
import sys
sys.path.insert(0, 'C:/Users/rudra/Desktop/movi/backend')
from app.core.supabase_client import get_conn

async def test_search():
    pool = await get_conn()
    async with pool.acquire() as conn:
        # Test exact match
        text = "Bulk - 00:01"
        result = await conn.fetchrow("""
            SELECT trip_id, display_name
            FROM daily_trips 
            WHERE LOWER(display_name) = LOWER($1)
            LIMIT 1
        """, text.strip())
        print(f'\n1. Exact match for "{text}": {result}')
        
        # Test fuzzy match with full sentence
        text2 = "Remove vehicle from Bulk - 00:01"
        result2 = await conn.fetchrow("""
            SELECT trip_id, display_name
            FROM daily_trips 
            WHERE LOWER(display_name) LIKE LOWER($1)
            LIMIT 1
        """, f"%{text2.strip()}%")
        print(f'\n2. Fuzzy match for "{text2}": {result2}')
        
        # Test fuzzy match with just "Bulk"
        text3 = "Bulk"
        result3 = await conn.fetchrow("""
            SELECT trip_id, display_name
            FROM daily_trips 
            WHERE LOWER(display_name) LIKE LOWER($1)
            LIMIT 1
        """, f"%{text3.strip()}%")
        print(f'\n3. Fuzzy match for "{text3}": {result3}')

asyncio.run(test_search())
