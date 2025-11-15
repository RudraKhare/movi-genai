import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from langgraph.tools.llm_client import parse_intent_with_llm

async def test():
    text = "cancel the 8am trip"
    print(f"Testing: '{text}'")
    result = await parse_intent_with_llm(text, context={"currentPage": "busDashboard"})
    print(f"\nLLM Response:")
    print(f"  action: {result.get('action')}")
    print(f"  target_label: {result.get('target_label')}")
    print(f"  target_time: {result.get('target_time')}")
    print(f"  target_trip_id: {result.get('target_trip_id')}")
    print(f"  confidence: {result.get('confidence')}")
    print(f"\nFull response: {result}")

asyncio.run(test())
