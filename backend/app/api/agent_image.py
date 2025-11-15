"""
Agent Image API Endpoint - PHASE 1: TEXT EXTRACTION ONLY

This endpoint does ONE thing: extract text from image.
NO trip matching, NO action building, NO intelligence.

The extracted text is sent to /api/agent/message where LLM + LangGraph handle everything.
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Header
from typing import Optional
import logging

from app.core.ocr import extract_text_from_image

router = APIRouter(prefix="/agent", tags=["agent"])
logger = logging.getLogger(__name__)


@router.post("/image")
async def process_image(
    file: UploadFile = File(...),
    x_api_key: Optional[str] = Header(None)
):
    """
    PHASE 1: OCR - TEXT EXTRACTION ONLY
    
    This endpoint extracts text from uploaded image using Google Vision API.
    It does NOT:
    - Match trips
    - Build actions
    - Query database
    - Make decisions
    
    The extracted text is returned to frontend, which then sends it to
    /api/agent/message where LLM + LangGraph handle all intelligence.
    
    Returns:
    {
        "match_type": "text_extracted",
        "ocr_text": "... full extracted text ...",
        "blocks": ["line1", "line2", ...],
        "confidence": 0.94
    }
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
                "match_type": "text_extracted",
                "ocr_text": "",
                "blocks": [],
                "confidence": 0.0,
                "error": error_msg
            }
        
        raw_text = ocr_result["text"]
        ocr_confidence = ocr_result["confidence"]
        blocks = ocr_result.get("blocks", [])
        
        logger.info(f"[OCR] ✅ Extracted {len(raw_text)} chars, confidence: {ocr_confidence:.2f}")
        logger.info(f"[OCR] Preview: {raw_text[:200]}...")
        
        if not raw_text or len(raw_text.strip()) < 3:
            logger.warning("[OCR] ⚠️ No readable text found in image")
            return {
                "match_type": "text_extracted",
                "ocr_text": raw_text,
                "blocks": blocks,
                "confidence": ocr_confidence,
                "warning": "No readable text found. Try a clearer image."
            }
        
        # Return ONLY the extracted text
        # Frontend will send this to /api/agent/message with from_image=true
        # Then LLM + LangGraph will handle all intelligence
        return {
            "match_type": "text_extracted",
            "ocr_text": raw_text,
            "blocks": blocks,
            "confidence": ocr_confidence
        }
        
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
        "message": "Image OCR endpoint is ready (text extraction only)",
        "supported_formats": ["jpg", "jpeg", "png"],
        "max_file_size": "10MB",
        "note": "OCR only extracts text. Intelligence handled by LLM + LangGraph."
    }

