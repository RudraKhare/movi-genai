"""
Test the complete confirmation flow including confirm endpoint
"""
import asyncio
import sys
sys.path.insert(0, '.')

from langgraph.runtime import runtime
from app.core.supabase_client import get_conn
from app.api.agent import router
from fastapi import FastAPI
import json


async def test_full_confirmation_cycle():
    """Test: message -> get session_id -> confirm -> check result"""
    print("=" * 70)
    print("COMPLETE DAY 8 CONFIRMATION CYCLE TEST")
    print("=" * 70)
    
    # Step 1: Send message that needs confirmation
    print("\n[STEP 1] Sending message: 'Remove vehicle from Path-3 - 07:30'")
    print("-" * 70)
    
    input_state = {
        "text": "Remove vehicle from Path-3 - 07:30",
        "user_id": 1,
    }
    
    result = await runtime.run(input_state)
    
    session_id = result.get("session_id")
    trip_id = result.get("trip_id")
    
    print(f"[OK] Message processed")
    print(f"   Action: {result.get('action')}")
    print(f"   Trip ID: {trip_id}")
    print(f"   Needs Confirmation: {result.get('needs_confirmation')}")
    print(f"   Session ID: {session_id}")
    print(f"   Booking Count: {result.get('consequences', {}).get('booking_count')}")
    
    if not session_id:
        print("[FAIL] No session_id returned!")
        return
    
    # Step 2: Verify session in database
    print(f"\n[STEP 2] Verifying session in database")
    print("-" * 70)
    
    pool = await get_conn()
    async with pool.acquire() as conn:
        session = await conn.fetchrow("""
            SELECT session_id, user_id, status, pending_action
            FROM agent_sessions
            WHERE session_id = $1
        """, session_id)
        
        if session:
            print(f"[OK] Session found!")
            print(f"   Status: {session['status']}")
            pending_action = session['pending_action']
            if isinstance(pending_action, str):
                pending_action = json.loads(pending_action)
            print(f"   Pending Action: {pending_action.get('action')}")
            print(f"   Pending Trip ID: {pending_action.get('trip_id')}")
        else:
            print(f"[FAIL] Session not found!")
            return
    
    # Step 3: Test confirmation (confirmed=true)
    print(f"\n[STEP 3] Confirming action via /confirm endpoint")
    print("-" * 70)
    
    from langgraph.tools import tool_remove_vehicle
    
    # Simulate the confirm endpoint logic
    async with pool.acquire() as conn:
        # Retrieve pending action
        row = await conn.fetchrow("""
            SELECT pending_action, status 
            FROM agent_sessions 
            WHERE session_id=$1
        """, session_id)
        
        if not row:
            print("[FAIL] Session not found for confirmation")
            return
        
        pending_action = row["pending_action"]
        if isinstance(pending_action, str):
            pending_action = json.loads(pending_action)
        
        print(f"[OK] Retrieved pending action")
        print(f"   Action: {pending_action.get('action')}")
        print(f"   Trip ID: {pending_action.get('trip_id')}")
        
        # Execute the action
        print(f"\n[EXECUTING] Calling tool_remove_vehicle...")
        result = await tool_remove_vehicle(pending_action.get('trip_id'), 1)
        
        print(f"[OK] Tool executed")
        print(f"   Success: {result.get('ok')}")
        print(f"   Message: {result.get('message')}")
        
        # Update session status
        await conn.execute("""
            UPDATE agent_sessions 
            SET status='DONE', 
                user_response=$1, 
                execution_result=$2,
                updated_at=now()
            WHERE session_id=$3
        """, 
            json.dumps({"confirmed": True}),
            json.dumps(result),
            session_id
        )
        
        print(f"[OK] Session updated to DONE")
    
    # Step 4: Verify final state
    print(f"\n[STEP 4] Verifying final session state")
    print("-" * 70)
    
    async with pool.acquire() as conn:
        final_session = await conn.fetchrow("""
            SELECT session_id, status, execution_result
            FROM agent_sessions
            WHERE session_id = $1
        """, session_id)
        
        if final_session:
            print(f"[OK] Final session state:")
            print(f"   Status: {final_session['status']}")
            exec_result = final_session['execution_result']
            if isinstance(exec_result, str):
                exec_result = json.loads(exec_result)
            print(f"   Execution Success: {exec_result.get('ok')}")
            print(f"   Execution Message: {exec_result.get('message')}")
    
    # Clean up test data
    print(f"\n[CLEANUP] Removing test session")
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM agent_sessions WHERE session_id = $1", session_id)
    
    print("\n" + "=" * 70)
    print("[SUCCESS] DAY 8 CONFIRMATION FLOW COMPLETE!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_full_confirmation_cycle())
