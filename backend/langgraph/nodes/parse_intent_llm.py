"""
Parse Intent LLM Node
Uses LLM to extract user intent and action type from natural language input
"""
from typing import Dict
import logging

logger = logging.getLogger(__name__)


async def parse_intent_llm(state: Dict) -> Dict:
    """
    Parse the user's text input using LLM to identify the intended action.
    
    LLM Flow:
    1. Checks if selectedTripId exists (OCR flow) → skip LLM, use context
    2. Calls LLM with text and context
    3. Merges LLM output into state
    4. Sets needs_clarification if LLM unsure
    
    CRITICAL: This node does NOT query the database or verify trip IDs.
    Verification happens in resolve_target node.
    
    Args:
        state: Graph state with 'text' field, optionally 'selectedTripId'
        
    Returns:
        Updated state with LLM-parsed fields:
        - action: cancel_trip, remove_vehicle, assign_vehicle, unknown
        - target_label: LLM's suggested trip/route name
        - target_time: Extracted time if present
        - parsed_params: {vehicle_id, driver_id, target_trip_id}
        - confidence: 0.0-1.0
        - llm_explanation: Human-readable reasoning
        - needs_clarification: True if LLM unsure
        - clarify_options: List of suggestions if ambiguous
    """
    text = state.get("text", "").lower().strip()
    selected_trip_id = state.get("selectedTripId")
    
    if not text:
        state["action"] = "unknown"
        state["error"] = "No input text provided"
        logger.warning("[LLM] No text provided")
        return state
    
    logger.info(f"[LLM] Parsing intent from: {text}")
    
    # Import LLM client
    try:
        from langgraph.tools.llm_client import parse_intent_with_llm
    except ImportError as e:
        logger.error(f"[LLM] Failed to import LLM client: {e}")
        state["action"] = "unknown"
        state["error"] = "LLM client not available"
        state["needs_clarification"] = True
        return state
    
    # Build context for LLM
    context = {
        "currentPage": state.get("currentPage"),
        "selectedRouteId": state.get("selectedRouteId"),
        "conversation_history": state.get("conversation_history", []),
    }
    
    try:
        # Call LLM to parse intent
        logger.info(f"[LLM] Calling parse_intent_with_llm with context: {context}")
        llm_response = await parse_intent_with_llm(text, context)
        
        # Log LLM response
        logger.info(f"[LLM] Response: action={llm_response.get('action')}, "
                   f"confidence={llm_response.get('confidence', 0.0):.2f}, "
                   f"clarify={llm_response.get('clarify')}")
        
        # Merge LLM output into state
        state["action"] = llm_response.get("action", "unknown")
        state["target_label"] = llm_response.get("target_label")
        state["target_time"] = llm_response.get("target_time")
        state["target_trip_id"] = llm_response.get("target_trip_id")
        state["target_path_id"] = llm_response.get("target_path_id")
        state["target_route_id"] = llm_response.get("target_route_id")
        state["confidence"] = llm_response.get("confidence", 0.0)
        state["llm_explanation"] = llm_response.get("explanation", "")
        
        # Extract parameters (all possible fields)
        parameters = llm_response.get("parameters", {})
        state["parsed_params"] = parameters
        
        # If LLM provided ID suggestions, store them
        # NOTE: These are NOT verified yet! resolve_target will verify them
        if parameters.get("target_trip_id"):
            logger.info(f"[LLM] Suggested trip_id: {parameters['target_trip_id']} "
                       f"(needs DB verification)")
        if llm_response.get("target_path_id"):
            logger.info(f"[LLM] Suggested path_id: {llm_response['target_path_id']}")
        if llm_response.get("target_route_id"):
            logger.info(f"[LLM] Suggested route_id: {llm_response['target_route_id']}")
        
        # Check if clarification needed
        if llm_response.get("clarify"):
            state["needs_clarification"] = True
            state["clarify_options"] = llm_response.get("clarify_options", [])
            logger.info(f"[LLM] Clarification needed. Options: {state['clarify_options']}")
        else:
            state["needs_clarification"] = False
        
        logger.info(f"[LLM] Successfully parsed intent: {state['action']}")
        
        # IMPORTANT: Only use OCR trip_id if this request came from an image (from_image=True)
        # OR if the user is clicking a suggestion button (which would reference the OCR trip)
        # Don't persist OCR context forever - only for immediate follow-up actions
        from_image = state.get("from_image", False)
        if selected_trip_id and from_image:
            logger.info(f"[LLM] Overriding with OCR trip_id from current image: {selected_trip_id}")
            state["trip_id"] = selected_trip_id
            state["target_trip_id"] = selected_trip_id
        elif selected_trip_id and not from_image:
            # OCR context exists but this is a new text query
            # Let LLM's parsed trip_id take precedence
            logger.info(f"[LLM] Ignoring stale OCR trip_id {selected_trip_id}, using LLM-parsed trip_id instead")
        
    except Exception as e:
        logger.error(f"[LLM] Error parsing intent: {e}", exc_info=True)
        # Fallback to safe state
        state["action"] = "unknown"
        state["error"] = f"LLM parsing failed: {str(e)}"
        state["needs_clarification"] = True
        state["clarify_options"] = [
            "Please rephrase your request",
            "Try being more specific about which trip or vehicle"
        ]
        state["confidence"] = 0.0
        state["llm_explanation"] = "Error processing request, please clarify"
    
    return state
