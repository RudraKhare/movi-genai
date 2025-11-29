#!/usr/bin/env python3
"""Full e2e test of compound command flow"""
import asyncio
import sys
sys.path.insert(0, '.')

# Test the entire graph flow
from langgraph.graph_def import graph

async def main():
    text = "Assign vehicle 'MH-12-7777' and driver 'John Snow' to trip 42"
    
    print(f"\nTesting FULL GRAPH FLOW: {text}")
    print("=" * 70)
    
    # Initial state
    state = {
        "text": text,  # The parse_intent_llm expects 'text' key
        "user_input": text,
        "session_id": "test-session-compound",
        "user_id": 1,
        "action": None,
        "trip_id": None,
        "message": None,
        "status": None,
        "context": {},
        "parsed_params": {}
    }
    
    # Run parse_intent
    print("\n1. PARSE INTENT:")
    from langgraph.nodes.parse_intent_llm import parse_intent_llm
    state = await parse_intent_llm(state)
    print(f"   action: {state.get('action')}")
    print(f"   target_trip_id: {state.get('target_trip_id')}")
    print(f"   parsed_params: {state.get('parsed_params')}")
    
    if state.get("action") != "assign_vehicle_and_driver":
        print("   ❌ FAILED - Wrong action detected")
        return
    
    # Run resolve_target
    print("\n2. RESOLVE TARGET:")
    from langgraph.nodes.resolve_target import resolve_target
    state = await resolve_target(state)
    print(f"   trip_id: {state.get('trip_id')}")
    print(f"   error: {state.get('error')}")
    
    if not state.get("trip_id"):
        print("   ❌ FAILED - Trip ID not resolved")
        return
        
    # Run decision_router
    print("\n3. DECISION ROUTER:")
    from langgraph.nodes.decision_router import decision_router
    state = await decision_router(state)
    print(f"   next_node: {state.get('next_node')}")
    
    if state.get("next_node") != "check_consequences":
        print(f"   ❌ FAILED - Wrong next_node (expected check_consequences)")
        return
    
    # Run check_consequences
    print("\n4. CHECK CONSEQUENCES:")
    from langgraph.nodes.check_consequences import check_consequences
    state = await check_consequences(state)
    print(f"   needs_confirmation: {state.get('needs_confirmation')}")
    
    # For safe actions, check_consequences just returns - we need to go to execute
    # Check the graph edges condition: if not needs_confirmation and not error → execute_action
    if not state.get("needs_confirmation") and not state.get("error"):
        print("   → Safe action, proceeding to execute_action")
        
        print("\n5. EXECUTE ACTION:")
        from langgraph.nodes.execute_action import execute_action
        state = await execute_action(state)
        print(f"   status: {state.get('status')}")
        print(f"   message: {state.get('message')}")
        print(f"   error: {state.get('error')}")
    elif state.get("needs_confirmation"):
        print("   → Needs confirmation, would go to get_confirmation")
    else:
        print(f"   → Error: {state.get('error')}")
    
    print("\n" + "=" * 70)
    print("FINAL STATE:")
    print(f"   action: {state.get('action')}")
    print(f"   trip_id: {state.get('trip_id')}")
    print(f"   status: {state.get('status')}")
    print(f"   message: {state.get('message')}")

if __name__ == "__main__":
    asyncio.run(main())
