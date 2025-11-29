#!/usr/bin/env python3
"""
Check trip status after assignment
"""

import asyncio
import sys
import os

# Add backend to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(backend_dir)

async def check_trip_status():
    """Check current status of Trip 2"""
    try:
        from app.core.supabase_client import get_conn
        
        conn = await get_conn()
        try:
            print("🔍 CURRENT TRIP 2 STATUS")
            print("="*60)
            
            # Check deployments
            deployments = await conn.fetch("SELECT * FROM deployments WHERE trip_id = 2")
            for dep in deployments:
                print(f"📋 Deployment {dep['deployment_id']}:")
                print(f"   trip_id: {dep['trip_id']}")
                print(f"   vehicle_id: {dep['vehicle_id']}")
                print(f"   driver_id: {dep['driver_id']}")
                print(f"   deployed_at: {dep['deployed_at']}")
                
        finally:
            await conn.close()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_trip_status())
