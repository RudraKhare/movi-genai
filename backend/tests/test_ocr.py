"""
Tests for OCR, Text Extraction, and Trip Matching

Tests the complete OCR pipeline:
1. Image preprocessing and OCR
2. Text cleaning and candidate extraction
3. Fuzzy trip matching
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from PIL import Image
import io

from app.core.text_extract import (
    clean_text,
    extract_time_patterns,
    extract_route_keywords,
    extract_shift_patterns,
    extract_candidates
)
from app.core.trip_matcher import compute_fuzzy_score, match_candidates


# ==================== Text Extraction Tests ====================

def test_clean_text():
    """Test text cleaning and normalization."""
    # Test lowercase conversion
    assert clean_text("HELLO WORLD") == "hello world"
    
    # Test whitespace normalization
    assert clean_text("hello    world") == "hello world"
    assert clean_text("  hello world  ") == "hello world"
    
    # Test dash normalization
    assert clean_text("hello–world—test") == "hello-world-test"


def test_extract_time_patterns():
    """Test time pattern extraction."""
    # Test HH:MM format
    text = "Meeting at 09:30 and 14:45"
    times = extract_time_patterns(text)
    assert "09:30" in times or "9:30" in times
    assert "14:45" in times
    
    # Test edge cases
    text2 = "Bulk - 00:01 and Path-3 - 07:30"
    times2 = extract_time_patterns(text2)
    assert "00:01" in times2 or "0:01" in times2
    assert "07:30" in times2 or "7:30" in times2
    
    # Test no times
    text3 = "No times here"
    times3 = extract_time_patterns(text3)
    assert len(times3) == 0


def test_extract_route_keywords():
    """Test route keyword extraction."""
    text = "Route Jayanagar and Path BTM"
    keywords = extract_route_keywords(text)
    
    # Should extract route names
    assert any("jayanagar" in k for k in keywords)
    assert any("btm" in k for k in keywords)


def test_extract_shift_patterns():
    """Test shift pattern extraction."""
    text = "Bulk - 00:01 and BTM - 08:30"
    patterns = extract_shift_patterns(text)
    
    assert "bulk - 00:01" in patterns or "bulk - 0:01" in patterns
    assert "btm - 08:30" in patterns or "btm - 8:30" in patterns


def test_extract_candidates():
    """Test candidate extraction."""
    text = "Bulk - 00:01\nRoute Jayanagar\n09:30"
    candidates = extract_candidates(text)
    
    # Should extract full text
    assert any("bulk" in c.lower() for c in candidates)
    
    # Should extract time
    assert any("09:30" in c or "9:30" in c for c in candidates)
    
    # Should have multiple candidates
    assert len(candidates) > 5


# ==================== Trip Matching Tests ====================

def test_compute_fuzzy_score_exact_match():
    """Test fuzzy scoring with exact match."""
    trip = {
        "trip_id": 1,
        "display_name": "Bulk - 00:01",
        "scheduled_time": "00:01",
        "route_name": "Route A",
        "path_name": "Path 1"
    }
    
    # Exact match should score very high
    score = compute_fuzzy_score("Bulk - 00:01", trip)
    assert score > 0.9  # Should be >90%


def test_compute_fuzzy_score_partial_match():
    """Test fuzzy scoring with partial match."""
    trip = {
        "trip_id": 1,
        "display_name": "Jayanagar - 08:00",
        "scheduled_time": "08:00",
        "route_name": "Route Jayanagar",
        "path_name": "Path 3"
    }
    
    # Partial match should score moderately
    score = compute_fuzzy_score("Jayanagar 08:00", trip)
    assert score > 0.6  # Should be >60%
    
    # Just time match should score lower
    score2 = compute_fuzzy_score("08:00", trip)
    assert score2 > 0.2  # Time component = 25%


def test_compute_fuzzy_score_no_match():
    """Test fuzzy scoring with no match."""
    trip = {
        "trip_id": 1,
        "display_name": "Bulk - 00:01",
        "scheduled_time": "00:01",
        "route_name": "Route A",
        "path_name": "Path 1"
    }
    
    # Completely different text should score low
    score = compute_fuzzy_score("Random unrelated text xyz", trip)
    assert score < 0.3  # Should be <30%


@pytest.mark.asyncio
async def test_match_candidates_single_match():
    """Test matching with single confident match."""
    # Mock database trips
    mock_trips = [
        {
            "trip_id": 1,
            "display_name": "Bulk - 00:01",
            "scheduled_time": "00:01",
            "route_name": "Route A",
            "path_name": "Path 1",
            "route_id": 1,
            "live_status": "SCHEDULED"
        },
        {
            "trip_id": 2,
            "display_name": "BTM - 08:30",
            "scheduled_time": "08:30",
            "route_name": "Route B",
            "path_name": "Path 2",
            "route_id": 2,
            "live_status": "SCHEDULED"
        }
    ]
    
    with patch('app.core.trip_matcher.get_daily_trips', return_value=mock_trips):
        candidates = ["Bulk - 00:01", "bulk", "00:01"]
        result = await match_candidates(candidates, confidence_threshold=0.65)
        
        assert result["match_type"] == "single"
        assert result["trip_id"] == 1
        assert result["auto_forward"] == True
        assert result["confidence"] > 0.65


@pytest.mark.asyncio
async def test_match_candidates_multiple_matches():
    """Test matching with ambiguous results."""
    # Mock database trips with similar names
    mock_trips = [
        {
            "trip_id": 1,
            "display_name": "Jayanagar - 08:00",
            "scheduled_time": "08:00",
            "route_name": "Route Jayanagar",
            "path_name": "Path 3",
            "route_id": 1,
            "live_status": "SCHEDULED"
        },
        {
            "trip_id": 2,
            "display_name": "Jayanagar - 08:05",
            "scheduled_time": "08:05",
            "route_name": "Route Jayanagar",
            "path_name": "Path 3",
            "route_id": 2,
            "live_status": "SCHEDULED"
        }
    ]
    
    with patch('app.core.trip_matcher.get_daily_trips', return_value=mock_trips):
        # Ambiguous candidate - just "Jayanagar" without time
        candidates = ["Jayanagar", "route jayanagar"]
        result = await match_candidates(candidates, confidence_threshold=0.60)
        
        # Should return multiple matches or single if one is clearly better
        assert result["match_type"] in ["single", "multiple"]
        
        if result["match_type"] == "multiple":
            assert result["needs_clarification"] == True
            assert len(result["candidates"]) >= 2
            assert result["auto_forward"] == False


@pytest.mark.asyncio
async def test_match_candidates_no_match():
    """Test matching with no valid matches."""
    mock_trips = [
        {
            "trip_id": 1,
            "display_name": "Bulk - 00:01",
            "scheduled_time": "00:01",
            "route_name": "Route A",
            "path_name": "Path 1",
            "route_id": 1,
            "live_status": "SCHEDULED"
        }
    ]
    
    with patch('app.core.trip_matcher.get_daily_trips', return_value=mock_trips):
        # Completely unrelated text
        candidates = ["random text xyz", "nothing matches"]
        result = await match_candidates(candidates, confidence_threshold=0.65)
        
        assert result["match_type"] == "none"
        assert result["auto_forward"] == False
        assert "message" in result


@pytest.mark.asyncio
async def test_match_candidates_empty_input():
    """Test matching with empty candidates."""
    result = await match_candidates([], confidence_threshold=0.65)
    
    assert result["match_type"] == "none"
    assert result["auto_forward"] == False


# ==================== OCR Mock Tests ====================

def create_test_image(text: str, size=(400, 100)) -> bytes:
    """
    Create a simple test image with text.
    
    Args:
        text: Text to draw on image
        size: Image size tuple
        
    Returns:
        Image bytes
    """
    from PIL import Image, ImageDraw, ImageFont
    
    # Create white image
    img = Image.new('RGB', size, color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw text (simple, no fancy fonts)
    draw.text((10, 40), text, fill='black')
    
    # Convert to bytes
    output = io.BytesIO()
    img.save(output, format='PNG')
    return output.getvalue()


@pytest.mark.asyncio
async def test_ocr_extract_text_mock():
    """Test OCR with mocked Vision API."""
    from app.core.ocr import extract_text_from_image
    
    # Create mock response
    mock_annotation = Mock()
    mock_annotation.description = "Bulk - 00:01"
    mock_annotation.confidence = 0.95
    
    mock_response = Mock()
    mock_response.text_annotations = [mock_annotation]
    mock_response.error.message = ""
    
    # Mock Vision client
    mock_client = Mock()
    mock_client.text_detection = Mock(return_value=mock_response)
    
    with patch('app.core.ocr.get_vision_client', return_value=mock_client):
        test_img = create_test_image("Bulk - 00:01")
        result = extract_text_from_image(test_img, preprocess=False)
        
        assert result["success"] == True
        assert "bulk" in result["text"].lower()
        assert result["confidence"] > 0


def test_image_preprocessing():
    """Test image preprocessing pipeline."""
    from app.core.ocr import preprocess_image
    
    # Create test image
    test_img = create_test_image("Test Text", size=(800, 200))
    
    # Preprocess
    processed = preprocess_image(test_img)
    
    # Should return bytes
    assert isinstance(processed, bytes)
    assert len(processed) > 0
    
    # Should be valid image
    img = Image.open(io.BytesIO(processed))
    assert img.mode == 'L'  # Grayscale


# ==================== Integration Test ====================

@pytest.mark.asyncio
async def test_full_ocr_pipeline_mock():
    """Test complete OCR pipeline with mocked components."""
    from app.core.ocr import extract_text_from_image
    from app.core.text_extract import clean_text, extract_candidates
    from app.core.trip_matcher import match_candidates
    
    # Step 1: Mock OCR
    mock_annotation = Mock()
    mock_annotation.description = "Bulk - 00:01\nRoute A"
    mock_annotation.confidence = 0.90
    
    mock_response = Mock()
    mock_response.text_annotations = [mock_annotation]
    mock_response.error.message = ""
    
    mock_client = Mock()
    mock_client.text_detection = Mock(return_value=mock_response)
    
    # Step 2: Mock database
    mock_trips = [
        {
            "trip_id": 1,
            "display_name": "Bulk - 00:01",
            "scheduled_time": "00:01",
            "route_name": "Route A",
            "path_name": "Path 1",
            "route_id": 1,
            "live_status": "SCHEDULED"
        }
    ]
    
    with patch('app.core.ocr.get_vision_client', return_value=mock_client), \
         patch('app.core.trip_matcher.get_daily_trips', return_value=mock_trips):
        
        # Run pipeline
        test_img = create_test_image("Bulk - 00:01")
        
        # OCR
        ocr_result = extract_text_from_image(test_img, preprocess=False)
        assert ocr_result["success"] == True
        
        # Extract
        cleaned = clean_text(ocr_result["text"])
        candidates = extract_candidates(cleaned)
        assert len(candidates) > 0
        
        # Match
        match_result = await match_candidates(candidates)
        assert match_result["match_type"] in ["single", "multiple", "none"]


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
