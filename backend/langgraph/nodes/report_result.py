"""
Report Result Node
Formats the final output for frontend consumption
"""
from typing import Dict
import logging

logger = logging.getLogger(__name__)


async def report_result(state: Dict) -> Dict:
    """
    Format the final response for the user.
    
    Args:
        state: Complete graph state after processing
        
    Returns:
        State with formatted 'final_output' field
    """
    logger.info("Generating final report")
    
    # Check if execute_action already set final_output (for formatted data like tables)
    existing_formatted_output = state.get("final_output")
    
    # Build comprehensive output
    final_output = {
        "action": state.get("action"),
        "trip_id": state.get("trip_id"),
        "trip_label": state.get("trip_label"),
        "status": state.get("status", "completed"),
        "message": state.get("message", "Action completed successfully."),
        "needs_confirmation": state.get("needs_confirmation", False),
        "confirmation_required": state.get("confirmation_required", False),
        "consequences": state.get("consequences", {}),
        "execution_result": state.get("execution_result", {}),
        "error": state.get("error"),
        "session_id": state.get("session_id"),  # Add session_id for confirmation flow
        
        # NEW: LLM fields
        "llm_explanation": state.get("llm_explanation"),
        "confidence": state.get("confidence"),
        "clarify_options": state.get("clarify_options", []),
        
        # NEW: Suggestions from suggestion_provider node
        "suggestions": state.get("suggestions", []),  # ✅ FIX: Include suggestions in output
        
        # NEW: Options from vehicle_selection_provider node
        "options": state.get("options", []),  # ✅ Vehicle/driver selection options
        "awaiting_selection": state.get("awaiting_selection", False),
        "selection_type": state.get("selection_type"),  # vehicle, driver, etc.
    }
    
    # IMPORTANT: Preserve formatted output from execute_action (tables, lists, objects, help, input_required)
    # Don't nest it - merge it directly into final_output
    if existing_formatted_output and isinstance(existing_formatted_output, dict):
        # If it has a 'type', it's formatted output - add it directly
        if "type" in existing_formatted_output:
            final_output["final_output"] = existing_formatted_output
        else:
            # Otherwise merge all keys
            final_output.update(existing_formatted_output)
    
    # Add pending action details if confirmation is needed
    if state.get("pending_action"):
        final_output["pending_action"] = state["pending_action"]
    
    # Add success indicator
    final_output["success"] = (
        not state.get("error") 
        and (
            state.get("status") == "executed" 
            or state.get("status") == "awaiting_confirmation"
            or state.get("status") == "suggestions_provided"  # ✅ FIX: Suggestions are also a success
            or state.get("status") == "options_provided"  # ✅ FIX: Vehicle options are also a success
            or state.get("status") == "awaiting_input"  # ✅ FIX: Awaiting user input is also a success
            or state.get("status") == "wizard_active"  # ✅ Wizard prompting for input is success
            or state.get("status") == "wizard_step"  # ✅ Wizard step prompting is success
            or state.get("status") == "completed"  # ✅ Completed actions are success
        )
    )
    
    # Add wizard state to output if wizard is active
    if state.get("wizard_active") or state.get("status") == "wizard_active" or state.get("status") == "wizard_step":
        final_output["wizard_active"] = True
        final_output["wizard_type"] = state.get("wizard_type")
        final_output["wizard_step"] = state.get("wizard_step", 0)
        final_output["wizard_steps_total"] = state.get("wizard_steps_total")
        final_output["wizard_data"] = state.get("wizard_data", {})
        final_output["wizard_field"] = state.get("wizard_field")
        final_output["awaiting_wizard_input"] = True
        final_output["success"] = True  # Wizard prompts are successful states
    
    state["final_output"] = final_output
    
    logger.info(
        f"Final report - action: {final_output['action']}, "
        f"status: {final_output['status']}, "
        f"success: {final_output['success']}"
    )
    
    # DEBUG: Log suggestions
    if final_output.get("suggestions"):
        logger.info(f"✅ Including {len(final_output['suggestions'])} suggestions in response")
    else:
        logger.warning(f"⚠️ No suggestions in final_output! state.suggestions = {state.get('suggestions')}")
    
    return state
