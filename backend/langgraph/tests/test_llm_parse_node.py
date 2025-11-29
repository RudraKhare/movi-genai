"""
Unit tests for LLM Parse Intent Node
Tests the parse_intent_llm node with mocked LLM responses
"""
import pytest
from unittest.mock import patch, AsyncMock
from langgraph.nodes.parse_intent_llm import parse_intent_llm


@pytest.mark.asyncio
async def test_parse_intent_llm_success():
    """Test successful LLM parsing with valid response"""
    
    # Mock LLM response
    mock_llm_response = {
        "action": "cancel_trip",
        "target_label": "Bulk - 00:01",
        "target_time": "00:01",
        "target_trip_id": None,
        "parameters": {},
        "confidence": 0.95,
        "clarify": False,
        "clarify_options": [],
        "explanation": "User wants to cancel a specific trip"
    }
    
    # Input state
    state = {
        "text": "Cancel Bulk - 00:01",
        "user_id": 1
    }
    
    # Mock the LLM client (import happens inside the function)
    with patch("langgraph.tools.llm_client.parse_intent_with_llm", 
               new_callable=AsyncMock, return_value=mock_llm_response):
        
        result = await parse_intent_llm(state)
        
        # Assertions
        assert result["action"] == "cancel_trip"
        assert result["target_label"] == "Bulk - 00:01"
        assert result["confidence"] == 0.95
        assert result["llm_explanation"] == "User wants to cancel a specific trip"
        assert result["needs_clarification"] is False


@pytest.mark.asyncio
async def test_parse_intent_llm_clarify():
    """Test LLM returns clarify=true for ambiguous input"""
    
    mock_llm_response = {
        "action": "cancel_trip",
        "target_label": None,
        "target_time": "07:30",
        "target_trip_id": None,
        "parameters": {},
        "confidence": 0.60,
        "clarify": True,
        "clarify_options": ["Path-3 - 07:30", "Path-3 - 19:30"],
        "explanation": "Multiple trips at 7:30, need clarification"
    }
    
    state = {
        "text": "Cancel the 7:30 run",
        "user_id": 1
    }
    
    with patch("langgraph.tools.llm_client.parse_intent_with_llm",
               new_callable=AsyncMock, return_value=mock_llm_response):
        
        result = await parse_intent_llm(state)
        
        assert result["action"] == "cancel_trip"
        assert result["needs_clarification"] is True
        assert len(result["clarify_options"]) == 2
        assert "Path-3 - 07:30" in result["clarify_options"]


@pytest.mark.asyncio
async def test_parse_intent_llm_ocr_bypass():
    """Test that LLM is skipped when selectedTripId is present"""
    
    state = {
        "text": "Cancel trip",
        "selectedTripId": 5,
        "user_id": 1
    }
    
    # LLM should NOT be called
    with patch("langgraph.tools.llm_client.parse_intent_with_llm",
               new_callable=AsyncMock) as mock_llm:
        
        result = await parse_intent_llm(state)
        
        # LLM should not have been called
        mock_llm.assert_not_called()
        
        # Should use context bypass
        assert result.get("selectedTripId") == 5
        assert ("context" in str(result.get("llm_explanation", "")).lower() or 
                "OCR" in str(result.get("llm_explanation", "")) or 
                "skipped" in str(result.get("llm_explanation", "")))


@pytest.mark.asyncio
async def test_parse_intent_llm_confidence_normalized():
    """Test that confidence values from LLM are passed through correctly"""
    
    mock_llm_response = {
        "action": "cancel_trip",
        "target_label": "Test Trip",
        "target_time": None,
        "target_trip_id": None,
        "parameters": {},
        "confidence": 0.85,  # Valid confidence (LLM client validation already happened)
        "clarify": False,
        "clarify_options": [],
        "explanation": "Test"
    }
    
    state = {"text": "Cancel test trip", "user_id": 1}
    
    with patch("langgraph.tools.llm_client.parse_intent_with_llm",
               new_callable=AsyncMock, return_value=mock_llm_response):
        
        result = await parse_intent_llm(state)
        
        # Confidence should match what LLM client returned (already validated)
        assert result["confidence"] == 0.85
        assert result["confidence"] <= 1.0
        assert result["confidence"] >= 0.0


