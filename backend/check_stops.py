"""Check available stops in database"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def main():
    # Get database URL and convert to asyncpg format
    db_url = os.getenv("DATABASE_URL")
    if "postgresql+asyncpg://" in db_url:
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    conn = await asyncpg.connect(db_url, ssl="require")
    
    print("\n=== Direction constraint check ===")
    constraint = await conn.fetch("""
        SELECT conname, pg_get_constraintdef(oid) as definition
        FROM pg_constraint 
        WHERE conname = 'routes_direction_check'
    """)
    for c in constraint:
        print(f"  {c['conname']}: {c['definition']}")
    
    print("\n=== Existing direction values in routes ===")
    rows = await conn.fetch("SELECT DISTINCT direction FROM routes WHERE direction IS NOT NULL")
    for row in rows:
        print(f"  '{row['direction']}'")
    
    print("\n=== Available Stops ===")
    rows = await conn.fetch("SELECT stop_id, name FROM stops ORDER BY name")
    for row in rows:
        print(f"  {row['stop_id']}: {row['name']}")
    
    print("\n=== Available Paths ===")
    rows = await conn.fetch("SELECT path_id, path_name FROM paths ORDER BY path_name")
    for row in rows:
        print(f"  {row['path_id']}: {row['path_name']}")
    
    print("\n=== Available Routes ===")
    rows = await conn.fetch("SELECT route_id, route_name, path_id FROM routes ORDER BY route_name")
    for row in rows:
        print(f"  {row['route_id']}: {row['route_name']} (path_id: {row['path_id']})")
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
