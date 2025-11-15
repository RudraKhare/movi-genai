"""
Debug: Check what state.get("target_label") returns
"""
import asyncio
import sys
sys.path.insert(0, 'C:/Users/rudra/Desktop/movi/backend')

from langgraph.runtime import runtime

async def test():
    test_input = {
        "text": "cancel the Bulk - 00:01 trip",
        "currentPage": "busDashboard",
        "user_id": 1
    }
    
    # Patch resolve_target to see state
    from langgraph.nodes import resolve_target
    original_func = resolve_target.resolve_target
    
    async def debug_resolve_target(state):
        print("\n🔍 DEBUG resolve_target - STATE:")
        print(f"   target_label: {state.get('target_label')}")
        print(f"   text: {state.get('text')}")
        print(f"   bool(target_label): {bool(state.get('target_label'))}")
        return await original_func(state)
    
    resolve_target.resolve_target = debug_resolve_target
    
    # Run
    result = await runtime.run(test_input)
    print(f"\n✅ Final target_label: {result.get('target_label')}")
    print(f"✅ Final trip_id: {result.get('trip_id')}")

asyncio.run(test())
