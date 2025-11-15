"""
Test the complete Day 8 confirmation flow
"""
import asyncio
import sys
sys.path.insert(0, '.')

from langgraph.runtime import runtime


async def test_confirmation_flow():
    """Test the full flow from message to confirmation"""
    print("=" * 70)
    print("DAY 8 CONFIRMATION FLOW TEST")
    print("=" * 70)
    
    # Test 1: Action requiring confirmation
    print("\n[TEST 1] Remove vehicle from trip with bookings")
    print("-" * 70)
    
    input_state = {
        "text": "Remove vehicle from Path-3 - 07:30",
        "user_id": 1,
    }
    
    result = await runtime.run(input_state)
    
    print(f"\n[OK] Graph execution completed")
    print(f"   Status: {result.get('status')}")
    print(f"   Action: {result.get('action')}")
    print(f"   Trip ID: {result.get('trip_id')}")
    print(f"   Needs Confirmation: {result.get('needs_confirmation')}")
    print(f"   Session ID: {result.get('session_id')}")
    print(f"   Message: {result.get('message', '')[:200]}")
    
    if result.get("consequences"):
        cons = result["consequences"]
        print(f"\n   Consequences:")
        print(f"      Booking Count: {cons.get('booking_count')}")
        print(f"      Booking %: {cons.get('booking_percentage')}")
        print(f"      Has Deployment: {cons.get('has_deployment')}")
        print(f"      Live Status: {cons.get('live_status')}")
    
    # Check final_output
    if "final_output" in result:
        print(f"\n   Final Output Present: Yes")
        final = result["final_output"]
        print(f"      Final Session ID: {final.get('session_id')}")
        print(f"      Final Needs Confirmation: {final.get('needs_confirmation')}")
    
    # Check if session was created in DB
    if result.get("session_id"):
        print(f"\n[CHECKING] Looking for session in database...")
        from app.core.supabase_client import get_conn
        pool = await get_conn()
        async with pool.acquire() as conn:
            session = await conn.fetchrow("""
                SELECT session_id, status, pending_action
                FROM agent_sessions
                WHERE session_id = $1
            """, result["session_id"])
            
            if session:
                print(f"   [OK] Session found in database!")
                print(f"      Status: {session['status']}")
                print(f"      Action: {session['pending_action'].get('action') if isinstance(session['pending_action'], dict) else 'N/A'}")
            else:
                print(f"   [FAIL] Session NOT found in database!")
    else:
        print(f"\n[FAIL] No session_id returned - this is the bug!")
    
    print("\n" + "=" * 70)
    
    # Test 2: Safe action (no confirmation needed)
    print("\n[TEST 2] Action with no bookings (safe)")
    print("-" * 70)
    
    input_state2 = {
        "text": "Assign vehicle to Path-1 - 08:00",
        "user_id": 1,
    }
    
    result2 = await runtime.run(input_state2)
    
    print(f"\n[OK] Graph execution completed")
    print(f"   Status: {result2.get('status')}")
    print(f"   Action: {result2.get('action')}")
    print(f"   Trip ID: {result2.get('trip_id')}")
    print(f"   Needs Confirmation: {result2.get('needs_confirmation')}")
    print(f"   Message: {result2.get('message', '')[:200]}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(test_confirmation_flow())
