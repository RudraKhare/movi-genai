import asyncio
import sys
import os

# Clear cache
if 'langgraph.nodes.resolve_target' in sys.modules:
    del sys.modules['langgraph.nodes.resolve_target']

sys.path.insert(0, os.path.dirname(__file__))

from langgraph.nodes.resolve_target import resolve_target

async def test():
    # Simulate state after parse_intent_llm
    state = {
        "text": "cancel the 8am trip",
        "action": "cancel_trip",
        "target_time": "08:00",  # This is what LLM extracts
        "confidence": 0.85,
        "parsed_params": {}
    }
    
    print("Input state:")
    print(f"  action: {state['action']}")
    print(f"  target_time: {state['target_time']}")
    print(f"  confidence: {state['confidence']}")
    print()
    
    result = await resolve_target(state)
    
    print("Output state:")
    print(f"  status: {result.get('status')}")
    print(f"  trip_id: {result.get('trip_id')}")
    print(f"  trip_label: {result.get('trip_label')}")
    print(f"  needs_clarification: {result.get('needs_clarification')}")
    print(f"  clarify_options: {result.get('clarify_options')}")
    print(f"  error: {result.get('error')}")

asyncio.run(test())
