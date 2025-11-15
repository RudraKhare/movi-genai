"""
Create Trip Suggester Node
Offers to create a new trip when one is not found.
"""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


async def create_trip_suggester(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    When a trip is not found (especially from image OCR), offer to create it.
    
    Extracts any available info from:
    - OCR text
    - User message
    - Image metadata
    
    Then asks: "Would you like to create this trip?"
    """
    
    ocr_text = state.get("ocr_text", "")
    user_message = state.get("user_message", "")
    extracted_info = {}
    
    logger.info(f"Trip not found. Offering to create. OCR: {ocr_text[:50]}...")
    
    # Try to extract useful info from OCR/text
    if ocr_text:
        # Simple extraction patterns
        text_lower = ocr_text.lower()
        
        # Extract potential trip name (e.g., "Path-1", "Bulk")
        import re
        name_match = re.search(r'(path-\d+|bulk|express|tech-loop|[a-z]+-\d+)', text_lower)
        if name_match:
            extracted_info["suggested_name"] = name_match.group(1).title()
        
        # Extract time (e.g., "08:00", "00:01")
        time_match = re.search(r'(\d{1,2}:\d{2})', ocr_text)
        if time_match:
            extracted_info["suggested_time"] = time_match.group(1)
        
        # Extract date
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', ocr_text)
        if date_match:
            extracted_info["suggested_date"] = date_match.group(1)
    
    # Build message with extracted info
    message = "This trip doesn't exist yet."
    
    if extracted_info:
        message += "\n\nI detected:"
        if extracted_info.get("suggested_name"):
            message += f"\n• **Name**: {extracted_info['suggested_name']}"
        if extracted_info.get("suggested_time"):
            message += f"\n• **Time**: {extracted_info['suggested_time']}"
        if extracted_info.get("suggested_date"):
            message += f"\n• **Date**: {extracted_info['suggested_date']}"
    
    message += "\n\n**Would you like to create it?**"
    
    state["message"] = message
    state["extracted_info"] = extracted_info
    
    # Offer two options
    state["suggestions"] = [
        {
            "action": "start_trip_wizard",
            "label": "✅ Yes, create trip",
            "description": "Start guided trip creation wizard"
        },
        {
            "action": "cancel_wizard",
            "label": "❌ No, cancel",
            "description": "Don't create anything"
        }
    ]
    
    state["awaiting_user_selection"] = True
    state["status"] = "creation_offered"
    state["next_node"] = "report_result"
    
    logger.info(f"Offered trip creation with extracted info: {extracted_info}")
    
    return state