@pytest.mark.asyncio
async def test_parse_intent_llm_empty_text():
    """Test handling of empty input text"""
    
    state = {
        "text": "",
        "user_id": 1
    }
    
    result = await parse_intent_llm(state)
    
    assert result["action"] == "unknown"
    assert "error" in result


@pytest.mark.asyncio
async def test_parse_intent_llm_error_handling():
    """Test graceful error handling when LLM fails - should fall back to regex"""
    
    state = {
        "text": "Cancel trip",
        "user_id": 1
    }
    
    # Mock LLM to raise exception
    with patch("langgraph.tools.llm_client.parse_intent_with_llm",
               new_callable=AsyncMock, side_effect=Exception("LLM API Error")):
        
        result = await parse_intent_llm(state)
        
        # Should fall back to regex parsing (which recognizes "cancel")
        assert result["action"] == "cancel_trip"  # Regex fallback should work
        assert result["confidence"] == 0.3  # Lower confidence for fallback
        assert "fallback" in result.get("llm_explanation", "").lower()


@pytest.mark.asyncio
async def test_parse_intent_llm_assign_vehicle():
    """Test parsing assign vehicle action"""
    
    mock_llm_response = {
        "action": "assign_vehicle",
        "target_label": "Jayanagar - 08:00",
        "target_time": "08:00",
        "target_trip_id": None,
        "parameters": {
            "vehicle_id": 5,
            "driver_id": 3
        },
        "confidence": 0.88,
        "clarify": False,
        "clarify_options": [],
        "explanation": "Assign vehicle 5 and driver 3 to trip"
    }
    
    state = {
        "text": "Assign bus 5 driver 3 to Jayanagar route",
        "user_id": 1
    }
    
    with patch("langgraph.tools.llm_client.parse_intent_with_llm",
               new_callable=AsyncMock, return_value=mock_llm_response):
        
        result = await parse_intent_llm(state)
        
        assert result["action"] == "assign_vehicle"
        assert result["parsed_params"]["vehicle_id"] == 5
        assert result["parsed_params"]["driver_id"] == 3


@pytest.mark.asyncio
async def test_llm_client_confidence_validation():
    """Test that LLM client validation clamps confidence to 0-1 range"""
    from langgraph.tools.llm_client import _validate_llm_response
    
    # Test confidence > 1.0
    response_high = {
        "action": "cancel_trip",
        "confidence": 1.5,
        "clarify": False,
        "explanation": "Test"
    }
    validated = _validate_llm_response(response_high)
    assert validated["confidence"] == 1.0, "Confidence > 1.0 should be clamped to 1.0"
    
    # Test confidence < 0.0
    response_low = {
        "action": "cancel_trip",
        "confidence": -0.5,
        "clarify": False,
        "explanation": "Test"
    }
    validated = _validate_llm_response(response_low)
    assert validated["confidence"] == 0.0, "Confidence < 0.0 should be clamped to 0.0"
    
    # Test valid confidence
    response_valid = {
        "action": "cancel_trip",
        "confidence": 0.75,
        "clarify": False,
        "explanation": "Test"
    }
    validated = _validate_llm_response(response_valid)
    assert validated["confidence"] == 0.75, "Valid confidence should be preserved"


@pytest.mark.asyncio
async def test_parse_intent_llm_complete_failure():
    """Test complete fallback when both LLM and regex fail"""
    
    state = {
        "text": "some gibberish that wont match regex",
        "user_id": 1
    }
    
    # Mock LLM to raise exception
    with patch("langgraph.tools.llm_client.parse_intent_with_llm",
               new_callable=AsyncMock, side_effect=Exception("LLM API Error")):
        
        result = await parse_intent_llm(state)
        
        # Should return complete fallback when both LLM and regex fail
        assert result["action"] == "unknown"
        assert result["confidence"] == 0.0
        assert "failed" in result.get("llm_explanation", "").lower()
        assert result["needs_clarification"] == True
