#!/usr/bin/env python3
"""Check trip 42 assignments"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.core.supabase_client import get_conn

async def main():
    pool = await get_conn()
    async with pool.acquire() as conn:
        # Check deployments table for trip 42
        row = await conn.fetchrow("""
            SELECT d.*, v.registration_number, dr.name as driver_name
            FROM deployments d
            LEFT JOIN vehicles v ON d.vehicle_id = v.vehicle_id
            LEFT JOIN drivers dr ON d.driver_id = dr.driver_id
            WHERE d.trip_id = 42
        """)
        if row:
            print(f"\nDeployment for Trip 42:")
            print(f"  Vehicle ID: {row['vehicle_id']}")
            print(f"  Vehicle Reg: {row['registration_number']}")
            print(f"  Driver ID: {row['driver_id']}")
            print(f"  Driver Name: {row['driver_name']}")
        else:
            print("\nNo deployment found for trip 42")

if __name__ == "__main__":
    asyncio.run(main())
