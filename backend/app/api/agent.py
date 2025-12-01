"""
Agent API Endpoints
Exposes the LangGraph agent to the frontend
Updated: Force reload for resolve_target fix
"""
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
from langgraph.runtime import runtime

# runtime → THIS is the LangGraph engine that runs our agent graph
# Under the hood:
# Import time is synchronous.
# runtime.run() is async and manages:
# graph execution → node transitions → state updates.

logger = logging.getLogger(__name__)

router = APIRouter()


class AgentMessageRequest(BaseModel):
    """Request model for agent messages"""
    text: str
    user_id: Optional[int] = 1
    session_id: Optional[str] = None
    selectedTripId: Optional[int] = None  # OCR-resolved trip ID
    from_image: Optional[bool] = False  # NEW: Flag to indicate OCR flow
    currentPage: Optional[str] = None
    selectedRouteId: Optional[int] = None
    conversation_history: Optional[list] = []  # NEW: For LLM context
    
    
class AgentConfirmRequest(BaseModel):
    """Request model for confirming an action"""
    session_id: str
    confirmed: bool
    user_id: Optional[int] = 1
    force_delete: Optional[bool] = False  # NEW: Force delete despite dependencies


@router.post("/message")
async def agent_message(request: AgentMessageRequest):
# Please create an HTTP POST endpoint at /message, and when a request comes, run the function agent_message()
    


    """
    Process a natural language message from the user.
    
    Example request:
    ```json
    {
        "text": "Remove vehicle from Bulk - 00:01",
        "user_id": 1
    }
    ```
    
    Example response (needs confirmation):
    ```json
    {
        "agent_output": {
            "action": "remove_vehicle",
            "trip_id": 12,
            "trip_label": "Bulk - 00:01",
            "status": "awaiting_confirmation",
            "needs_confirmation": true,
            "confirmation_required": true,
            "message": "⚠️ This trip has 5 active booking(s) (25% capacity)\\n\\n❓ Do you want to proceed?",
            "consequences": {
                "booking_count": 5,
                "booking_percentage": 25,
                "has_deployment": true
            },
            "success": true
        }
    }
    ```
    
    Example response (executed immediately):
    ```json
    {
        "agent_output": {
            "action": "remove_vehicle",
            "trip_id": 12,
            "status": "executed",
            "message": "Vehicle removed from trip 12",
            "success": true
        }
    }
    ```
    """
    try:
        logger.info(f"Received agent message from user {request.user_id}: {request.text}")
        
        # CRITICAL DEBUG: Log the exact request data received
        logger.info(f"🔥 [API] DEBUGGING REQUEST DATA:")
        logger.info(f"   selectedTripId: {request.selectedTripId}")
        logger.info(f"   currentPage: {request.currentPage}")
        logger.info(f"   selectedRouteId: {request.selectedRouteId}")
        logger.info(f"   from_image: {request.from_image}")
        logger.info(f"   Request model dict: {request.model_dump()}")
        
        # Check if there's an active wizard session
        wizard_state = {}
        conversation_history = []
        if request.session_id:
            from app.core.db import get_conn
            pool = await get_conn()
            async with pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT pending_action, conversation_history FROM agent_sessions 
                    WHERE session_id=$1 AND status='PENDING'
                """, request.session_id)
                
                if row and row["pending_action"]:
                    import json
                    pending_action = json.loads(row["pending_action"]) if isinstance(row["pending_action"], str) else row["pending_action"]
                    
                    # Extract wizard state if present
                    if pending_action.get("wizard_active"):
                        wizard_state = {
                            "wizard_active": True,
                            "wizard_type": pending_action.get("wizard_type"),
                            "wizard_step": pending_action.get("wizard_step", 0),
                            "wizard_data": pending_action.get("wizard_data", {})
                        }
                        logger.info(f"Loaded wizard state: {wizard_state['wizard_type']} at step {wizard_state['wizard_step']}")
                
                # Load conversation history if available
                if row and row.get("conversation_history"):
                    try:
                        stored_history = json.loads(row["conversation_history"]) if isinstance(row["conversation_history"], str) else row["conversation_history"]
                        logger.info(f"Loaded {len(stored_history)} messages from conversation history")
                        conversation_history = stored_history
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse stored conversation history, using empty list")
                        conversation_history = []
        
        # Use conversation history from request if provided, otherwise use stored history
        final_conversation_history = request.conversation_history or conversation_history
        
        # Prepare input state with enhanced UI context
        ui_context = {
            "selectedTripId": request.selectedTripId,
            "selectedRouteId": request.selectedRouteId,
            "selectedPathId": getattr(request, 'selectedPathId', None),
            "currentTrip": None,  # Will be filled by resolve_target if trip found
            "lastAction": None,
            "currentPage": request.currentPage
        }
        
        input_state = {
            "text": request.text,
            "user_id": request.user_id,
            "session_id": request.session_id,
            "selectedTripId": request.selectedTripId,  # Pass OCR-resolved trip ID
            "currentPage": request.currentPage,
            "selectedRouteId": request.selectedRouteId,
            "from_image": request.from_image,  # ✅ Use flag from frontend
            "conversation_history": final_conversation_history,  # Include conversation history
            "ui_context": ui_context,  # Enhanced UI context
            **wizard_state,  # Merge wizard state if exists
        }
        
        # Log if OCR flow detected
        if request.from_image:
            logger.info(f"OCR flow detected (from_image=True). Text length: {len(request.text)} chars")
        
        # Execute the graph
        result_state = await runtime.run(input_state)
        
        # Extract final output
        agent_output = result_state.get("final_output", result_state)
        
        logger.info(
            f"Agent processed message - action: {agent_output.get('action')}, "
            f"status: {agent_output.get('status')}"
        )
        
        # Use session_id from agent output if available (for confirmation flows)
        session_id = agent_output.get("session_id") or request.session_id
        
        # Persist wizard state if wizard is active
        if result_state.get("wizard_active") or result_state.get("status") == "wizard_active":
            import json
            import uuid
            from app.core.db import get_conn
            
            # Create new session_id if none exists
            if not session_id:
                session_id = str(uuid.uuid4())
                logger.info(f"Created new wizard session: {session_id}")
            
            pool = await get_conn()
            async with pool.acquire() as conn:
                wizard_action_data = {
                    "wizard_active": True,
                    "wizard_type": result_state.get("wizard_type"),
                    "wizard_step": result_state.get("wizard_step", 0),
                    "wizard_data": result_state.get("wizard_data", {}),
                    "wizard_steps_total": result_state.get("wizard_steps_total"),
                    "action": result_state.get("action", "wizard_step_input")
                }
                
                await conn.execute("""
                    INSERT INTO agent_sessions (session_id, user_id, status, pending_action, conversation_history, created_at, updated_at)
                    VALUES ($1, $2, 'PENDING', $3, $4, now(), now())
                    ON CONFLICT (session_id) DO UPDATE SET
                        pending_action=$3,
                        conversation_history=$4,
                        status='PENDING',
                        updated_at=now()
                """, session_id, request.user_id, json.dumps(wizard_action_data), json.dumps(final_conversation_history))
                
                logger.info(f"Persisted wizard state for session {session_id}: {wizard_action_data['wizard_type']} at step {wizard_action_data['wizard_step']}")
                
                # Add session_id to agent_output so frontend can track it
                agent_output["session_id"] = session_id
        
        # Clear wizard state if wizard is completed
        elif result_state.get("wizard_completed") and session_id:
            from app.core.db import get_conn
            
            pool = await get_conn()
            async with pool.acquire() as conn:
                # Set pending_action to empty JSON object instead of NULL (column has NOT NULL constraint)
                await conn.execute("""
                    UPDATE agent_sessions 
                    SET status='DONE', pending_action='{}', updated_at=now()
                    WHERE session_id=$1
                """, session_id)
                
                logger.info(f"Cleared wizard state for completed session {session_id}")
        
        return {
            "agent_output": agent_output,
            "session_id": session_id,
        }
        
    except Exception as e:
        logger.error(f"Error processing agent message: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Agent error: {str(e)}"
        )


@router.post("/confirm")
async def agent_confirm(request: AgentConfirmRequest):
    """
    Confirm or reject a pending action.
    
    This endpoint retrieves the pending action from the database,
    executes it if confirmed, and returns the result.
    
    Example request (confirm):
    ```json
    {
        "session_id": "abc-123",
        "confirmed": true,
        "user_id": 1
    }
    ```
    
    Example request (cancel):
    ```json
    {
        "session_id": "abc-123",
        "confirmed": false,
        "user_id": 1
    }
    ```
    """
    try:
        from app.core.supabase_client import get_conn
        from langgraph.tools import (
            tool_cancel_trip, 
            tool_remove_vehicle, 
            tool_remove_driver,
            tool_assign_vehicle,
            tool_assign_driver,
            tool_update_trip_status,
            tool_update_trip_time,
            tool_delay_trip,
            tool_reschedule_trip,
        )
        import json
        
        logger.info(
            f"Received confirmation from user {request.user_id}: "
            f"session={request.session_id}, confirmed={request.confirmed}"
        )
        
        # If user cancelled, just mark session as cancelled
        if not request.confirmed:
            pool = await get_conn()
            async with pool.acquire() as conn:
                await conn.execute("""
                    UPDATE agent_sessions 
                    SET status='CANCELLED', user_response=$1, updated_at=now()
                    WHERE session_id=$2
                """, json.dumps({"confirmed": False}), request.session_id)
            
            return {
                "agent_output": {
                    "status": "cancelled",
                    "success": True,
                    "message": "❌ Action cancelled by user.",
                }
            }
        
        # Retrieve pending action from database
        pool = await get_conn()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT pending_action, status 
                FROM agent_sessions 
                WHERE session_id=$1
            """, request.session_id)
            
            if not row:
                raise HTTPException(
                    status_code=404,
                    detail="Session not found or expired"
                )
            
            if row["status"] != "PENDING":
                raise HTTPException(
                    status_code=400,
                    detail=f"Session is not pending (status: {row['status']})"
                )
            
            # Parse the pending action
            if isinstance(row["pending_action"], str):
                pending_action = json.loads(row["pending_action"])
            else:
                pending_action = row["pending_action"]
            
            action = pending_action.get("action")
            trip_id = pending_action.get("trip_id")
            user_id = pending_action.get("user_id", request.user_id)
            
            logger.info(f"Executing confirmed action: {action} on trip {trip_id}")
            
            # Execute the appropriate tool based on action
            result = None
            if action == "cancel_trip":
                result = await tool_cancel_trip(trip_id, user_id)
            elif action == "remove_vehicle":
                result = await tool_remove_vehicle(trip_id, user_id)
            elif action == "remove_driver":
                result = await tool_remove_driver(trip_id, user_id)
            elif action == "assign_vehicle":
                vehicle_id = pending_action.get("vehicle_id")
                driver_id = pending_action.get("driver_id")
                if vehicle_id and driver_id:
                    result = await tool_assign_vehicle(trip_id, vehicle_id, driver_id, user_id)
                else:
                    result = {
                        "ok": False,
                        "message": "Missing vehicle_id or driver_id for assignment"
                    }
            elif action == "assign_driver":
                driver_id = pending_action.get("driver_id")
                if driver_id:
                    result = await tool_assign_driver(trip_id, driver_id, user_id)
                else:
                    result = {
                        "ok": False,
                        "message": "Missing driver_id for driver assignment"
                    }
            elif action == "update_trip_status":
                new_status = pending_action.get("new_status")
                if new_status:
                    result = await tool_update_trip_status(trip_id, new_status, user_id)
                else:
                    result = {
                        "ok": False,
                        "message": "Missing new_status for status update"
                    }
            elif action == "update_trip_time":
                new_time = pending_action.get("new_time")
                if new_time:
                    result = await tool_update_trip_time(trip_id, new_time, user_id)
                else:
                    result = {
                        "ok": False,
                        "message": "Missing new_time for time update"
                    }
            elif action == "delay_trip":
                delay_minutes = pending_action.get("delay_minutes")
                reason = pending_action.get("reason", "Delayed via agent")
                if delay_minutes:
                    result = await tool_delay_trip(trip_id, delay_minutes, reason)
                else:
                    result = {
                        "ok": False,
                        "message": "Missing delay_minutes for delay"
                    }
            elif action == "reschedule_trip":
                new_time = pending_action.get("new_time")
                new_date = pending_action.get("new_date")
                if new_time or new_date:
                    result = await tool_reschedule_trip(trip_id, new_time, new_date)
                else:
                    result = {
                        "ok": False,
                        "message": "Missing new_time or new_date for reschedule"
                    }
            elif action == "cancel_all_bookings":
                from langgraph.tools import tool_cancel_all_bookings
                reason = pending_action.get("reason", "Cancelled by operator")
                result = await tool_cancel_all_bookings(trip_id, reason, user_id)
            elif action == "delete_stop":
                from app.core.service import delete_stop, list_all_stops
                # Get stop_name with multiple fallbacks
                stop_name = (
                    pending_action.get("stop_name") or 
                    pending_action.get("stop_id") or
                    pending_action.get("llm_parsed", {}).get("target_label")
                )
                logger.info(f"[DELETE_STOP] stop_name={stop_name}, force_delete={request.force_delete}")
                
                if not stop_name:
                    result = {"ok": False, "message": "No stop name specified for deletion"}
                # Resolve name to ID if needed
                elif not isinstance(stop_name, int):
                    stops = await list_all_stops()
                    stop_id = None
                    for stop in stops:
                        if stop.get("stop_name", "").lower() == str(stop_name).lower():
                            stop_id = stop.get("stop_id")  # Fix: use stop_id
                            break
                    if not stop_id:
                        result = {"ok": False, "message": f"Stop '{stop_name}' not found"}
                    else:
                        result = await delete_stop(stop_id, force_delete=request.force_delete)
                else:
                    result = await delete_stop(stop_name, force_delete=request.force_delete)
            elif action == "delete_path":
                from app.core.service import delete_path, list_all_paths
                # Get path_name with multiple fallbacks
                path_name = (
                    pending_action.get("path_name") or 
                    pending_action.get("path_id") or
                    pending_action.get("llm_parsed", {}).get("target_label")
                )
                logger.info(f"[DELETE_PATH] path_name={path_name}, force_delete={request.force_delete}")
                
                if not path_name:
                    result = {"ok": False, "message": "No path name specified for deletion"}
                # Resolve name to ID if needed
                elif not isinstance(path_name, int):
                    paths = await list_all_paths()
                    path_id = None
                    for path in paths:
                        if path.get("path_name", "").lower() == str(path_name).lower():
                            path_id = path.get("path_id")  # Fix: use path_id
                            break
                    if not path_id:
                        result = {"ok": False, "message": f"Path '{path_name}' not found"}
                    else:
                        result = await delete_path(path_id, force_delete=request.force_delete)
                else:
                    result = await delete_path(path_name, force_delete=request.force_delete)
            elif action == "delete_route":
                from app.core.service import delete_route, list_all_routes
                # Get route_name with multiple fallbacks
                route_name = (
                    pending_action.get("route_name") or 
                    pending_action.get("route_id") or
                    pending_action.get("llm_parsed", {}).get("target_label")
                )
                logger.info(f"[DELETE_ROUTE] route_name={route_name}, pending_action keys={list(pending_action.keys())}")
                
                if not route_name:
                    result = {"ok": False, "message": "No route name specified for deletion"}
                # Resolve name to ID if needed
                elif not isinstance(route_name, int):
                    routes = await list_all_routes()
                    route_id = None
                    for route in routes:
                        if route.get("route_name", "").lower() == str(route_name).lower():
                            route_id = route.get("route_id")  # Fix: use route_id not id
                            break
                    if not route_id:
                        result = {"ok": False, "message": f"Route '{route_name}' not found"}
                    else:
                        result = await delete_route(route_id)
                else:
                    result = await delete_route(route_name)
            else:
                result = {
                    "ok": False,
                    "message": f"Unknown action: {action}"
                }
            
            # Update session with execution result
            # If action failed but can be force-deleted, keep session PENDING for retry
            if result.get("can_force_delete") and not result.get("ok"):
                # Keep session PENDING so user can retry with force_delete=True
                await conn.execute("""
                    UPDATE agent_sessions 
                    SET execution_result=$1,
                        updated_at=now()
                    WHERE session_id=$2
                """, 
                    json.dumps(result),
                    request.session_id
                )
            else:
                # Normal case: mark session as DONE
                await conn.execute("""
                    UPDATE agent_sessions 
                    SET status='DONE', 
                        user_response=$1, 
                        execution_result=$2,
                        updated_at=now()
                    WHERE session_id=$3
                """, 
                    json.dumps({"confirmed": True, "force_delete": request.force_delete}),
                    json.dumps(result),
                    request.session_id
                )
            
            # Format response
            trip_label = pending_action.get("trip_label", f"trip {trip_id}")
            
            # Log the result for debugging force-delete flow
            logger.info(f"[CONFIRM] Action result: ok={result.get('ok')}, can_force_delete={result.get('can_force_delete')}, has_deps={bool(result.get('dependent_entities'))}")
            
            if result and result.get("ok"):
                message = f"✅ {result.get('message', 'Action completed successfully')}"
            else:
                message = f"❌ {result.get('message', 'Action failed')}"
            
            response_data = {
                "agent_output": {
                    "status": "executed" if result.get("ok") else "error",
                    "success": result.get("ok", False),
                    "message": message,
                    "action": action,
                    "trip_id": trip_id,
                    "trip_label": trip_label,
                    "execution_result": result,
                }
            }
            
            logger.info(f"[CONFIRM] Returning response with execution_result keys: {list(result.keys()) if result else 'None'}")
            
            return response_data
            
    except Exception as e:
        logger.error(f"Error processing confirmation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Confirmation error: {str(e)}"
        )


@router.get("/health")
async def agent_health():
    """
    Health check for agent service.
    """
    return {
        "status": "healthy",
        "service": "movi_agent",
        "graph_nodes": len(runtime.graph.nodes),
    }
