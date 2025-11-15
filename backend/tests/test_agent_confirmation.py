"""
DAY 8 COMPREHENSIVE TEST SUITE
Tests all aspects of the confirmation flow
"""
import pytest
import asyncio
import sys
sys.path.insert(0, '.')

from langgraph.runtime import runtime
from langgraph.nodes import check_consequences, get_confirmation
from langgraph.tools import (
    tool_get_trip_status,
    tool_get_bookings,
    tool_remove_vehicle,
    tool_cancel_trip,
)
from app.core.supabase_client import get_conn
import json


@pytest.mark.asyncio
async def test_risk_detection_high_bookings():
    """Test that high booking count triggers confirmation"""
    state = {
        "action": "remove_vehicle",
        "trip_id": 5,  # Path-3 - 07:30 has 8 bookings
        "trip_label": "Path-3 - 07:30"
    }
    
    result = await check_consequences(state)
    
    assert result["needs_confirmation"] == True
    assert result["consequences"]["booking_count"] > 0
    assert "warning" in result["message"].lower() or "⚠️" in result["message"]


@pytest.mark.asyncio
async def test_risk_detection_no_bookings():
    """Test that trips without bookings don't require confirmation"""
    # Find a trip without bookings first
    pool = await get_conn()
    async with pool.acquire() as conn:
        trip = await conn.fetchrow("""
            SELECT dt.trip_id, dt.display_name
            FROM daily_trips dt
            LEFT JOIN bookings b ON dt.trip_id = b.trip_id AND b.status != 'CANCELLED'
            WHERE dt.trip_id NOT IN (
                SELECT trip_id FROM bookings WHERE status != 'CANCELLED'
            )
            LIMIT 1
        """)
        
        if not trip:
            pytest.skip("No trips without bookings available for testing")
        
        state = {
            "action": "remove_vehicle",
            "trip_id": trip["trip_id"],
            "trip_label": trip["display_name"]
        }
        
        result = await check_consequences(state)
        
        # Should not need confirmation if no bookings
        # (unless deployed or in-transit, which we'd check separately)
        assert "consequences" in result
        assert result["consequences"]["booking_count"] == 0


@pytest.mark.asyncio
async def test_session_creation():
    """Test that agent_sessions row is created correctly"""
    state = {
        "action": "cancel_trip",
        "trip_id": 5,
        "trip_label": "Path-3 - 07:30",
        "user_id": 1,
        "consequences": {
            "booking_count": 8,
            "booking_percentage": 10
        },
        "needs_confirmation": True
    }
    
    result = await get_confirmation(state)
    
    assert result["session_id"] is not None
    assert result["status"] == "awaiting_confirmation"
    assert result["confirmation_required"] == True
    
    # Verify in database
    pool = await get_conn()
    async with pool.acquire() as conn:
        session = await conn.fetchrow("""
            SELECT session_id, status, pending_action
            FROM agent_sessions
            WHERE session_id = $1
        """, result["session_id"])
        
        assert session is not None
        assert session["status"] == "PENDING"
        
        pending_action = session["pending_action"]
        if isinstance(pending_action, str):
            pending_action = json.loads(pending_action)
        
        assert pending_action["action"] == "cancel_trip"
        assert pending_action["trip_id"] == 5
        
        # Clean up
        await conn.execute(
            "DELETE FROM agent_sessions WHERE session_id = $1",
            result["session_id"]
        )


