"""Direct test of tool_identify_trip_from_label"""
import asyncio
import sys
sys.path.insert(0, 'C:/Users/rudra/Desktop/movi/backend')

from langgraph.tools import tool_identify_trip_from_label

async def test():
    print("Testing trip matching...")
    
    tests = [
        "Bulk - 00:01",
        "bulk - 00:01",
        "Bulk-00:01",
        "BULK - 00:01",
        "bulk  -  00:01",
    ]
    
    for test_str in tests:
        result = await tool_identify_trip_from_label(test_str)
        status = "✅" if result else "❌"
        print(f"{status} '{test_str}' → {result}")

asyncio.run(test())
