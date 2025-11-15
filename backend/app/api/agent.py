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


@router.post("/message")
async def agent_message(request: AgentMessageRequest):
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
        
        # Check if there's an active wizard session
        wizard_state = {}
        if request.session_id:
            from app.core.db import get_conn
            pool = await get_conn()
            async with pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT pending_action FROM agent_sessions 
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
        
        # Prepare input state
        input_state = {
            "text": request.text,
            "user_id": request.user_id,
            "session_id": request.session_id,
            "selectedTripId": request.selectedTripId,  # Pass OCR-resolved trip ID
            "currentPage": request.currentPage,
            "selectedRouteId": request.selectedRouteId,
            "from_image": request.from_image,  # ✅ Use flag from frontend
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
        if result_state.get("wizard_active") and session_id:
            import json
            from app.core.db import get_conn
            
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
                    INSERT INTO agent_sessions (session_id, user_id, status, pending_action, created_at, updated_at)
                    VALUES ($1, $2, 'PENDING', $3, now(), now())
                    ON CONFLICT (session_id) DO UPDATE SET
                        pending_action=$3,
                        status='PENDING',
                        updated_at=now()
                """, session_id, request.user_id, json.dumps(wizard_action_data))
                
                logger.info(f"Persisted wizard state for session {session_id}: {wizard_action_data['wizard_type']} at step {wizard_action_data['wizard_step']}")
        
        # Clear wizard state if wizard is completed
        elif result_state.get("wizard_completed") and session_id:
            from app.core.db import get_conn
            
            pool = await get_conn()
            async with pool.acquire() as conn:
                await conn.execute("""
                    UPDATE agent_sessions 
                    SET status='DONE', pending_action=NULL, updated_at=now()
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
            tool_assign_vehicle
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
            elif action == "assign_vehicle":
                # For assign, we'd need vehicle_id and driver_id from the action
                # This would come from a more detailed confirmation flow
                vehicle_id = pending_action.get("vehicle_id")
                driver_id = pending_action.get("driver_id")
                if vehicle_id and driver_id:
                    result = await tool_assign_vehicle(trip_id, vehicle_id, driver_id, user_id)
                else:
                    result = {
                        "ok": False,
                        "message": "Missing vehicle_id or driver_id for assignment"
                    }
            else:
                result = {
                    "ok": False,
                    "message": f"Unknown action: {action}"
                }
            
            # Update session with execution result
            await conn.execute("""
                UPDATE agent_sessions 
                SET status='DONE', 
                    user_response=$1, 
                    execution_result=$2,
                    updated_at=now()
                WHERE session_id=$3
            """, 
                json.dumps({"confirmed": True}),
                json.dumps(result),
                request.session_id
            )
            
            # Format response
            trip_label = pending_action.get("trip_label", f"trip {trip_id}")
            
            if result and result.get("ok"):
                message = f"✅ {result.get('message', 'Action completed successfully')}"
            else:
                message = f"❌ {result.get('message', 'Action failed')}"
            
            return {
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
