"""
Agent Image API Endpoint - COMPLETE OCR + TRIP MATCHING

This endpoint:
1. Extracts text from image using Google Cloud Vision OCR
2. Matches extracted text against database trips using fuzzy matching
3. Returns structured response for frontend to display

Returns one of three match types:
- "single": Confident single match with trip details
- "multiple": Ambiguous matches requiring user clarification
- "none": No match found
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Header
from typing import Optional
import logging

from app.core.ocr import extract_text_from_image
from app.core.trip_matcher import match_candidates

router = APIRouter(prefix="/agent", tags=["agent"])
logger = logging.getLogger(__name__)


@router.post("/image")
async def process_image(
    file: UploadFile = File(...),
    x_api_key: Optional[str] = Header(None)
):
    """
    Process uploaded image: OCR extraction + Trip matching.
    
    Flow:
    1. Validate image file
    2. Extract text using Google Cloud Vision OCR
    3. Match extracted text against database trips (fuzzy matching)
    4. Return structured response
    
    Returns:
    - match_type: "single" | "multiple" | "none"
    - For "single": trip_id, display_name, confidence, auto_forward=True
    - For "multiple": candidates list with trip options
    - For "none": error message
    """
    # Validate API key
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API key")
    
    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only images (jpg, jpeg, png) are supported."
        )
    
    try:
        # Read image bytes
        image_bytes = await file.read()
        
        if len(image_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        
        logger.info(f"[OCR] Processing image: {file.filename}, size: {len(image_bytes)} bytes")
        
        # PHASE 1: Extract text using Google Vision OCR
        logger.info("[OCR] Starting text extraction...")
        ocr_result = extract_text_from_image(image_bytes, preprocess=True)
        
        if not ocr_result["success"]:
            error_msg = ocr_result.get("message", "Failed to extract text from image")
            logger.error(f"[OCR] ❌ Extraction failed: {error_msg}")
            return {
                "match_type": "none",
                "message": error_msg,
                "auto_forward": False
            }
        
        raw_text = ocr_result["text"]
        ocr_confidence = ocr_result["confidence"]
        blocks = ocr_result.get("blocks", [])
        
        logger.info(f"[OCR] ✅ Extracted {len(raw_text)} chars, confidence: {ocr_confidence:.2f}")
        logger.info(f"[OCR] Preview: {raw_text[:200]}...")
        
        if not raw_text or len(raw_text.strip()) < 3:
            logger.warning("[OCR] ⚠️ No readable text found in image")
            return {
                "match_type": "none",
                "message": "No readable text found in image. Please try a clearer image.",
                "auto_forward": False
            }
        
        # STEP 2: Match extracted text against database trips
        logger.info("[OCR] Starting trip matching...")
        
        # Build candidate list: full text + individual blocks for better matching
        candidates = [raw_text]
        if blocks:
            candidates.extend(blocks[:10])  # Add top 10 blocks
        
        # Remove duplicates while preserving order
        seen = set()
        unique_candidates = []
        for c in candidates:
            c_clean = c.strip()
            if c_clean and c_clean not in seen:
                seen.add(c_clean)
                unique_candidates.append(c_clean)
        
        logger.info(f"[OCR] Matching {len(unique_candidates)} candidates against trips...")
        
        # Perform fuzzy matching against database
        match_result = await match_candidates(unique_candidates, confidence_threshold=0.65)
        
        logger.info(f"[OCR] Match result: {match_result.get('match_type')}")
        
        # Add OCR text to result for debugging/display
        match_result["ocr_text"] = raw_text
        match_result["ocr_confidence"] = ocr_confidence
        
        return match_result
        
    except Exception as e:
        logger.error(f"[OCR] ❌ Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Image processing failed: {str(e)}"
        )


@router.get("/image/test")
async def test_image_endpoint():
    """
    Test endpoint to verify image API is working.
    """
    return {
        "status": "ok",
        "message": "Image OCR + Trip Matching endpoint is ready",
        "supported_formats": ["jpg", "jpeg", "png"],
        "max_file_size": "10MB",
        "features": [
            "Google Cloud Vision OCR",
            "Fuzzy trip matching with rapidfuzz",
            "Returns single/multiple/none match types"
        ]
    }

