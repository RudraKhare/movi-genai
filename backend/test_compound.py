#!/usr/bin/env python3
"""Test compound command parsing"""
import asyncio
import sys
sys.path.insert(0, '.')

from langgraph.tools.llm_client import parse_intent_with_llm

async def main():
    text = "Assign vehicle 'MH-12-7777' and driver 'John Snow' to trip 42"
    context = {}
    
    print(f"\nTesting: {text}")
    print("=" * 60)
    
    result = await parse_intent_with_llm(text, context)
    
    print(f"Action: {result.get('action')}")
    print(f"Target Trip ID: {result.get('target_trip_id')}")
    print(f"Parameters: {result.get('parameters')}")
    print(f"Confidence: {result.get('confidence')}")
    print(f"Explanation: {result.get('explanation')}")

if __name__ == "__main__":
    asyncio.run(main())
