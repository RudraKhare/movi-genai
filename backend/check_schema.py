import asyncio
import sys
sys.path.insert(0, 'C:/Users/rudra/Desktop/movi/backend')
from app.core.supabase_client import get_conn

async def check_schema():
    pool = await get_conn()
    async with pool.acquire() as conn:
        # Check columns in daily_trips
        columns = await conn.fetch("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'daily_trips'
            ORDER BY ordinal_position
        """)
        
        print('\n=== daily_trips columns ===')
        for col in columns:
            print(f'{col["column_name"]}: {col["data_type"]}')
        
        # Check vehicles columns
        columns = await conn.fetch("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'vehicles'
            ORDER BY ordinal_position
        """)
        
        print('\n=== vehicles columns ===')
        for col in columns:
            print(f'{col["column_name"]}: {col["data_type"]}')
        
        # Check drivers columns
        drivers = await conn.fetch("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'drivers'
            ORDER BY ordinal_position
        """)
        
        print('\n=== drivers columns ===')
        for col in drivers:
            print(f'{col["column_name"]}: {col["data_type"]}')
        
        # Check if routes table exists
        routes = await conn.fetch("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'routes'
            ORDER BY ordinal_position
        """)
        
        print('\n=== routes columns ===')
        for col in routes:
            print(f'{col["column_name"]}: {col["data_type"]}')
        
        # Check sample data
        print('\n=== Sample trip data ===')
        sample = await conn.fetchrow("""
            SELECT * FROM daily_trips LIMIT 1
        """)
        if sample:
            print('Columns in result:', list(sample.keys()))

asyncio.run(check_schema())
