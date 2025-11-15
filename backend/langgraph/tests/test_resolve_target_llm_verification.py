"""
Unit tests for LLM Trip ID Verification in resolve_target node
Tests DB verification of LLM-suggested trip IDs
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from langgraph.nodes.resolve_target import resolve_target


@pytest.mark.asyncio
async def test_resolve_verifies_llm_trip_id_valid():
    """Test that valid LLM-suggested trip_id is verified and accepted"""
    
    state = {
        "action": "cancel_trip",
        "text": "Cancel trip",
        "parsed_params": {
            "target_trip_id": 7
        },
        "user_id": 1
    }
    
    # Mock database response - trip exists
    mock_trip_row = {
        "trip_id": 7,
        "display_name": "Bulk - 00:01",
        "trip_date": "2025-11-14",
        "live_status": "SCHEDULED"
    }
    
    # Mock the database connection
    mock_conn = AsyncMock()
    mock_conn.fetchrow = AsyncMock(return_value=mock_trip_row)
    mock_pool = AsyncMock()
    mock_pool.acquire = AsyncMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_conn), __aexit__=AsyncMock()))
    
    with patch("langgraph.nodes.resolve_target.get_conn", return_value=mock_pool):
        result = await resolve_target(state)
        
        # Assertions
        assert result["trip_id"] == 7
        assert result["trip_label"] == "Bulk - 00:01"
        assert "error" not in result


@pytest.mark.asyncio
async def test_resolve_rejects_hallucinated_trip_id():
    """Test that invalid LLM-suggested trip_id is rejected"""
    
    state = {
        "action": "cancel_trip",
        "text": "Cancel trip 999",
        "target_label": "Nonexistent Trip",
        "parsed_params": {
            "target_trip_id": 999  # Does not exist
        },
        "user_id": 1
    }
    
    # Mock database response - trip does NOT exist
    mock_conn = AsyncMock()
    mock_conn.fetchrow = AsyncMock(return_value=None)  # No trip found
    mock_pool = AsyncMock()
    mock_pool.acquire = AsyncMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_conn), __aexit__=AsyncMock()))
    
    # Mock tool_identify_trip_from_label to also return nothing
    with patch("langgraph.nodes.resolve_target.get_conn", return_value=mock_pool):
        with patch("langgraph.nodes.resolve_target.tool_identify_trip_from_label", 
                   new_callable=AsyncMock, return_value=None):
            
            result = await resolve_target(state)
            
            # Should fall back to clarification
            assert result.get("needs_clarification") is True
            assert "trip_id" not in result or result.get("trip_id") is None


@pytest.mark.asyncio
async def test_resolve_target_label_single_match():
    """Test label-based search with single match"""
    
    state = {
        "action": "cancel_trip",
        "text": "Cancel Bulk - 00:01",
        "target_label": "Bulk - 00:01",
        "parsed_params": {},
        "user_id": 1
    }
    
    # Mock tool response - single match
    mock_trip = {
        "trip_id": 7,
        "display_name": "Bulk - 00:01",
        "trip_date": "2025-11-14"
    }
    
    with patch("langgraph.nodes.resolve_target.tool_identify_trip_from_label",
               new_callable=AsyncMock, return_value=mock_trip):
        
        result = await resolve_target(state)
        
        assert result["trip_id"] == 7
        assert result["trip_label"] == "Bulk - 00:01"


@pytest.mark.asyncio
async def test_resolve_target_label_no_match():
    """Test label-based search with no matches"""
    
    state = {
        "action": "cancel_trip",
        "text": "Cancel XYZ trip",
        "target_label": "XYZ",
        "parsed_params": {},
        "confidence": 0.50,
        "user_id": 1
    }
    
    # Mock tool response - no match
    with patch("langgraph.nodes.resolve_target.tool_identify_trip_from_label",
               new_callable=AsyncMock, return_value=None):
        
        result = await resolve_target(state)
        
        assert result.get("needs_clarification") is True


@pytest.mark.asyncio
async def test_resolve_ocr_selectedtripid():
    """Test OCR bypass - selectedTripId takes precedence"""
    
    state = {
        "action": "cancel_trip",
        "text": "Cancel trip",
        "selectedTripId": 5,
        "user_id": 1
    }
    
    # Mock database lookup for OCR trip
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
        result = await resolve_target(state)
        
        assert result["trip_id"] == 5
        assert result["trip_label"] == "Path-3 - 07:30"


@pytest.mark.asyncio
async def test_resolve_target_multiple_matches_clarify():
    """Test that multiple matches trigger clarification"""
    
    state = {
        "action": "cancel_trip",
        "text": "Cancel 7:30 trip",
        "target_label": "7:30",
        "parsed_params": {},
        "confidence": 0.70,
        "clarify_options": ["Path-3 - 07:30", "Path-3 - 19:30"],
        "user_id": 1
    }
    
    # If tool returns None but LLM already suggested clarify_options
    with patch("langgraph.nodes.resolve_target.tool_identify_trip_from_label",
               new_callable=AsyncMock, return_value=None):
        
        result = await resolve_target(state)
        
        # Should preserve clarify_options from LLM
        assert result.get("needs_clarification") is True
        assert len(result.get("clarify_options", [])) == 2
