"""
Script to add a test vehicle to the database
"""
import asyncio
from app.core.db import get_conn


async def add_test_vehicle():
    pool = await get_conn()
    async with pool.acquire() as conn:
        # Check if test vehicle already exists
        existing = await conn.fetchrow('''
            SELECT vehicle_id FROM vehicles WHERE registration_number = 'TEST-VEHICLE-01'     
        ''')

        if existing:
            print(f'✅ Test vehicle already exists with ID: {existing["vehicle_id"]}')
        else:
            # Add test vehicle
            result = await conn.fetchrow('''
                INSERT INTO vehicles (registration_number, vehicle_type, capacity, status)
                VALUES ('TEST-VEHICLE-01', 'Bus', 40, 'available')
                RETURNING vehicle_id, registration_number, capacity
            ''')
            print(f'✅ Created test vehicle: {dict(result)}')

        # Check unassigned vehicles
        vehicles = await conn.fetch('''
            SELECT DISTINCT
                v.vehicle_id,
                v.registration_number,
                v.capacity,
                v.status
            FROM vehicles v
            LEFT JOIN deployments d ON v.vehicle_id = d.vehicle_id
            WHERE v.status = 'available'
                AND (
                    d.deployment_id IS NULL
                    OR NOT EXISTS (
                        SELECT 1
                        FROM deployments d2
                        JOIN daily_trips t2 ON d2.trip_id = t2.trip_id
                        WHERE d2.vehicle_id = v.vehicle_id
                            AND t2.live_status IN ('SCHEDULED', 'IN_PROGRESS')
                    )
                )
            ORDER BY v.registration_number
        ''')

        print(f'\n📋 Available vehicles: {len(vehicles)}')
        for v in vehicles:
            print(f'  - {v["registration_number"]} ({v["capacity"]} seats) - ID: {v["vehicle_id"]}')


if __name__ == '__main__':
    asyncio.run(add_test_vehicle())
