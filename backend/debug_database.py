#!/usr/bin/env python3
"""
Debug the database structure
"""

import asyncio
import sys
import os

# Add backend to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(backend_dir)

async def debug_database():
    """Debug database structure and Trip 2 deployment"""
    try:
        from app.core.supabase_client import get_conn
        
        conn = await get_conn()
        try:
            print("🔍 DEBUGGING DATABASE STRUCTURE")
            print("="*60)
            
            # Check tables and columns
            print("\n📋 DEPLOYMENTS TABLE:")
            deployments = await conn.fetch("SELECT * FROM deployments WHERE trip_id = 2")
            for dep in deployments:
                print(f"   deployment_id: {dep['deployment_id']}, trip_id: {dep['trip_id']}")
                print(f"   columns: {list(dep.keys())}")
            
            print("\n📋 DAILY_TRIPS TABLE:")
            # Let's see what columns actually exist
            trips = await conn.fetch("SELECT * FROM daily_trips WHERE trip_id = 2 LIMIT 1")
            if trips:
                print(f"   Available columns: {list(trips[0].keys())}")
                print(f"   Sample row: {dict(trips[0])}")
            else:
                print("   No trips found for trip_id=2")
            
            print("\n📋 DEPLOYMENT+TRIP JOIN:")
            # This is the query I used in the service layer - let's see what it returns
            result = await conn.fetch("""
                SELECT d.deployment_id, dt.vehicle_id, dt.trip_id
                FROM deployments d 
                JOIN daily_trips dt ON d.trip_id = dt.trip_id 
                WHERE d.trip_id = 2
            """)
            
            for row in result:
                print(f"   deployment_id: {row['deployment_id']}, vehicle_id: {row['vehicle_id']}, trip_id: {row['trip_id']}")
            
            if not result:
                print("   ❌ JOIN QUERY RETURNED NOTHING!")
                print("   This means the deployment exists but JOIN failed")
                
                # Try individual queries
                print("\n🔍 INDIVIDUAL CHECKS:")
                deployments = await conn.fetch("SELECT * FROM deployments WHERE trip_id = 2")
                print(f"   Deployments: {deployments}")
                
                trips = await conn.fetch("SELECT * FROM daily_trips WHERE trip_id = 2") 
                print(f"   Trips: {trips}")
                
        finally:
            await conn.close()
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_database())
