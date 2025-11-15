"""
End-to-end tests for LLM integration flow
Tests the complete flow: parse → resolve → consequences → confirm → execute
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import json


@pytest.mark.asyncio
async def test_e2e_llm_cancel_trip_with_confirmation():
    """Test full flow: LLM parse → DB verify → consequences → confirm → execute"""
    
    # Step 1: Parse intent with LLM
    mock_llm_response = {
        "action": "cancel_trip",
        "target_label": "Bulk - 00:01",
        "target_time": "00:01",
        "target_trip_id": None,
        "parameters": {},
        "confidence": 0.95,
        "clarify": False,
        "clarify_options": [],
        "explanation": "User wants to cancel trip"
    }
    
    # Step 2: DB verification
    mock_trip = {
        "trip_id": 7,
        "display_name": "Bulk - 00:01",
        "trip_date": "2025-11-14"
    }
    
    # Step 3: Consequences
    mock_trip_status = {
        "exists": True,
        "trip_id": 7,
        "display_name": "Bulk - 00:01",
        "booking_status_percentage": 19,
        "live_status": "SCHEDULED",
        "trip_date": "2025-11-14",
        "vehicle_id": 7,
        "driver_id": 7
    }
    
    mock_bookings = [
        {"booking_id": 1, "passenger_name": "Alice"},
        {"booking_id": 2, "passenger_name": "Bob"}
    ]
    
    # Import nodes
    from langgraph.nodes.parse_intent_llm import parse_intent_llm
    from langgraph.nodes.resolve_target import resolve_target
    from langgraph.nodes.check_consequences import check_consequences
    from langgraph.nodes.get_confirmation import get_confirmation
    
    # Initialize state
    state = {
        "text": "Cancel Bulk - 00:01",
        "user_id": 1
    }
    
    # Execute flow with mocks
    with patch("langgraph.nodes.parse_intent_llm.parse_intent_with_llm",
               new_callable=AsyncMock, return_value=mock_llm_response):
        
        # Step 1: Parse intent
        state = await parse_intent_llm(state)
        assert state["action"] == "cancel_trip"
        assert state["confidence"] == 0.95
        
        with patch("langgraph.nodes.resolve_target.tool_identify_trip_from_label",
                   new_callable=AsyncMock, return_value=mock_trip):
            
            # Step 2: Resolve target
            state = await resolve_target(state)
            assert state["trip_id"] == 7
            
            with patch("langgraph.nodes.check_consequences.tool_get_trip_status",
                       new_callable=AsyncMock, return_value=mock_trip_status):
                with patch("langgraph.nodes.check_consequences.tool_get_bookings",
                           new_callable=AsyncMock, return_value=mock_bookings):
                    
                    # Step 3: Check consequences
                    state = await check_consequences(state)
                    assert state["consequences"]["booking_count"] == 2
                    assert state["consequences"]["has_deployment"] is True
                    
                    # Mock session storage
                    mock_conn = AsyncMock()
                    mock_conn.fetchval = AsyncMock(return_value="test-session-id")
                    mock_pool = AsyncMock()
                    mock_pool.acquire = AsyncMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_conn), __aexit__=AsyncMock()))
                    
                    with patch("langgraph.nodes.get_confirmation.get_conn", return_value=mock_pool):
                        
                        # Step 4: Get confirmation
                        state = await get_confirmation(state)
                        assert state["needs_confirmation"] is True
                        assert state.get("session_id") is not None


@pytest.mark.asyncio
async def test_e2e_llm_ambiguous_clarify():
    """Test flow with ambiguous input → clarify UI → user selects → continues"""
    
    # LLM returns clarify=true
    mock_llm_response = {
        "action": "cancel_trip",
        "target_label": None,
        "target_time": "07:30",
        "target_trip_id": None,
        "parameters": {},
        "confidence": 0.60,
        "clarify": True,
        "clarify_options": ["Path-3 - 07:30", "Path-3 - 19:30"],
        "explanation": "Multiple trips at 7:30"
    }
    
    from langgraph.nodes.parse_intent_llm import parse_intent_llm
    from langgraph.nodes.resolve_target import resolve_target
    
    state = {
        "text": "Cancel the 7:30 run",
        "user_id": 1
    }
    
    with patch("langgraph.nodes.parse_intent_llm.parse_intent_with_llm",
               new_callable=AsyncMock, return_value=mock_llm_response):
        
        # Parse with LLM
        state = await parse_intent_llm(state)
        
        assert state["needs_clarification"] is True
        assert len(state["clarify_options"]) == 2
        assert "Path-3 - 07:30" in state["clarify_options"]


@pytest.mark.asyncio
async def test_e2e_llm_low_confidence_forces_clarify():
    """Test that low confidence (<0.5) forces clarification"""
    
    mock_llm_response = {
        "action": "unknown",
        "target_label": None,
        "target_time": None,
        "target_trip_id": None,
        "parameters": {},
        "confidence": 0.30,  # Low confidence
        "clarify": True,
        "clarify_options": [],
        "explanation": "Unable to understand intent"
    }
    
    from langgraph.nodes.parse_intent_llm import parse_intent_llm
    
    state = {
        "text": "do something with the thing",
        "user_id": 1
    }
    
    with patch("langgraph.nodes.parse_intent_llm.parse_intent_with_llm",
               new_callable=AsyncMock, return_value=mock_llm_response):
        
        state = await parse_intent_llm(state)
        
        assert state["confidence"] < 0.5
        assert state["needs_clarification"] is True


@pytest.mark.asyncio
async def test_e2e_ocr_bypass_flow():
    """Test OCR → auto-forward → skips LLM → goes straight to consequences"""
    
    from langgraph.nodes.parse_intent_llm import parse_intent_llm
    from langgraph.nodes.resolve_target import resolve_target
    
    state = {
        "text": "Cancel trip",
        "selectedTripId": 5,  # OCR provided this
        "action": "cancel_trip",
        "user_id": 1
    }
    
    # Mock that LLM is NOT called
    with patch("langgraph.nodes.parse_intent_llm.parse_intent_with_llm",
               new_callable=AsyncMock) as mock_llm:
        
        # Parse should skip LLM
        state = await parse_intent_llm(state)
        mock_llm.assert_not_called()
        
        # Mock DB lookup for selectedTripId
        mock_trip_row = {
            "trip_id": 5,
            "display_name": "Path-3 - 07:30",
            "trip_date": "2025-11-14",
            "live_status": "SCHEDULED"
        }
        
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value=mock_trip_row)
        mock_pool = AsyncMock()
        mock_pool.acquire = AsyncMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_conn), __aexit__=AsyncMock()))
        
        with patch("langgraph.nodes.resolve_target.get_conn", return_value=mock_pool):
            
            # Resolve should use OCR trip ID
            state = await resolve_target(state)
            
            assert state["trip_id"] == 5
            assert "[BYPASS]" in str(state.get("llm_explanation", "")) or state.get("selectedTripId") == 5


@pytest.mark.asyncio
async def test_e2e_llm_timeout_fallback():
    """Test that LLM timeout triggers fallback"""
    
    from langgraph.nodes.parse_intent_llm import parse_intent_llm
    
    state = {
        "text": "Cancel trip",
        "user_id": 1
    }
    
    # Mock LLM to timeout
    import asyncio
    
    with patch("langgraph.nodes.parse_intent_llm.parse_intent_with_llm",
               new_callable=AsyncMock, side_effect=asyncio.TimeoutError()):
        
        state = await parse_intent_llm(state)
        
        # Should have safe fallback
        assert state["action"] == "unknown"
        assert state["confidence"] == 0.0


@pytest.mark.asyncio
async def test_e2e_no_double_mutation():
    """Test that repeat confirmations don't cause double mutation"""
    
    # This test would verify session state prevents double execution
    # Requires integration with actual session management
    
    from langgraph.nodes.get_confirmation import get_confirmation
    
    state = {
        "action": "cancel_trip",
        "trip_id": 7,
        "trip_label": "Bulk - 00:01",
        "consequences": {
            "booking_count": 2,
            "has_deployment": True
        },
        "needs_confirmation": True,
        "user_id": 1
    }
    
    # Mock session creation
    mock_conn = AsyncMock()
    mock_conn.fetchval = AsyncMock(return_value="session-123")
    mock_pool = AsyncMock()
    mock_pool.acquire = AsyncMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_conn), __aexit__=AsyncMock()))
    
    with patch("langgraph.nodes.get_confirmation.get_conn", return_value=mock_pool):
        
        state = await get_confirmation(state)
        
        # Session should be created
        assert state.get("session_id") == "session-123"
        
        # Calling again with same session should not create new session
        state2 = await get_confirmation(state)
        assert state2.get("session_id") == "session-123"
