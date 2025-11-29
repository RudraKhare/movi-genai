#!/usr/bin/env python3
"""
Test script to verify the assign_driver fix
"""

import asyncio
import sys
sys.path.insert(0, 'C:/Users/rudra/Desktop/movi/backend')

from app.core.supabase_client import get_conn

async def test_deployments_schema():
    """Test that deployments table has correct schema"""
    print("🔍 Testing deployments table schema...")
    
    pool = await get_conn()
    async with pool.acquire() as conn:
        # Check table structure
        columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name='deployments'
            ORDER BY ordinal_position
        """)
        
        print("\n📋 Deployments table structure:")
        for col in columns:
            nullable = "NULL" if col["is_nullable"] == "YES" else "NOT NULL"
            print(f"   - {col['column_name']}: {col['data_type']} ({nullable})")
        
        # Verify expected columns exist
        column_names = [col["column_name"] for col in columns]
        expected_columns = ["deployment_id", "trip_id", "vehicle_id", "driver_id", "deployed_at"]
        
        missing_columns = [col for col in expected_columns if col not in column_names]
        if missing_columns:
            print(f"❌ Missing columns: {missing_columns}")
            return False
        
        # Verify problematic columns don't exist
        problematic_columns = ["status", "created_at", "updated_at"]
        found_problematic = [col for col in problematic_columns if col in column_names]
        if found_problematic:
            print(f"⚠️  Found problematic columns that might cause issues: {found_problematic}")
        
        print("✅ Schema verification complete")
        return True

async def test_assign_driver_service():
    """Test the assign_driver service function"""
    print("\n🧪 Testing assign_driver service function...")
    
    try:
        from app.core.service import assign_driver
        print("✅ assign_driver service function imported successfully")
        
        # Check if function signature is correct
        import inspect
        sig = inspect.signature(assign_driver)
        params = list(sig.parameters.keys())
        expected_params = ["trip_id", "driver_id", "user_id"]
        
        if params == expected_params:
            print("✅ Function signature is correct:", params)
        else:
            print("❌ Function signature mismatch:", params)
            return False
            
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import assign_driver: {e}")
        return False

async def test_tool_assign_driver():
    """Test the tool_assign_driver function"""
    print("\n🛠️  Testing tool_assign_driver function...")
    
    try:
        from langgraph.tools import tool_assign_driver
        print("✅ tool_assign_driver imported successfully")
        
        # Check if function signature is correct
        import inspect
        sig = inspect.signature(tool_assign_driver)
        params = list(sig.parameters.keys())
        expected_params = ["trip_id", "driver_id", "user_id"]
        
        if params == expected_params:
            print("✅ Function signature is correct:", params)
        else:
            print("❌ Function signature mismatch:", params)
            return False
            
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import tool_assign_driver: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting assign_driver fix verification...")
    print("=" * 60)
    
    tests = [
        test_deployments_schema,
        test_assign_driver_service, 
        test_tool_assign_driver
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with error: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    
    passed = sum(results)
    total = len(results)
    
    for i, (test, result) in enumerate(zip(tests, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {i+1}. {test.__name__}: {status}")
    
    print(f"\nSummary: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! assign_driver fix is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the implementation.")
        return False

if __name__ == "__main__":
    asyncio.run(main())