@pytest.mark.asyncio
async def test_confirm_executes_action():
    """Test that confirming a session executes the action"""
    # Step 1: Create a session
    state = {
        "action": "remove_vehicle",
        "trip_id": 7,  # Use Bulk - 00:01
        "trip_label": "Bulk - 00:01",
        "user_id": 1,
        "consequences": {"booking_count": 0},
        "needs_confirmation": True
    }
    
    result = await get_confirmation(state)
    session_id = result["session_id"]
    
    assert session_id is not None
    
    # Step 2: Simulate confirmation
    pool = await get_conn()
    async with pool.acquire() as conn:
        # Retrieve pending action
        row = await conn.fetchrow("""
            SELECT pending_action, status
            FROM agent_sessions
            WHERE session_id = $1
        """, session_id)
        
        assert row is not None
        assert row["status"] == "PENDING"
        
        pending_action = row["pending_action"]
        if isinstance(pending_action, str):
            pending_action = json.loads(pending_action)
        
        # Execute the action
        exec_result = await tool_remove_vehicle(
            pending_action["trip_id"],
            pending_action["user_id"]
        )
        
        # Update session
        await conn.execute("""
            UPDATE agent_sessions
            SET status='DONE',
                user_response=$1,
                execution_result=$2,
                updated_at=now()
            WHERE session_id=$3
        """,
            json.dumps({"confirmed": True}),
            json.dumps(exec_result),
            session_id
        )
        
        # Verify session updated
        final_session = await conn.fetchrow("""
            SELECT status, execution_result
            FROM agent_sessions
            WHERE session_id = $1
        """, session_id)
        
        assert final_session["status"] == "DONE"
        
        exec_result_data = final_session["execution_result"]
        if isinstance(exec_result_data, str):
            exec_result_data = json.loads(exec_result_data)
        
        assert exec_result_data.get("ok") == True
        
        # Clean up
        await conn.execute(
            "DELETE FROM agent_sessions WHERE session_id = $1",
            session_id
        )


@pytest.mark.asyncio
async def test_cancel_aborts_cleanly():
    """Test that cancelling a session does NOT execute the action"""
    # Step 1: Create a session
    state = {
        "action": "cancel_trip",
        "trip_id": 5,
        "trip_label": "Path-3 - 07:30",
        "user_id": 1,
        "consequences": {"booking_count": 8},
        "needs_confirmation": True
    }
    
    result = await get_confirmation(state)
    session_id = result["session_id"]
    
    # Step 2: Cancel the session
    pool = await get_conn()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE agent_sessions
            SET status='CANCELLED',
                user_response=$1,
                updated_at=now()
            WHERE session_id=$2
        """,
            json.dumps({"confirmed": False}),
            session_id
        )
        
        # Verify session is cancelled
        session = await conn.fetchrow("""
            SELECT status, execution_result
            FROM agent_sessions
            WHERE session_id = $1
        """, session_id)
        
        assert session["status"] == "CANCELLED"
        assert session["execution_result"] is None  # No execution happened
        
        # Verify trip is still active (not cancelled)
        trip = await conn.fetchrow("""
            SELECT live_status
            FROM daily_trips
            WHERE trip_id = 5
        """)
        
        assert trip["live_status"] != "CANCELLED"
        
        # Clean up
        await conn.execute(
            "DELETE FROM agent_sessions WHERE session_id = $1",
            session_id
        )


@pytest.mark.asyncio
async def test_end_to_end_remove_vehicle_flow():
    """Test complete flow: message -> confirm -> execute"""
    # Step 1: Send message
    input_state = {
        "text": "Remove vehicle from Bulk - 00:01",
        "user_id": 1
    }
    
    result = await runtime.run(input_state)
    
    # Verify response structure
    assert result.get("action") == "remove_vehicle"
    assert result.get("trip_id") is not None
    assert result.get("needs_confirmation") in [True, False]
    
    # If confirmation needed, verify session created
    if result.get("needs_confirmation"):
        assert result.get("session_id") is not None
        
        # Verify session in DB
        pool = await get_conn()
        async with pool.acquire() as conn:
            session = await conn.fetchrow("""
                SELECT session_id, status
                FROM agent_sessions
                WHERE session_id = $1
            """, result["session_id"])
            
            assert session is not None
            assert session["status"] == "PENDING"
            
            # Clean up
            await conn.execute(
                "DELETE FROM agent_sessions WHERE session_id = $1",
                result["session_id"]
            )


@pytest.mark.asyncio
async def test_confirmation_response_format():
    """Test that agent returns properly formatted confirmation response"""
    input_state = {
        "text": "Cancel Path-3 - 07:30",
        "user_id": 1
    }
    
    result = await runtime.run(input_state)
    
    # Check for required fields
    assert "action" in result
    assert "trip_id" in result
    assert "needs_confirmation" in result
    assert "message" in result
    
    # If confirmation needed, check for session_id
    if result.get("needs_confirmation"):
        assert "session_id" in result
        assert result["session_id"] is not None
        assert isinstance(result["session_id"], str)
        
        # Clean up
        pool = await get_conn()
        async with pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM agent_sessions WHERE session_id = $1",
                result["session_id"]
            )


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
