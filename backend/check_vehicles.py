import asyncio
from app.core.supabase_client import get_conn

async def main():
    pool = await get_conn()
    async with pool.acquire() as conn:
        # Check routes
        routes = await conn.fetch('SELECT route_id, route_name FROM routes ORDER BY route_id LIMIT 10')
        print('\n=== ROUTES IN DATABASE ===')
        for r in routes:
            print(f"ID: {r['route_id']}, Name: {r['route_name']}")

if __name__ == "__main__":
    asyncio.run(main())
