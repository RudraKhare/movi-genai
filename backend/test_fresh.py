"""Test with fresh module imports"""
import asyncio
import sys
sys.path.insert(0, 'C:/Users/rudra/Desktop/movi/backend')

# Clear any cached modules
for mod in list(sys.modules.keys()):
    if mod.startswith('langgraph'):
        del sys.modules[mod]

# Now import fresh
from langgraph.runtime import runtime

async def test():
    result = await runtime.run({
        "text": "cancel the Bulk - 00:01 trip",
        "currentPage": "busDashboard",
        "user_id": 1
    })
    
    print(f"\n✅ Action: {result.get('action')}")
    print(f"✅ Trip ID: {result.get('trip_id')}")
    print(f"✅ Trip Label: {result.get('trip_label')}")
    print(f"✅ Target Label from LLM: {result.get('target_label')}")
    print(f"✅ Error: {result.get('error')}")

asyncio.run(test())
