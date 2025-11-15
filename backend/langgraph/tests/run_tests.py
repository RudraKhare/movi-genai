"""
Test script for the LangGraph agent
Run this to test the agent locally without starting the full API
"""
import asyncio
import json
from langgraph.runtime import runtime


async def test_agent():
    """
    Test the agent with various sample queries.
    """
    
    print("=" * 70)
    print("MOVI LangGraph Agent Test Suite")
    print("=" * 70)
    
    test_cases = [
        {
            "name": "Remove vehicle (with bookings - should need confirmation)",
            "input": {
                "text": "Remove vehicle from Bulk - 00:01",
                "user_id": 1
            }
        },
        {
            "name": "Cancel trip",
            "input": {
                "text": "Cancel trip Bulk - 00:01",
                "user_id": 1
            }
        },
        {
            "name": "Assign vehicle",
            "input": {
                "text": "Assign vehicle to Bulk - 00:01",
                "user_id": 1
            }
        },
        {
            "name": "Unknown action",
            "input": {
                "text": "Do something random",
                "user_id": 1
            }
        },
        {
            "name": "Trip not found",
            "input": {
                "text": "Remove vehicle from NonExistentTrip",
                "user_id": 1
            }
        },
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'=' * 70}")
        print(f"Test {i}: {test['name']}")
        print(f"{'=' * 70}")
        print(f"Input: {test['input']['text']}")
        print()
        
        try:
            result = await runtime.run(test['input'])
            output = result.get('final_output', result)
            
            print(f"Status: {output.get('status', 'N/A')}")
            print(f"Action: {output.get('action', 'N/A')}")
            
            if output.get('trip_id'):
                print(f"Trip ID: {output['trip_id']}")
                print(f"Trip Label: {output.get('trip_label', 'N/A')}")
            
            print(f"Needs Confirmation: {output.get('needs_confirmation', False)}")
            print(f"Success: {output.get('success', False)}")
            print(f"\nMessage:\n{output.get('message', 'No message')}")
            
            if output.get('consequences'):
                print(f"\nConsequences:")
                cons = output['consequences']
                print(f"  - Booking Count: {cons.get('booking_count', 0)}")
                print(f"  - Booking %: {cons.get('booking_percentage', 0)}")
                print(f"  - Has Deployment: {cons.get('has_deployment', False)}")
            
            if output.get('error'):
                print(f"\n⚠️  Error: {output['error']}")
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'=' * 70}")
    print("Test suite completed")
    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    print("\n🧪 Starting agent tests...\n")
    asyncio.run(test_agent())
