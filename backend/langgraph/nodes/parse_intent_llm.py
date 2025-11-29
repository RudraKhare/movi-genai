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
    1. Checks if wizard is active → route to wizard continuation
    2. Checks if selectedTripId exists (OCR flow) → skip LLM, use context
    3. Calls LLM with text and context
    4. Merges LLM output into state
    5. Sets needs_clarification if LLM unsure
    
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
    
    # ✅ WIZARD CONTINUATION: If wizard is active, route user input to wizard
    if state.get("wizard_active") or state.get("awaiting_wizard_input"):
        wizard_type = state.get("wizard_type", "")
        logger.info(f"[WIZARD] Wizard active (type={wizard_type}), routing user input: '{text}'")
        state["user_message"] = state.get("text", "")  # Store raw text for wizard
        
        # Add_vehicle and add_driver wizards are handled in execute_action
        if wizard_type in ["add_vehicle", "add_driver"]:
            logger.info(f"[WIZARD] {wizard_type} wizard continues in execute_action")
            state["action"] = wizard_type  # Keep original action
            state["next_node"] = "execute_action"
            return state
        
        # Other wizards (create_stop, create_path, create_route) use collect_user_input
        state["action"] = "wizard_step_input"
        state["next_node"] = "collect_user_input"  # Go directly to input collection
        return state
    
    # Handle structured commands from frontend UI selections
    if text.startswith("structured_cmd:"):
        logger.info(f"[STRUCTURED] Processing structured command: '{text}'")
        return await parse_structured_command(state, text)
    
    # CONTEXT AWARENESS FIX: Handle "this trip" and general context-aware commands
    # Use word boundary matching to avoid false positives like "Smith" containing "it"
    import re
    context_patterns = [
        r'\bthis trip\b', r'\bcurrent trip\b', r'\bthis\b', r'\bhere\b', r'\bit\b'
    ]
    has_context_reference = any(re.search(pattern, text) for pattern in context_patterns)
    
    if selected_trip_id and has_context_reference:
        logger.info(f"[CONTEXT] Found context reference with selectedTripId={selected_trip_id}")
        
        # Detect action type from text
        # ✅ FIX: Check for remove/unassign BEFORE assign to handle "unassign vehicle" correctly
        if "remove vehicle" in text or "unassign vehicle" in text:
            action = "remove_vehicle"
        elif "remove driver" in text or "unassign driver" in text:
            action = "remove_driver"
        elif "assign vehicle" in text or ("assign" in text and "vehicle" in text):
            action = "assign_vehicle"
        elif "assign driver" in text or ("assign" in text and "driver" in text):
            action = "assign_driver"
        elif "cancel" in text:
            action = "cancel_trip"
        else:
            action = "assign_vehicle"  # Default for context
        
        # Use context directly without LLM
        state.update({
            "action": action,
            "target_trip_id": selected_trip_id,
            "confidence": 0.95,  # High confidence with context
            "needs_clarification": False,
            "llm_explanation": f"Using context: selectedTripId={selected_trip_id}",
            "parsed_params": {"trip_id": selected_trip_id}
        })
        
        logger.info(f"[CONTEXT] ✅ Resolved context reference to action={action}, trip_id={selected_trip_id}")
        return state
    
    # ENHANCED CONTEXT AWARENESS: For basic actions without explicit "this trip"
    # If selectedTripId exists and user mentions common actions, assume they mean the selected trip
    # ✅ FIX: BUT only if user doesn't explicitly mention a different trip ID in their message
    action_keywords = ["assign vehicle", "assign driver", "remove vehicle"]
    cancel_with_context = "cancel" in text and ("trip" in text or "this" in text)
    
    # Check if user explicitly mentions a trip ID (e.g., "trip 39", "trip 40")
    import re
    explicit_trip_match = re.search(r'\btrip\s*#?\s*(\d+)\b', text, re.IGNORECASE)
    has_explicit_trip_id = explicit_trip_match is not None
    
    if selected_trip_id and (any(keyword in text for keyword in action_keywords) or cancel_with_context):
        # ✅ FIX: If user explicitly mentioned a trip ID, let LLM handle it - don't use context
        if has_explicit_trip_id:
            explicit_id = int(explicit_trip_match.group(1))
            logger.info(f"[CONTEXT] User explicitly mentioned trip {explicit_id}, ignoring selectedTripId={selected_trip_id} - letting LLM parse")
            # Fall through to LLM processing below (don't return, don't use context)
            pass
        else:
            logger.info(f"[CONTEXT] Found action with selectedTripId={selected_trip_id}, assuming context reference")
        
            # Detect action type from text
            # ✅ FIX: Check for remove/unassign BEFORE assign to handle "unassign vehicle" correctly
            if "remove vehicle" in text or "unassign vehicle" in text:
                action = "remove_vehicle"
            elif "remove driver" in text or "unassign driver" in text:
                action = "remove_driver"
            elif "assign vehicle" in text or ("assign" in text and "vehicle" in text):
                action = "assign_vehicle"
            elif "assign driver" in text or ("assign" in text and "driver" in text):
                action = "assign_driver"
            elif "cancel" in text:
                action = "cancel_trip"
            else:
                action = "assign_vehicle"  # Default
            
            # Use context directly without LLM
            state.update({
                "action": action,
                "target_trip_id": selected_trip_id,
                "confidence": 0.90,  # Slightly lower confidence without explicit "this"
                "needs_clarification": False,
                "llm_explanation": f"Using context: selectedTripId={selected_trip_id}, inferred reference",
                "parsed_params": {"trip_id": selected_trip_id}
            })
            
            logger.info(f"[CONTEXT] ✅ Inferred context reference to action={action}, trip_id={selected_trip_id}")
            return state
    
    # Safety check: prevent processing commands with "undefined" parameters
    if "undefined" in text.lower():
        state["action"] = "unknown"
        state["error"] = "invalid_selection"
        state["message"] = "It looks like you clicked an invalid option. Please select a valid driver or vehicle."
        logger.warning(f"[LLM] Rejected input containing 'undefined': '{text}'")
        return state
    
    if not text:
        state["action"] = "unknown"
        state["error"] = "No input text provided"
        logger.warning("[LLM] No text provided")
        return state
    
    logger.info(f"[LLM] 🤖 Processing natural language input: '{text}'")
    
    # Debug: Log the complete context to help identify frontend issues
    logger.info(f"[CONTEXT] Complete context received: selectedTripId={selected_trip_id}, ui_context={state.get('ui_context', {})}")
    
    # ENHANCED: If user says "this trip" but no selectedTripId, provide helpful guidance
    # Use word boundary matching to avoid false positives like "Smith" containing "it"
    import re
    context_patterns = [
        r'\bthis trip\b', r'\bcurrent trip\b', r'\bthis\b', 
        r'\bhere\b', r'\bit\b', r'\bthe trip\b'
    ]
    has_context_reference = any(re.search(pattern, text) for pattern in context_patterns)
    
    if has_context_reference and not selected_trip_id:
        logger.warning(f"[CONTEXT] User referenced 'this trip' but selectedTripId is None - frontend context issue")
        
        # Check if we can find a recent trip from conversation history or session
        recent_trip_id = None
        conversation_history = state.get('conversation_history', [])
        
        # Look for recent trip references in conversation
        for msg in reversed(conversation_history[-5:]):  # Check last 5 messages
            if isinstance(msg, dict) and msg.get('trip_id'):
                recent_trip_id = msg.get('trip_id')
                logger.info(f"[CONTEXT] Found recent trip_id={recent_trip_id} in conversation history")
                break
        
        # If we found a recent trip, suggest using it
        if recent_trip_id:
            state.update({
                "action": "unknown",
                "confidence": 0.0,
                "needs_clarification": True,
                "clarify_options": [
                    f"Did you mean trip {recent_trip_id}? Please select the trip first or specify the trip number.",
                    "Click on a trip from the list to select it",
                    f"Try: 'assign vehicle to trip {recent_trip_id}'"
                ],
                "llm_explanation": f"Context missing: You referred to 'this trip' but no trip is selected. Recent trip: {recent_trip_id}"
            })
        else:
            # Provide general helpful guidance
            state.update({
                "action": "unknown",
                "confidence": 0.0,
                "needs_clarification": True,
                "clarify_options": [
                    "Please select a trip first by clicking on it in the list",
                    "Try specifying the trip number: 'assign vehicle to trip 38'",
                    "Or browse trips and click on one to select it"
                ],
                "llm_explanation": "Context missing: You referred to 'this trip' but no trip is currently selected. Please select a trip first."
            })
        
        return state
    
    # Import LLM client
    try:
        from langgraph.tools.llm_client import parse_intent_with_llm
    except ImportError as e:
        logger.error(f"[LLM] Failed to import LLM client: {e}")
        state["action"] = "unknown"
        state["error"] = "LLM client not available"
        state["needs_clarification"] = True
        return state
    
    # Build comprehensive context for LLM
    context = {
        "selectedTripId": selected_trip_id,  # OCR or manual selection
        "currentPage": state.get("currentPage"),
        "selectedRouteId": state.get("selectedRouteId"),
        "selectedPathId": state.get("selectedPathId"),
        "conversation_history": state.get("conversation_history", []),
        "trip_details": state.get("trip_details"),
        "last_offered_options": state.get("last_offered_options"),
        "awaiting_selection": state.get("awaiting_selection"),
        "ui_context": {
            "selectedTripId": selected_trip_id,
            "selectedRouteId": state.get("selectedRouteId"),
            "selectedPathId": state.get("selectedPathId"),
            "currentTrip": state.get("trip_details"),
            "lastAction": state.get("last_action")
        }
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
        
        # IMPORTANT: For entity-based actions, copy target_label to the appropriate param
        # The LLM may put the name in target_label instead of parameters
        action = llm_response.get("action", "unknown")
        target_label = llm_response.get("target_label")
        
        if target_label:
            if action == "delete_route" and not parameters.get("route_name"):
                parameters["route_name"] = target_label
                logger.info(f"[LLM] Copied target_label to route_name: {target_label}")
            elif action == "delete_path" and not parameters.get("path_name"):
                parameters["path_name"] = target_label
                logger.info(f"[LLM] Copied target_label to path_name: {target_label}")
            elif action == "delete_stop" and not parameters.get("stop_name"):
                parameters["stop_name"] = target_label
                logger.info(f"[LLM] Copied target_label to stop_name: {target_label}")
            elif action == "rename_stop" and not parameters.get("stop_name"):
                parameters["stop_name"] = target_label
                logger.info(f"[LLM] Copied target_label to stop_name: {target_label}")
            elif action in ["create_route", "duplicate_route"] and not parameters.get("route_name"):
                parameters["route_name"] = target_label
                logger.info(f"[LLM] Copied target_label to route_name: {target_label}")
        
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
        
        # Check if clarification needed or if we need to ask for missing parameters
        confidence = llm_response.get("confidence", 0.0)
        action = llm_response.get("action", "unknown")
        
        if llm_response.get("clarify") or confidence < 0.6:
            state["needs_clarification"] = True
            state["clarify_options"] = llm_response.get("clarify_options", [])
            logger.info(f"[LLM] Clarification needed. Confidence: {confidence:.2f}, Options: {state['clarify_options']}")
        else:
            state["needs_clarification"] = False
            
            # Check for missing critical parameters and ask for them
            missing_params = []
            
            if action == "assign_driver":
                if not state.get("target_label") and not state.get("target_trip_id"):
                    missing_params.append("trip identifier")
                # For assign_driver, don't require driver info upfront - let driver_selection_provider handle it
                # This allows "assign driver to this trip" to work without needing specific driver initially
                    
            elif action == "assign_vehicle":
                if not state.get("target_label") and not state.get("target_trip_id"):
                    missing_params.append("trip identifier")
                if not parameters.get("vehicle_registration") and not parameters.get("vehicle_id"):
                    missing_params.append("vehicle registration or ID")
                    
            elif action in ["remove_vehicle", "cancel_trip", "get_trip_status", "get_trip_details"]:
                if not state.get("target_label") and not state.get("target_trip_id"):
                    missing_params.append("trip identifier")
            
            # If critical parameters are missing, ask for them
            if missing_params:
                state["needs_clarification"] = True
                action_verb = action.replace("_", " ")
                missing_str = " and ".join(missing_params)
                state["clarify_options"] = [
                    f"I can {action_verb}, but I need {missing_str}.",
                    "Please specify which trip you're referring to (e.g., 'Bulk - 00:01')",
                    "Try including more details in your request"
                ]
                logger.info(f"[LLM] Missing parameters for {action}: {missing_params}")
        
        logger.info(f"[LLM] Successfully parsed intent: {state['action']}, needs_clarification: {state.get('needs_clarification', False)}")
        
        # OCR CONTEXT PERSISTENCE: Use OCR trip_id for follow-up text commands
        # If from_image=True, the frontend is telling us to use the saved OCR context
        from_image = state.get("from_image", False)
        if selected_trip_id and from_image:
            logger.info(f"[LLM] ✅ Using OCR context trip_id: {selected_trip_id}")
            state["trip_id"] = selected_trip_id
            state["target_trip_id"] = selected_trip_id
            state["needs_clarification"] = False  # We have the trip, no need to clarify
            
            # Clear any "missing trip" clarification if we have OCR context
            if state.get("clarify_options"):
                state["clarify_options"] = []
        elif selected_trip_id and not from_image:
            # UI context (not from OCR) - still use it
            logger.info(f"[LLM] Using UI context trip_id: {selected_trip_id}")
            state["trip_id"] = selected_trip_id
            state["target_trip_id"] = selected_trip_id
        
    except Exception as e:
        logger.error(f"[LLM] Error parsing intent: {e}", exc_info=True)
        
        # Fallback to regex parsing if LLM fails
        logger.info("[LLM] Attempting regex fallback...")
        try:
            from langgraph.nodes.parse_intent import parse_intent
            logger.info("[LLM] Falling back to regex parser due to LLM failure")
            regex_state = await parse_intent(state.copy())
            
            # If regex found something, use it but mark lower confidence
            if regex_state.get("action") != "unknown":
                regex_state["confidence"] = 0.3  # Lower confidence for regex fallback
                regex_state["llm_explanation"] = f"LLM failed ({str(e)}), used regex fallback"
                logger.info(f"[LLM] Regex fallback successful: {regex_state['action']}")
                return regex_state
            
        except Exception as regex_error:
            logger.error(f"[LLM] Regex fallback also failed: {regex_error}")
        
        # Complete fallback to safe state
        state["action"] = "unknown"
        state["error"] = f"parsing_failed"
        state["needs_clarification"] = True
        state["clarify_options"] = [
            "I'm having trouble understanding. Please rephrase your request.",
            "Try using simpler language like 'assign vehicle to [trip name]'",
            "Be more specific about which trip or vehicle you're referring to"
        ]
        state["confidence"] = 0.0
        state["llm_explanation"] = f"Both LLM and regex parsing failed: {str(e)}"
    
    return state


async def parse_structured_command(state: Dict, text: str) -> Dict:
    """
    Parse structured commands from frontend UI selections.
    
    Format: STRUCTURED_CMD:action|param1:value1|param2:value2|...
    Example: STRUCTURED_CMD:assign_driver|trip_id:123|driver_id:456|driver_name:John|context:selection_ui
    
    Args:
        state: Graph state
        text: Structured command text
        
    Returns:
        Updated state with parsed command data
    """
    try:
        # Remove prefix and split by |
        command_data = text[len("structured_cmd:"):].split("|")
        
        # First part is the action
        action = command_data[0].strip()
        
        # Parse parameters
        params = {}
        for param in command_data[1:]:
            if ":" in param:
                key, value = param.split(":", 1)
                params[key.strip()] = value.strip()
        
        logger.info(f"[STRUCTURED] Parsed action: {action}, params: {params}")
        
        # ✅ FIX: Convert numeric parameters from strings to integers
        # This prevents asyncpg "str cannot be interpreted as int" errors
        numeric_fields = ["trip_id", "vehicle_id", "driver_id", "booking_count", "count"]
        for field in numeric_fields:
            if field in params and params[field] is not None and params[field] != "":
                try:
                    params[field] = int(params[field])
                    logger.info(f"[STRUCTURED] Converted {field}: '{params[field]}' → {params[field]} (int)")
                except (ValueError, TypeError) as e:
                    logger.warning(f"[STRUCTURED] Could not convert {field}='{params[field]}' to int: {e}")
        
        logger.info(f"[STRUCTURED] After type conversion: {params}")
        
        # Set state based on parsed data
        state["action"] = action
        state["confidence"] = 1.0  # High confidence for UI selections
        state["llm_explanation"] = f"UI selection: {action} with {len(params)} parameters"
        state["source"] = "structured_command"
        
        # Extract specific parameters (now using converted int values)
        if "trip_id" in params:
            state["selectedTripId"] = params["trip_id"]  # Already converted to int
            state["target_trip_id"] = params["trip_id"]
            state["trip_id"] = params["trip_id"]  # Set trip_id for immediate use
        
        if "driver_id" in params:
            state["selectedEntityId"] = params["driver_id"]  # Already converted to int
            state["entityName"] = params.get("driver_name", "Unknown")
            # Fix: For structured commands, mark as from UI selection to bypass decision_router
            state["from_selection_ui"] = True
            
        if "vehicle_id" in params:
            state["selectedEntityId"] = params["vehicle_id"]  # Already converted to int
            # ✅ FIX: Use registration_number as vehicle_name for proper naming
            state["vehicle_name"] = params.get("vehicle_name", "Unknown")
            state["entityName"] = params.get("vehicle_name", "Unknown")
        
        # Store all params for later use
        state["parsed_params"] = params
        state["needs_clarification"] = False
        state["resolve_result"] = "ready"  # Skip resolution, go directly to action
        
        # For structured commands, ensure we don't go through driver_selection_provider again
        if action == "assign_driver" and "driver_id" in params:
            state["skip_driver_selection"] = True
        
        logger.info(f"✅ [STRUCTURED] Successfully parsed: action={action}, "
                   f"trip_id={params.get('trip_id')}, "
                   f"entity_id={params.get('driver_id', params.get('vehicle_id'))}")
        
        return state
        
    except Exception as e:
        logger.error(f"❌ [STRUCTURED] Failed to parse structured command '{text}': {str(e)}")
        
        # Fallback to normal LLM parsing
        state["action"] = "unknown"
        state["error"] = "structured_command_parse_error"
        state["needs_clarification"] = True
        state["message"] = "Error processing your selection. Please try again."
        
        return state
