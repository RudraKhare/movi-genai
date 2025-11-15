import asyncio
import asyncpg
import os

async def check_schema():
    db_url = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL")
    if not db_url:
        print("❌ DATABASE_URL or SUPABASE_DB_URL not set!")
        return
    
    conn = await asyncpg.connect(db_url)
    
    # Check routes table columns
    cols = await conn.fetch("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name='routes' 
        ORDER BY ordinal_position
    """)
    
    print("\n=== ROUTES TABLE COLUMNS ===")
    for col in cols:
        print(f"  {col['column_name']:30} {col['data_type']}")
    
    # Check if we have any routes
    routes = await conn.fetch("SELECT * FROM routes LIMIT 1")
    if routes:
        print("\n=== SAMPLE ROUTE DATA ===")
        print(dict(routes[0]))
    else:
        print("\n⚠️ No routes found in database")
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(check_schema())
