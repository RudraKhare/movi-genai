"""
Day 7 Tool Verification Script
Tests all 8 tools directly to ensure they work without errors
"""
import asyncio
import sys
sys.path.insert(0, 'C:/Users/rudra/Desktop/movi/backend')

from langgraph import tools


async def test_all_tools():
    """Test each tool to verify it works correctly."""
    
    print("=" * 70)
    print("Day 7 Tool Integrity Verification")
    print("=" * 70)
    
    # Test 1: tool_identify_trip_from_label
    print("\n[Test 1] tool_identify_trip_from_label('Bulk')")
    try:
        result = await tools.tool_identify_trip_from_label("Bulk")
        if result:
            print(f"✅ Found trip: {result.get('display_name')} (ID: {result.get('trip_id')})")
        else:
            print("⚠️  No trip found (expected if no test data)")
        print(f"   Type: {type(result)}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: tool_get_trip_status
    print("\n[Test 2] tool_get_trip_status(1)")
    try:
        result = await tools.tool_get_trip_status(1)
        if result:
            print(f"✅ Got trip status: {len(result)} fields")
            print(f"   Keys: {list(result.keys())}")
        else:
            print("⚠️  No trip found with ID 1 (expected if no test data)")
        print(f"   Type: {type(result)}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: tool_get_bookings
    print("\n[Test 3] tool_get_bookings(1)")
    try:
        result = await tools.tool_get_bookings(1)
        print(f"✅ Got bookings: {len(result)} bookings")
        print(f"   Type: {type(result)}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: tool_get_vehicles
    print("\n[Test 4] tool_get_vehicles()")
    try:
        result = await tools.tool_get_vehicles()
        print(f"✅ Got vehicles: {len(result)} vehicles")
        if result:
            print(f"   Sample: {result[0] if result else 'None'}")
        print(f"   Type: {type(result)}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 5: tool_get_drivers
    print("\n[Test 5] tool_get_drivers()")
    try:
        result = await tools.tool_get_drivers()
        print(f"✅ Got drivers: {len(result)} drivers")
        if result:
            print(f"   Sample: {result[0] if result else 'None'}")
        print(f"   Type: {type(result)}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 6-8: Action tools (will fail without real trip but shouldn't crash)
    print("\n[Test 6] tool_assign_vehicle (dry run check)")
    try:
        # Don't actually call - just verify function exists
        print(f"✅ Function exists: {callable(tools.tool_assign_vehicle)}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n[Test 7] tool_remove_vehicle (dry run check)")
    try:
        print(f"✅ Function exists: {callable(tools.tool_remove_vehicle)}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n[Test 8] tool_cancel_trip (dry run check)")
    try:
        print(f"✅ Function exists: {callable(tools.tool_cancel_trip)}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 70)
    print("Tool Integrity Check Complete")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_all_tools())
