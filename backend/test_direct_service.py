#!/usr/bin/env python3
"""
Direct service test to see exact error
"""

import asyncio
import sys
import os

# Add backend to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(backend_dir)

async def test_direct_service():
    """Test service layer directly"""
    try:
        from app.core import service
        
        print("🔍 TESTING DIRECT SERVICE CALL")
        print("="*60)
        
        result = await service.assign_vehicle(
            trip_id=2,
            vehicle_id=2, 
            driver_id=2,
            user_id=999
        )
        
        print(f"✅ SUCCESS: {result}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_direct_service())
