"""
Get Trip Summary Node
A simple node that fetches and formats a trip summary.

This is a TUTORIAL node to demonstrate how LangGraph nodes work in MOVI.
"""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


async def get_trip_summary(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fetches a quick summary of a trip.
    
    INPUT (from state):
        - trip_id: int - The trip to summarize
        
    OUTPUT (to state):
        - message: str - Formatted summary message
        - final_output: dict - Structured response for frontend
        - next_node: str - Where to go next (report_result)
    
    ROUTING:
        Always routes to "report_result" (terminal node)
    """
    
    # ========== STEP 1: READ FROM STATE ==========
    trip_id = state.get("trip_id")
    
    logger.info(f"[GET_TRIP_SUMMARY] Processing trip_id={trip_id}")
    
    # Validate input
    if not trip_id:
        logger.warning("[GET_TRIP_SUMMARY] No trip_id provided")
        state["error"] = "missing_trip_id"
        state["message"] = "❌ I need a trip ID to get the summary. Please specify which trip."
        state["status"] = "failed"
        state["next_node"] = "report_result"
        return state
    
    # ========== STEP 2: DO THE LOGIC ==========
    try:
        # Import the database function
        from app.core.supabase_client import get_conn
        
        pool = await get_conn()
        async with pool.acquire() as conn:
            # Query trip details
            trip = await conn.fetchrow("""
                SELECT 
                    dt.trip_id,
                    dt.display_name,
                    dt.live_status,
                    dt.trip_date,
                    r.route_name,
                    r.shift_time,
                    d.vehicle_id,
                    d.driver_id,
                    v.registration_number,
                    v.capacity,
                    dr.name as driver_name,
                    COUNT(b.booking_id) FILTER (WHERE b.status = 'CONFIRMED') as booking_count,
                    COALESCE(SUM(b.seats) FILTER (WHERE b.status = 'CONFIRMED'), 0) as seats_booked
                FROM daily_trips dt
                LEFT JOIN routes r ON dt.route_id = r.route_id
                LEFT JOIN deployments d ON dt.trip_id = d.trip_id
                LEFT JOIN vehicles v ON d.vehicle_id = v.vehicle_id
                LEFT JOIN drivers dr ON d.driver_id = dr.driver_id
                LEFT JOIN bookings b ON dt.trip_id = b.trip_id
                WHERE dt.trip_id = $1
                GROUP BY dt.trip_id, dt.display_name, dt.live_status, dt.trip_date,
                         r.route_name, r.shift_time, d.vehicle_id, d.driver_id,
                         v.registration_number, v.capacity, dr.name
            """, trip_id)
        
        # Handle trip not found
        if not trip:
            logger.warning(f"[GET_TRIP_SUMMARY] Trip {trip_id} not found")
            state["error"] = "trip_not_found"
            state["message"] = f"❌ Trip #{trip_id} not found in the system."
            state["status"] = "failed"
            state["next_node"] = "report_result"
            return state
        
        # ========== STEP 3: FORMAT THE RESPONSE ==========
        
        # Build summary message
        display_name = trip["display_name"] or f"Trip #{trip_id}"
        status_emoji = {
            "SCHEDULED": "📅",
            "IN_PROGRESS": "🚌",
            "COMPLETED": "✅",
            "CANCELLED": "❌"
        }.get(trip["live_status"], "❓")
        
        # Format the message
        message_parts = [
            f"**{display_name}** {status_emoji}",
            f"",
            f"📊 **Status**: {trip['live_status']}",
        ]
        
        # Add vehicle info if deployed
        if trip["vehicle_id"]:
            message_parts.append(f"🚗 **Vehicle**: {trip['registration_number']} ({trip['capacity']} seats)")
            message_parts.append(f"👤 **Driver**: {trip['driver_name'] or 'Not assigned'}")
        else:
            message_parts.append(f"🚗 **Vehicle**: Not assigned")
        
        # Add booking info
        booking_count = int(trip["booking_count"] or 0)
        seats_booked = int(trip["seats_booked"] or 0)
        capacity = int(trip["capacity"] or 0)
        
        if capacity > 0:
            percentage = round((seats_booked / capacity) * 100)
            message_parts.append(f"👥 **Bookings**: {booking_count} ({seats_booked}/{capacity} seats - {percentage}%)")
        else:
            message_parts.append(f"👥 **Bookings**: {booking_count} ({seats_booked} seats)")
        
        # Add date/time
        if trip["trip_date"]:
            message_parts.append(f"📅 **Date**: {trip['trip_date']}")
        if trip["shift_time"]:
            message_parts.append(f"⏰ **Time**: {str(trip['shift_time'])[:5]}")
        
        message = "\n".join(message_parts)
        
        logger.info(f"[GET_TRIP_SUMMARY] Successfully summarized trip {trip_id}")
        
        # ========== STEP 4: WRITE TO STATE ==========
        state["message"] = message
        state["status"] = "success"
        state["success"] = True
        
        # Build structured output for frontend
        state["final_output"] = {
            "action": "get_trip_summary",
            "trip_id": trip_id,
            "status": "success",
            "success": True,
            "message": message,
            "data": {
                "trip_id": trip["trip_id"],
                "display_name": display_name,
                "live_status": trip["live_status"],
                "vehicle_id": trip["vehicle_id"],
                "driver_id": trip["driver_id"],
                "registration_number": trip["registration_number"],
                "driver_name": trip["driver_name"],
                "booking_count": booking_count,
                "seats_booked": seats_booked,
                "capacity": capacity
            }
        }
        
        # ========== STEP 5: SET NEXT NODE ==========
        state["next_node"] = "report_result"
        
        return state
        
    except Exception as e:
        logger.error(f"[GET_TRIP_SUMMARY] Error: {e}", exc_info=True)
        state["error"] = "execution_error"
        state["message"] = f"❌ Failed to get trip summary: {str(e)}"
        state["status"] = "failed"
        state["next_node"] = "report_result"
        return state
