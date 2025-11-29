"""
LLM Client for Intent Parsing
Supports OpenAI, Google Gemini, and Ollama with structured JSON output
"""
import os
import re
import json
import logging
import asyncio
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
import httpx
import google.generativeai as genai

logger = logging.getLogger(__name__)

# System prompt for LLM
SYSTEM_PROMPT = """You are MoviAgent's intelligent intent parser. Parse transport operations commands into structured JSON, understanding natural language, synonyms, and colloquial expressions.

Return ONLY valid JSON following this schema:

{
 "action":"cancel_trip|remove_vehicle|assign_vehicle|assign_driver|assign_vehicle_and_driver|update_trip_time|get_unassigned_vehicles|get_trip_status|get_trip_details|get_trip_summary|list_all_stops|list_stops_for_path|list_routes_using_path|create_stop|create_path|create_route|rename_stop|duplicate_route|create_new_route_help|context_mismatch|unknown",
 "target_label":"string|null",
 "target_time":"HH:MM|null",
 "target_trip_id":int|null,
 "target_path_id":int|null,
 "target_route_id":int|null,
 "parameters":{
   "vehicle_id":int|null,
   "driver_id":int|null,
   "vehicle_registration":"string"|null,
   "driver_name":"string"|null,
   "stop_ids":[int]|null,
   "stop_names":[string]|null,
   "path_stop_order":[int]|null,
   "new_time":"HH:MM"|null,
   "stop_name":"string"|null,
   "latitude":float|null,
   "longitude":float|null,
   "path_name":"string"|null,
   "route_name":"string"|null,
   "passenger_count":int|null
 },
 "confidence":0.0-1.0,
 "clarify":boolean,
 "clarify_options":[string],
 "explanation":"short"
}

**NATURAL LANGUAGE UNDERSTANDING RULES:**

**COMPOUND ACTIONS (Multiple Operations in One Command):**
CRITICAL: When user wants to assign BOTH a vehicle AND a driver in one command, use action="assign_vehicle_and_driver".

Patterns for compound assign:
- "Assign vehicle X and driver Y to trip Z"
- "Put vehicle X with driver Y on this trip"
- "Deploy bus X and driver Y to trip Z"
- "Assign vehicle 'MH-12-7777' and driver 'John Snow' to trip 42"
- "Add vehicle ABC with driver John to the trip"

For assign_vehicle_and_driver:
- Extract vehicle_registration from vehicle identifier (e.g., "MH-12-7777", "Bus 123")
- Extract driver_name from driver identifier (e.g., "John Snow", "Ramesh")
- Extract target_trip_id from trip reference
- Both vehicle AND driver must be mentioned for this action

**CONTEXT-AWARE INTERPRETATION:**
CRITICAL: If the user's message refers to an action on a trip (assign, remove, update, cancel)
and the context includes a selectedTripId, assume the user is referring to that trip 
even if they do NOT explicitly mention "this trip" or provide specific identifiers.

The user may use vague, casual, conversational, or incomplete language including:
- Informal pronouns: "this", "that", "it", "here", "now"  
- Casual commands: "assign", "add driver", "put someone on this"
- Hinglish/mixed language: "driver dal do", "yaha driver add karo"
- Incomplete phrases: "assign", "driver now", "cancel"
- Conversational references: "the current one", "the one showing", "the selected trip"

ALWAYS return target_trip_id when selectedTripId exists in context, unless user explicitly 
mentions another specific trip/route by name or ID.

Support varying English fluency levels. Interpret intent instead of matching exact keywords.

**CONTEXTUAL TARGET RESOLUTION:**
1. If selectedTripId exists in context → Use it as target_trip_id for trip actions, set clarify=false
2. If user says vague references like "this", "that", "it", "here" → Map to selectedTripId, set clarify=false  
3. If user mentions specific trip name/time → Override context and use specific target, set clarify=false
4. If no context and no specific mention → Set clarify=true
5. For structured commands or UI selections → NEVER set clarify=true

VEHICLE ASSIGNMENT - Recognize these patterns as action="assign_vehicle":
- "assign vehicle", "allocate vehicle", "give this trip a vehicle", "put a bus on this"
- "attach vehicle", "deploy vehicle", "set vehicle for", "book vehicle"
- "assign bus", "allocate transport", "provide vehicle", "schedule vehicle"

DRIVER ASSIGNMENT - Recognize these patterns as action="assign_driver":  
- "assign driver", "allocate driver", "give this trip a driver", "put a driver on this"
- "attach driver", "deploy driver", "set driver for", "book driver" 
- "appoint driver", "schedule driver", "add driver to", "connect driver"
- "driver dal do", "yaha driver add karo", "assign", "add someone", "put someone on"

TRIP CANCELLATION - Recognize these patterns as action="cancel_trip":
- "cancel trip", "cancel this", "remove trip", "delete trip"
- "abort trip", "stop trip", "discontinue trip", "kill trip"

VEHICLE REMOVAL - Recognize these patterns as action="remove_vehicle":
- "remove vehicle", "unassign vehicle", "take vehicle off", "detach vehicle" 
- "pull vehicle", "free up vehicle", "disconnect vehicle"

DRIVER REMOVAL - Recognize these patterns as action="remove_driver":
- "remove driver", "unassign driver", "take driver off", "detach driver"
- "pull driver from", "free up driver", "disconnect driver", "remove the driver"

TRIP STATUS UPDATE - Recognize these patterns as action="update_trip_status":
- "update status to", "change status to", "set status to", "mark as"
- "put status to in progress", "make it in progress", "mark completed"
- Valid statuses: SCHEDULED, IN_PROGRESS, COMPLETED, CANCELLED
- Extract the new status as parameters.new_status

DASHBOARD INTELLIGENCE - Recognize these patterns:
- "trips needing attention", "problem trips", "what needs attention" → action="get_trips_needing_attention"
- "today summary", "today's status", "operations summary" → action="get_today_summary"
- "recent changes", "what changed", "last 10 minutes" → action="get_recent_changes"
- "high demand", "busiest office", "most bookings" → action="get_high_demand_offices"
- "most used vehicle", "vehicle usage" → action="get_most_used_vehicles"
- "overbooked trips", "detect overbooking" → action="detect_overbooking"
- "predict problems", "at risk trips" → action="predict_problem_trips"

VEHICLE MANAGEMENT - Recognize these patterns:
- "vehicle status", "show vehicle" → action="get_vehicle_status", extract vehicle_id
- "block vehicle", "disable vehicle" → action="block_vehicle", extract vehicle_id
- "unblock vehicle", "enable vehicle" → action="unblock_vehicle", extract vehicle_id
- "vehicle trips today", "what trips has vehicle" → action="get_vehicle_trips_today"
- "recommend vehicle", "suggest vehicle", "best vehicle" → action="recommend_vehicle_for_trip"
- "suggest alternate vehicle", "alternate vehicle", "replacement vehicle" → action="suggest_alternate_vehicle"
- "list vehicles", "all vehicles", "show all vehicles" → action="list_all_vehicles"
- "show unassigned vehicles", "available vehicles" → action="get_unassigned_vehicles"

DRIVER MANAGEMENT - Recognize these patterns:
- "list drivers", "all drivers", "show all drivers" → action="list_all_drivers"
- "available drivers", "show available drivers" → action="get_available_drivers"
- "driver status", "show driver" → action="get_driver_status", extract driver_id/driver_name
- "driver trips today", "what trips has driver" → action="get_driver_trips_today"
- "set driver available", "driver is available" → action="set_driver_availability", set is_available=true
- "set driver unavailable", "driver not available" → action="set_driver_availability", set is_available=false

PATH/ROUTE LISTING - Recognize these patterns:
- "list paths", "all paths", "show all paths" → action="list_all_paths"
- "list routes", "all routes", "show all routes" → action="list_all_routes"

BOOKING MANAGEMENT - Recognize these patterns:
- "booking count", "how many bookings" → action="get_booking_count"
- "check availability", "seats available", "how many seats", "available seats" → action="check_seat_availability"
- "add booking", "add bookings", "book seats", "increase bookings" → action="add_bookings", extract count
- "add X bookings", "book X passengers", "add X passengers" → action="add_bookings", extract count as booking_count
- "reduce booking", "reduce bookings", "remove bookings", "decrease bookings" → action="reduce_bookings", extract count
- "remove X bookings", "reduce by X", "cancel X bookings" → action="reduce_bookings", extract count as booking_count
- "list passengers", "show passengers", "who is booked" → action="list_passengers"
- "cancel all bookings", "remove all passengers" → action="cancel_all_bookings"
- "find employee", "employee trips", "trips for employee" → action="find_employee_trips", extract employee_name
- "what are the stops", "stops for trip", "stops in trip" → action="get_trip_stops" (available on busDashboard)

TRIP SUMMARY (Tutorial Example) - Recognize these patterns:
- "trip summary", "summarize trip", "give me trip summary", "show summary" → action="get_trip_summary"
- "summary for trip X", "summarize this trip" → action="get_trip_summary", extract trip_id

STOP/PATH/ROUTE MANAGEMENT - Recognize these patterns:
- "delete stop", "remove stop" → action="delete_stop", extract stop_id/stop_name
- "delete path", "remove path" → action="delete_path", extract path_id/path_name
- "delete route", "remove route" → action="delete_route", extract route_id/route_name
- "update path stops", "change path stops" → action="update_path_stops"
- "validate route", "check route" → action="validate_route"

TRIP SCHEDULING - Recognize these patterns:
- "delay trip", "postpone trip" → action="delay_trip", extract trip_id and delay_minutes
- "reschedule trip", "move trip to" → action="reschedule_trip", extract trip_id and new_time/new_date

FLEET MANAGEMENT (Adding NEW Resources) - IMPORTANT DISTINCTION:
These actions are for adding NEW resources to the fleet, NOT assigning to trips:
- "add driver John Smith", "create driver", "new driver", "register driver", "add driver named X" → action="add_driver"
- "add vehicle TN01AB1234", "create vehicle", "new vehicle", "register vehicle", "add vehicle with registration X" → action="add_vehicle"

CRITICAL: Distinguish between:
1. "add driver John Smith" (no trip context) → action="add_driver" (CREATE new driver in fleet)
2. "add driver to trip X", "assign driver to this trip" (has trip context) → action="assign_driver" (ASSIGN existing driver)

When user says "add driver [name]" WITHOUT mentioning any trip, it means CREATE a new driver, use add_driver.
When user says "add driver to [trip]" or has selectedTripId context, it means ASSIGN driver to trip, use assign_driver.

SMART AUTOMATION - Recognize these patterns:
- "can this trip run", "is trip ready", "check readiness" → action="check_trip_readiness"
- "simulate", "what would happen if" → action="simulate_action"
- "explain", "why did you", "explain decision" → action="explain_decision"

**PARAMETER EXTRACTION:**
- If user mentions driver name (e.g., "John", "Smith", "John Smith"), extract as driver_name
- If user mentions vehicle info (e.g., "Bus 123", "Vehicle ABC"), extract as vehicle_registration
- Always extract trip identifiers as target_label (e.g., "Bulk - 00:01", "Downtown Express")
- Extract times in HH:MM format as target_time
- For status updates, extract the target status as new_status (e.g., "IN_PROGRESS", "COMPLETED")

**CONFIDENCE GUIDELINES:**
- High confidence (0.9+): Clear action words + context (selectedTripId) OR specific targets
- Medium confidence (0.7-0.9): Clear action with partial targets
- Low confidence (0.4-0.7): Unclear action or very ambiguous
- Request clarification (clarify=true) ONLY if confidence < 0.6 AND no selectedTripId context

**CLARIFICATION STRATEGY:**
When missing critical information AND no context, set clarify=true and provide helpful options:
- Missing trip (no selectedTripId): "Which trip are you referring to? Please specify the route name and time."
- For assign_driver with selectedTripId: NEVER clarify - set confidence 0.9 (driver_selection_provider will handle driver choice)
- Missing vehicle: "Which vehicle should be assigned? Please specify the vehicle ID or registration."
- Ambiguous action: Provide multiple interpretations as clarify_options

**SPECIAL CASE: OCR-Extracted Trip Information**
When you receive text that looks like OCR output from a trip card/screen (contains trip ID, route name, status, etc.):
- Look for "ID Trip #X" or "Trip #X" patterns → extract as target_trip_id
- Look for route name patterns like "Path-1 - 08:00" → extract as target_label
- Look for time patterns like "08:00" → extract as target_time
- Default action to "get_trip_details" if no specific action is mentioned
- Set confidence to 0.85+ if trip ID is found
- DO NOT return "unknown" if you can extract trip information

Example OCR input:
"Path-1 - 08:00
ID Trip #1
Status: SCHEDULED
Vehicle: Unassigned
Bookings: 5"

Should parse as:
{
  "action": "get_trip_details",
  "target_label": "Path-1 - 08:00",
  "target_time": "08:00",
  "target_trip_id": 1,
  "confidence": 0.90,
  "explanation": "OCR-extracted trip information for Trip #1"
}

CONTEXT-AWARE RULES (CRITICAL):
You MUST enforce page context ONLY when currentPage is explicitly provided.

**IMPORTANT**: If currentPage is null/unknown/not provided, DO NOT return context_mismatch. Parse the action normally.

=== BUS DASHBOARD PAGE ACTIONS (currentPage="busDashboard") - 40 Actions ===

A. Trip Management (10 actions):
- assign_vehicle, assign_driver, remove_vehicle, remove_driver
- cancel_trip, update_trip_time, update_trip_status, delay_trip
- reschedule_trip, get_trip_details

B. Vehicle Management (8 actions):
- list_all_vehicles, get_unassigned_vehicles, get_vehicle_status
- get_vehicle_trips_today, block_vehicle, unblock_vehicle
- add_vehicle, recommend_vehicle_for_trip

C. Driver Management (7 actions):
- list_all_drivers, get_available_drivers, get_driver_status
- get_driver_trips_today, set_driver_availability
- add_driver, suggest_alternate_vehicle

D. Booking Management (4 actions):
- get_booking_count, list_passengers, cancel_all_bookings, find_employee_trips

E. Dashboard Intelligence (7 actions):
- get_trips_needing_attention, get_today_summary, get_recent_changes
- get_high_demand_offices, get_most_used_vehicles, detect_overbooking
- predict_problem_trips

F. Automation & Insights (4 actions):
- check_trip_readiness, simulate_action, explain_decision, get_trip_status

If user requests MANAGE ROUTE actions on busDashboard → return action="context_mismatch" with explanation.

=== MANAGE ROUTE PAGE ACTIONS (currentPage="manageRoute") - 15 Actions ===

A. Stop/Path/Route Configuration (11 actions):
- list_all_stops, list_all_paths, list_all_routes
- list_stops_for_path, list_routes_using_path
- create_stop, create_path, create_route
- rename_stop, duplicate_route, validate_route

B. Delete Operations (3 actions):
- delete_stop, delete_path, delete_route

C. Path Management (1 action):
- update_path_stops

Helper: create_new_route_help (manageRoute only)

If user requests DASHBOARD actions on manageRoute → return action="context_mismatch" with explanation.

Examples of context_mismatch:
- User on busDashboard asks "create a route" → action="context_mismatch", explanation="Route creation is only available on Manage Route page. Please navigate to Manage Route."
- User on busDashboard asks "delete route X" → action="context_mismatch", explanation="Route deletion is only available on Manage Route page. Please navigate to Manage Route."
- User on busDashboard asks "create stop X" → action="context_mismatch", explanation="Stop creation is only available on Manage Route page. Please navigate to Manage Route."
- User on manageRoute asks "cancel trip" → action="context_mismatch", explanation="Trip operations are only available on Dashboard. Please navigate to Dashboard."
- User on manageRoute asks "assign vehicle" → action="context_mismatch", explanation="Vehicle assignments are only available on Dashboard. Please navigate to Dashboard."

Other Rules:
- Never guess trip_id/path_id/route_id; allow DB to verify.
- If unsure, set clarify=true and provide clarify_options.
- If user refers generically, provide multiple possible labels.
- Use currentPage context: busDashboard=trip actions, manageRoute=route/path/stop actions.
- DO NOT execute actions; only parse intent.
- Respond ONLY with JSON and nothing else."""

# Few-shot examples (covering all 16 actions)
FEW_SHOT_EXAMPLES = [
    # OCR-EXTRACTED TRIP INFORMATION
    {
        "user": "Path-1 - 08:00\nID Trip #1\n2025-11-11\nStatus: SCHEDULED\nVehicle: Unassigned\nBookings: 5",
        "assistant": '{"action":"get_trip_details","target_label":"Path-1 - 08:00","target_time":"08:00","target_trip_id":1,"target_path_id":null,"target_route_id":null,"parameters":{},"confidence":0.90,"clarify":false,"clarify_options":[],"explanation":"OCR-extracted trip information for Trip #1"}'
    },
    {
        "user": "Path-3 - 07:30\nTrip #5\nStatus: IN PROGRESS\nVehicle: MH-12-AB-1234\nDriver: John Doe",
        "assistant": '{"action":"get_trip_details","target_label":"Path-3 - 07:30","target_time":"07:30","target_trip_id":5,"target_path_id":null,"target_route_id":null,"parameters":{},"confidence":0.92,"clarify":false,"clarify_options":[],"explanation":"OCR-extracted trip information for Trip #5"}'
    },
    
    # DYNAMIC READ
    {
        "user": "Show me available vehicles",
        "assistant": '{"action":"get_unassigned_vehicles","target_label":null,"target_time":null,"target_trip_id":null,"target_path_id":null,"target_route_id":null,"parameters":{},"confidence":0.95,"clarify":false,"clarify_options":[],"explanation":"User wants to see unassigned vehicles"}'
    },
    {
        "user": "What is the status of Path-3 - 07:30",
        "assistant": '{"action":"get_trip_status","target_label":"Path-3 - 07:30","target_time":"07:30","target_trip_id":null,"target_path_id":null,"target_route_id":null,"parameters":{},"confidence":0.90,"clarify":false,"clarify_options":[],"explanation":"User wants trip status"}'
    },
    {
        "user": "Get details for trip 5",
        "assistant": '{"action":"get_trip_details","target_label":null,"target_time":null,"target_trip_id":5,"target_path_id":null,"target_route_id":null,"parameters":{},"confidence":0.95,"clarify":false,"clarify_options":[],"explanation":"User wants detailed trip information"}'
    },
    
    # STATIC READ
    {
        "user": "List all stops",
        "assistant": '{"action":"list_all_stops","target_label":null,"target_time":null,"target_trip_id":null,"target_path_id":null,"target_route_id":null,"parameters":{},"confidence":0.98,"clarify":false,"clarify_options":[],"explanation":"User wants to see all stops"}'
    },
    {
        "user": "Show stops for Path-3",
        "assistant": '{"action":"list_stops_for_path","target_label":"Path-3","target_time":null,"target_trip_id":null,"target_path_id":null,"target_route_id":null,"parameters":{},"confidence":0.92,"clarify":false,"clarify_options":[],"explanation":"User wants stops on Path-3"}'
    },
    {
        "user": "Which routes use Jayanagar path",
        "assistant": '{"action":"list_routes_using_path","target_label":"Jayanagar","target_time":null,"target_trip_id":null,"target_path_id":null,"target_route_id":null,"parameters":{},"confidence":0.88,"clarify":false,"clarify_options":[],"explanation":"User wants routes using specific path"}'
    },
    
    # DYNAMIC MUTATE
    {
        "user": "Cancel Path-3 - 07:30",
        "assistant": '{"action":"cancel_trip","target_label":"Path-3 - 07:30","target_time":"07:30","target_trip_id":null,"target_path_id":null,"target_route_id":null,"parameters":{},"confidence":0.95,"clarify":false,"clarify_options":[],"explanation":"User wants to cancel specific trip"}'
    },
    {
        "user": "Remove vehicle from trip 5",
        "assistant": '{"action":"remove_vehicle","target_label":null,"target_time":null,"target_trip_id":5,"target_path_id":null,"target_route_id":null,"parameters":{},"confidence":0.90,"clarify":false,"clarify_options":[],"explanation":"User wants to remove vehicle from trip"}'
    },
    {
        "user": "Assign bus 8 driver 3 to Bulk - 00:01",
        "assistant": '{"action":"assign_vehicle_and_driver","target_label":"Bulk - 00:01","target_time":"00:01","target_trip_id":null,"target_path_id":null,"target_route_id":null,"parameters":{"vehicle_id":8,"driver_id":3},"confidence":0.92,"clarify":false,"clarify_options":[],"explanation":"User wants to assign both vehicle and driver to trip"}'
    },
    {
        "user": "Assign vehicle MH-12-3456 and driver Amit to trip 5",
        "assistant": '{"action":"assign_vehicle_and_driver","target_label":null,"target_time":null,"target_trip_id":5,"target_path_id":null,"target_route_id":null,"parameters":{"vehicle_registration":"MH-12-3456","driver_name":"Amit"},"confidence":0.92,"clarify":false,"clarify_options":[],"explanation":"User wants to assign both vehicle and driver to trip"}'
    },
    {
        "user": "Assign vehicle 'MH-12-7777' and driver 'John Snow' to trip 42",
        "assistant": '{"action":"assign_vehicle_and_driver","target_label":null,"target_time":null,"target_trip_id":42,"target_path_id":null,"target_route_id":null,"parameters":{"vehicle_registration":"MH-12-7777","driver_name":"John Snow"},"confidence":0.95,"clarify":false,"clarify_options":[],"explanation":"User wants to assign both vehicle and driver to specific trip"}'
    },
    {
        "user": "Assign driver John to Downtown - 14:30",
        "assistant": '{"action":"assign_driver","target_label":"Downtown - 14:30","target_time":"14:30","target_trip_id":null,"target_path_id":null,"target_route_id":null,"parameters":{"driver_name":"John"},"confidence":0.90,"clarify":false,"clarify_options":[],"explanation":"User wants to assign specific driver to trip"}'
    },
    {
        "user": "Put driver Sarah on trip 8",
        "assistant": '{"action":"assign_driver","target_label":null,"target_time":null,"target_trip_id":8,"target_path_id":null,"target_route_id":null,"parameters":{"driver_name":"Sarah"},"confidence":0.88,"clarify":false,"clarify_options":[],"explanation":"User wants to assign driver Sarah to specific trip"}'
    },
    {
        "user": "Appoint driver 5 to Bulk - 00:01",
        "assistant": '{"action":"assign_driver","target_label":"Bulk - 00:01","target_time":"00:01","target_trip_id":null,"target_path_id":null,"target_route_id":null,"parameters":{"driver_id":5},"confidence":0.92,"clarify":false,"clarify_options":[],"explanation":"User wants to assign driver by ID to trip"}'
    },
    {
        "user": "Allocate a driver to this trip",
        "assistant": '{"action":"assign_driver","target_label":null,"target_time":null,"target_trip_id":null,"target_path_id":null,"target_route_id":null,"parameters":{},"confidence":0.75,"clarify":true,"clarify_options":["Which trip are you referring to?","Please specify the driver name or ID"],"explanation":"User wants to assign driver but missing trip and driver details"}'
    },
    {
        "user": "Change Path-1 - 08:00 to 09:00",
        "assistant": '{"action":"update_trip_time","target_label":"Path-1 - 08:00","target_time":"08:00","target_trip_id":null,"target_path_id":null,"target_route_id":null,"parameters":{"new_time":"09:00"},"confidence":0.90,"clarify":false,"clarify_options":[],"explanation":"User wants to update departure time"}'
    },
    
    # STATIC MUTATE
    {
        "user": "Create a new stop called MG Road",
        "assistant": '{"action":"create_stop","target_label":null,"target_time":null,"target_trip_id":null,"target_path_id":null,"target_route_id":null,"parameters":{"stop_name":"MG Road","latitude":null,"longitude":null},"confidence":0.95,"clarify":false,"clarify_options":[],"explanation":"User wants to create new stop without coordinates"}'
    },
    {
        "user": "Create a new stop called Brigade Road at 12.9716, 77.5946",
        "assistant": '{"action":"create_stop","target_label":null,"target_time":null,"target_trip_id":null,"target_path_id":null,"target_route_id":null,"parameters":{"stop_name":"Brigade Road","latitude":12.9716,"longitude":77.5946},"confidence":0.95,"clarify":false,"clarify_options":[],"explanation":"User wants to create new stop with coordinates"}'
    },
    {
        "user": "Create path Downtown with stops MG Road, Brigade Road, Commercial Street",
        "assistant": '{"action":"create_path","target_label":null,"target_time":null,"target_trip_id":null,"target_path_id":null,"target_route_id":null,"parameters":{"path_name":"Downtown","stop_names":["MG Road","Brigade Road","Commercial Street"]},"confidence":0.88,"clarify":false,"clarify_options":[],"explanation":"User wants to create path with specific stops"}'
    },
    {
        "user": "Create route Express-1 using Path-3",
        "assistant": '{"action":"create_route","target_label":"Path-3","target_time":null,"target_trip_id":null,"target_path_id":null,"target_route_id":null,"parameters":{"route_name":"Express-1"},"confidence":0.90,"clarify":false,"clarify_options":[],"explanation":"User wants to create route with path"}'
    },
    {
        "user": "Rename Koramangala stop to Koramangala Metro",
        "assistant": '{"action":"rename_stop","target_label":"Koramangala","target_time":null,"target_trip_id":null,"target_path_id":null,"target_route_id":null,"parameters":{"stop_name":"Koramangala Metro"},"confidence":0.92,"clarify":false,"clarify_options":[],"explanation":"User wants to rename stop"}'
    },
    {
        "user": "Duplicate Path-3 route",
        "assistant": '{"action":"duplicate_route","target_label":"Path-3","target_time":null,"target_trip_id":null,"target_path_id":null,"target_route_id":null,"parameters":{},"confidence":0.88,"clarify":false,"clarify_options":[],"explanation":"User wants to copy existing route"}'
    },
    
    # FLEET MANAGEMENT
    {
        "user": "Add a new vehicle KA01MV5678",
        "assistant": '{"action":"add_vehicle","target_label":null,"target_time":null,"target_trip_id":null,"target_path_id":null,"target_route_id":null,"parameters":{"registration_number":"KA01MV5678","vehicle_type":"BUS","capacity":40},"confidence":0.95,"clarify":false,"clarify_options":[],"explanation":"User wants to add a new vehicle"}'
    },
    {
        "user": "Add driver John Smith with phone 9876543210",
        "assistant": '{"action":"add_driver","target_label":null,"target_time":null,"target_trip_id":null,"target_path_id":null,"target_route_id":null,"parameters":{"driver_name":"John Smith","phone":"9876543210"},"confidence":0.95,"clarify":false,"clarify_options":[],"explanation":"User wants to add a new driver"}'
    },
    {
        "user": "Delay trip 5 by 30 minutes",
        "assistant": '{"action":"delay_trip","target_label":null,"target_time":null,"target_trip_id":5,"target_path_id":null,"target_route_id":null,"parameters":{"delay_minutes":30},"confidence":0.95,"clarify":false,"clarify_options":[],"explanation":"User wants to delay a trip"}'
    },
    {
        "user": "Reschedule trip 3 to 14:00",
        "assistant": '{"action":"reschedule_trip","target_label":null,"target_time":null,"target_trip_id":3,"target_path_id":null,"target_route_id":null,"parameters":{"new_time":"14:00"},"confidence":0.95,"clarify":false,"clarify_options":[],"explanation":"User wants to reschedule a trip to new time"}'
    },
    {
        "user": "Show all paths",
        "assistant": '{"action":"list_all_paths","target_label":null,"target_time":null,"target_trip_id":null,"target_path_id":null,"target_route_id":null,"parameters":{},"confidence":0.95,"clarify":false,"clarify_options":[],"explanation":"User wants to see all paths"}'
    },
    {
        "user": "List all routes",
        "assistant": '{"action":"list_all_routes","target_label":null,"target_time":null,"target_trip_id":null,"target_path_id":null,"target_route_id":null,"parameters":{},"confidence":0.95,"clarify":false,"clarify_options":[],"explanation":"User wants to see all routes"}'
    },
    {
        "user": "Show all vehicles",
        "assistant": '{"action":"list_all_vehicles","target_label":null,"target_time":null,"target_trip_id":null,"target_path_id":null,"target_route_id":null,"parameters":{},"confidence":0.95,"clarify":false,"clarify_options":[],"explanation":"User wants to see all vehicles"}'
    },
    {
        "user": "List all drivers",
        "assistant": '{"action":"list_all_drivers","target_label":null,"target_time":null,"target_trip_id":null,"target_path_id":null,"target_route_id":null,"parameters":{},"confidence":0.95,"clarify":false,"clarify_options":[],"explanation":"User wants to see all drivers"}'
    },
    {
        "user": "Add a new driver named Ramesh with phone 9876543210",
        "assistant": '{"action":"add_driver","target_label":null,"target_time":null,"target_trip_id":null,"target_path_id":null,"target_route_id":null,"parameters":{"driver_name":"Ramesh","phone":"9876543210"},"confidence":0.95,"clarify":false,"clarify_options":[],"explanation":"User wants to add a new driver"}'
    },
    {
        "user": "Create driver John Smith",
        "assistant": '{"action":"add_driver","target_label":null,"target_time":null,"target_trip_id":null,"target_path_id":null,"target_route_id":null,"parameters":{"driver_name":"John Smith"},"confidence":0.95,"clarify":false,"clarify_options":[],"explanation":"User wants to add a new driver"}'
    },
    # CRITICAL DISAMBIGUATION: "add driver X" without trip context = CREATE driver
    {
        "user": "Add driver Suresh",
        "assistant": '{"action":"add_driver","target_label":null,"target_time":null,"target_trip_id":null,"target_path_id":null,"target_route_id":null,"parameters":{"driver_name":"Suresh"},"confidence":0.95,"clarify":false,"clarify_options":[],"explanation":"User wants to add new driver to fleet (no trip mentioned, so creating driver)"}'
    },
    {
        "user": "Add vehicle KA01AB1234",
        "assistant": '{"action":"add_vehicle","target_label":null,"target_time":null,"target_trip_id":null,"target_path_id":null,"target_route_id":null,"parameters":{"registration_number":"KA01AB1234"},"confidence":0.95,"clarify":false,"clarify_options":[],"explanation":"User wants to add a new vehicle"}'
    },
    {
        "user": "Create new vehicle MH12XY5678 with capacity 30",
        "assistant": '{"action":"add_vehicle","target_label":null,"target_time":null,"target_trip_id":null,"target_path_id":null,"target_route_id":null,"parameters":{"registration_number":"MH12XY5678","capacity":30},"confidence":0.95,"clarify":false,"clarify_options":[],"explanation":"User wants to add a new vehicle with specific capacity"}'
    },
    
    # HELPER
    {
        "user": "Help me create a new route",
        "assistant": '{"action":"create_new_route_help","target_label":null,"target_time":null,"target_trip_id":null,"target_path_id":null,"target_route_id":null,"parameters":{},"confidence":0.98,"clarify":false,"clarify_options":[],"explanation":"User needs guidance for route creation"}'
    },
    
    # PHASE 3: CONVERSATIONAL ACTIONS
    {
        "user": "What can I do with this trip?",
        "assistant": '{"action":"show_trip_suggestions","target_label":null,"target_time":null,"target_trip_id":null,"target_path_id":null,"target_route_id":null,"parameters":{},"confidence":0.95,"clarify":false,"clarify_options":[],"explanation":"User wants to see available actions"}'
    },
    {
        "user": "Help me create a new trip",
        "assistant": '{"action":"create_trip_from_scratch","target_label":null,"target_time":null,"target_trip_id":null,"target_path_id":null,"target_route_id":null,"parameters":{},"confidence":0.95,"clarify":false,"clarify_options":[],"explanation":"User wants guided trip creation"}'
    },
    {
        "user": "Show me bookings for trip 5",
        "assistant": '{"action":"get_trip_bookings","target_label":null,"target_time":null,"target_trip_id":5,"target_path_id":null,"target_route_id":null,"parameters":{},"confidence":0.90,"clarify":false,"clarify_options":[],"explanation":"User wants to view trip bookings"}'
    },
    {
        "user": "Change the driver for this trip",
        "assistant": '{"action":"change_driver","target_label":null,"target_time":null,"target_trip_id":null,"target_path_id":null,"target_route_id":null,"parameters":{},"confidence":0.85,"clarify":false,"clarify_options":[],"explanation":"User wants to reassign driver"}'
    },
    {
        "user": "Copy trip 3 for tomorrow",
        "assistant": '{"action":"duplicate_trip","target_label":null,"target_time":null,"target_trip_id":3,"target_path_id":null,"target_route_id":null,"parameters":{"date":"tomorrow"},"confidence":0.88,"clarify":false,"clarify_options":[],"explanation":"User wants to duplicate existing trip"}'
    },
    {
        "user": "08:30",
        "assistant": '{"action":"wizard_step_input","target_label":null,"target_time":"08:30","target_trip_id":null,"target_path_id":null,"target_route_id":null,"parameters":{"value":"08:30"},"confidence":0.98,"clarify":false,"clarify_options":[],"explanation":"User providing wizard input (time)"}'
    },
    
    # VEHICLE RECOMMENDATION WITH PASSENGER COUNT
    {
        "user": "Suggest a vehicle for trip 10",
        "assistant": '{"action":"recommend_vehicle_for_trip","target_label":null,"target_time":null,"target_trip_id":10,"target_path_id":null,"target_route_id":null,"parameters":{},"confidence":0.95,"clarify":false,"clarify_options":[],"explanation":"User wants vehicle recommendations for trip"}'
    },
    {
        "user": "I need a vehicle for 25 passengers for trip 10",
        "assistant": '{"action":"recommend_vehicle_for_trip","target_label":null,"target_time":null,"target_trip_id":10,"target_path_id":null,"target_route_id":null,"parameters":{"passenger_count":25},"confidence":0.95,"clarify":false,"clarify_options":[],"explanation":"User wants vehicle with capacity for 25 passengers"}'
    },
    {
        "user": "25 passengers",
        "assistant": '{"action":"recommend_vehicle_for_trip","target_label":null,"target_time":null,"target_trip_id":null,"target_path_id":null,"target_route_id":null,"parameters":{"passenger_count":25},"confidence":0.95,"clarify":false,"clarify_options":[],"explanation":"User providing passenger count for vehicle recommendation"}'
    },
    {
        "user": "30",
        "assistant": '{"action":"recommend_vehicle_for_trip","target_label":null,"target_time":null,"target_trip_id":null,"target_path_id":null,"target_route_id":null,"parameters":{"passenger_count":30},"confidence":0.90,"clarify":false,"clarify_options":[],"explanation":"User providing passenger count (just a number)"}'
    },
    {
        "user": "Find a bus for 40 people",
        "assistant": '{"action":"recommend_vehicle_for_trip","target_label":null,"target_time":null,"target_trip_id":null,"target_path_id":null,"target_route_id":null,"parameters":{"passenger_count":40},"confidence":0.95,"clarify":false,"clarify_options":[],"explanation":"User wants vehicle for 40 passengers"}'
    },
    
    # CONTEXT MISMATCH - Dashboard-only actions on wrong page
    {
        "user": "Context: busDashboard | Help me create a new route",
        "assistant": '{"action":"context_mismatch","target_label":null,"target_time":null,"target_trip_id":null,"target_path_id":null,"target_route_id":null,"parameters":{},"confidence":0.95,"clarify":false,"clarify_options":[],"explanation":"Route creation is only available on Manage Route page. Please switch to Manage Route."}'
    },
    {
        "user": "Context: manageRoute | Cancel the Bulk - 00:01 trip",
        "assistant": '{"action":"context_mismatch","target_label":null,"target_time":null,"target_trip_id":null,"target_path_id":null,"target_route_id":null,"parameters":{},"confidence":0.95,"clarify":false,"clarify_options":[],"explanation":"Trip cancellations are only available on Dashboard. Please switch to Dashboard."}'
    },
    {
        "user": "Context: busDashboard | Create a new stop called Odeon Circle",
        "assistant": '{"action":"context_mismatch","target_label":null,"target_time":null,"target_trip_id":null,"target_path_id":null,"target_route_id":null,"parameters":{},"confidence":0.95,"clarify":false,"clarify_options":[],"explanation":"Stop creation is only available on Manage Route page. Please switch to Manage Route."}'
    },
    {
        "user": "Context: manageRoute | Remove vehicle from trip 5",
        "assistant": '{"action":"context_mismatch","target_label":null,"target_time":null,"target_trip_id":null,"target_path_id":null,"target_route_id":null,"parameters":{},"confidence":0.95,"clarify":false,"clarify_options":[],"explanation":"Vehicle management is only available on Dashboard. Please switch to Dashboard."}'
    },
    # DELETE OPERATIONS - ManageRoute only
    {
        "user": "Context: busDashboard | Delete route Morning Route",
        "assistant": '{"action":"context_mismatch","target_label":null,"target_time":null,"target_trip_id":null,"target_path_id":null,"target_route_id":null,"parameters":{},"confidence":0.95,"clarify":false,"clarify_options":[],"explanation":"Route deletion is only available on Manage Route page. Please navigate to Manage Route to delete routes."}'
    },
    {
        "user": "Context: busDashboard | Delete path Path-1",
        "assistant": '{"action":"context_mismatch","target_label":null,"target_time":null,"target_trip_id":null,"target_path_id":null,"target_route_id":null,"parameters":{},"confidence":0.95,"clarify":false,"clarify_options":[],"explanation":"Path deletion is only available on Manage Route page. Please navigate to Manage Route to delete paths."}'
    },
    {
        "user": "Context: busDashboard | Delete stop Central Station",
        "assistant": '{"action":"context_mismatch","target_label":null,"target_time":null,"target_trip_id":null,"target_path_id":null,"target_route_id":null,"parameters":{},"confidence":0.95,"clarify":false,"clarify_options":[],"explanation":"Stop deletion is only available on Manage Route page. Please navigate to Manage Route to delete stops."}'
    },
    # DELETE OPERATIONS - Correct page (manageRoute)
    {
        "user": "Context: manageRoute | Delete route Morning Route",
        "assistant": '{"action":"delete_route","target_label":null,"target_time":null,"target_trip_id":null,"target_path_id":null,"target_route_id":null,"parameters":{"route_name":"Morning Route"},"confidence":0.95,"clarify":false,"clarify_options":[],"explanation":"User wants to delete Morning Route"}'
    },
    {
        "user": "Context: manageRoute | Delete path Path-1",
        "assistant": '{"action":"delete_path","target_label":null,"target_time":null,"target_trip_id":null,"target_path_id":null,"target_route_id":null,"parameters":{"path_name":"Path-1"},"confidence":0.95,"clarify":false,"clarify_options":[],"explanation":"User wants to delete Path-1"}'
    },
    {
        "user": "Context: manageRoute | Delete stop Central Station",
        "assistant": '{"action":"delete_stop","target_label":null,"target_time":null,"target_trip_id":null,"target_path_id":null,"target_route_id":null,"parameters":{"stop_name":"Central Station"},"confidence":0.95,"clarify":false,"clarify_options":[],"explanation":"User wants to delete Central Station stop"}'
    },
]


def _get_llm_config() -> Dict[str, Any]:
    """Get LLM configuration from environment"""
    return {
        "provider": os.getenv("LLM_PROVIDER", "openai").lower(),
        "model": os.getenv("LLM_MODEL", "gpt-4o-mini"),
        "timeout": int(os.getenv("LLM_TIMEOUT_SECONDS", "10")),
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "gemini_api_key": os.getenv("GEMINI_API_KEY"),
        "ollama_base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    }


def _validate_llm_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and normalize LLM response to ensure it matches expected schema
    """
    required_fields = ["action", "confidence", "clarify", "explanation"]
    for field in required_fields:
        if field not in response:
            raise ValueError(f"Missing required field: {field}")
    
    # Define centralized action registry for easier maintenance
    ACTION_REGISTRY = {
        # Dynamic READ actions
        "read_dynamic": [
            "get_unassigned_vehicles", "get_available_drivers", "get_trip_status", "get_trip_details",
            "get_booking_count", "get_trip_stops", "list_passengers", "get_vehicle_status",
            "get_driver_status", "get_vehicle_trips_today", "get_driver_trips_today",
            "find_employee_trips", "check_trip_readiness", "get_bookings"
        ],
        # Static READ actions  
        "read_static": [
            "list_all_stops", "list_stops_for_path", "list_routes_using_path",
            "validate_route", "list_all_paths", "get_all_paths", "list_all_routes", 
            "get_all_routes", "list_all_vehicles", "get_vehicles", "list_all_drivers", "get_drivers"
        ],
        # Dashboard/Analytics READ actions
        "read_analytics": [
            "get_trips_needing_attention", "get_today_summary", "get_recent_changes",
            "get_high_demand_offices", "get_most_used_vehicles", "detect_overbooking",
            "predict_problem_trips"
        ],
        # Dynamic MUTATE actions
        "mutate_dynamic": [
            "cancel_trip", "remove_vehicle", "remove_driver", "assign_vehicle", "assign_driver", 
            "assign_vehicle_and_driver",  # Compound action for assigning both
            "update_trip_time", "update_trip_status", "cancel_all_bookings",
            "block_vehicle", "unblock_vehicle", "set_driver_availability",
            "delay_trip", "reschedule_trip"
        ],
        # Static MUTATE actions
        "mutate_static": [
            "create_stop", "create_path", "create_route", "rename_stop", "duplicate_route",
            "delete_stop", "delete_path", "delete_route", "update_path_stops",
            "add_vehicle", "add_driver"
        ],
        # Recommendation actions
        "recommend": [
            "recommend_vehicle_for_trip", "suggest_alternate_vehicle"
        ],
        # Helper actions
        "helper": [
            "create_new_route_help", "simulate_action", "explain_decision"
        ],
        # Conversational actions (Phase 3)
        "conversational": [
            "wizard_step_input", "show_trip_suggestions", "create_trip_from_scratch",
            "create_followup_trip", "duplicate_trip", "change_driver", "get_trip_bookings",
            "start_trip_wizard", "cancel_wizard"
        ],
        # Special actions
        "special": [
            "context_mismatch", "unknown"
        ]
    }
    
    # Flatten registry into valid_actions list
    valid_actions = []
    for category, actions in ACTION_REGISTRY.items():
        valid_actions.extend(actions)
    
    logger.debug(f"Loaded {len(valid_actions)} valid actions from registry")
    
    # Normalize action synonyms before validation
    action_synonyms = {
        "change_driver": "assign_driver",
        "update_driver": "assign_driver", 
        "allocate_driver": "assign_driver",
        "appoint_driver": "assign_driver",
        "set_driver": "assign_driver",
        "deploy_driver": "assign_driver",
        "attach_driver": "assign_driver",
        "connect_driver": "assign_driver",
        "give_driver": "assign_driver",
        "send_driver": "assign_driver",
        "reserve_driver": "assign_driver",
        "allocate": "assign_driver",  # generic allocate maps to driver
        "appoint": "assign_driver",   # generic appoint maps to driver
        "give": "assign_driver",      # generic give maps to driver
        "send": "assign_driver"       # generic send maps to driver
    }
    
    original_action = response["action"]
    if original_action in action_synonyms:
        response["action"] = action_synonyms[original_action]
        logger.info(f"Normalized action '{original_action}' → '{response['action']}'")
    
    if response["action"] not in valid_actions:
        # Try fuzzy matching before defaulting to unknown
        fuzzy_matches = {
            "assign_drivers": "assign_driver",
            "attach_driver": "assign_driver",
            "give_driver": "assign_driver",
            "assign_vehicles": "assign_vehicle",
            "attach_vehicle": "assign_vehicle",
            "cancel_trips": "cancel_trip",
            "remove_trips": "cancel_trip",
            "delete_trip": "cancel_trip"
        }
        
        fuzzy_action = fuzzy_matches.get(response["action"])
        if fuzzy_action:
            logger.info(f"Fuzzy matched '{response['action']}' → '{fuzzy_action}'")
            response["action"] = fuzzy_action
        else:
            logger.warning(f"Invalid action '{response['action']}', setting to 'unknown'")
            response["action"] = "unknown"
    
    # Ensure confidence is between 0 and 1
    confidence = float(response.get("confidence", 0.5))
    response["confidence"] = max(0.0, min(1.0, confidence))
    
    # Normalize null fields
    response.setdefault("target_label", None)
    response.setdefault("target_time", None)
    response.setdefault("target_trip_id", None)
    response.setdefault("target_path_id", None)
    response.setdefault("target_route_id", None)
    response.setdefault("parameters", {})
    response.setdefault("clarify_options", [])
    
    # Ensure parameters is a dict
    if not isinstance(response["parameters"], dict):
        response["parameters"] = {}
    
    # Normalize all possible parameters
    response["parameters"].setdefault("vehicle_id", None)
    response["parameters"].setdefault("driver_id", None)
    response["parameters"].setdefault("vehicle_registration", None)
    response["parameters"].setdefault("driver_name", None)
    response["parameters"].setdefault("stop_ids", None)
    response["parameters"].setdefault("stop_names", None)
    response["parameters"].setdefault("path_stop_order", None)
    response["parameters"].setdefault("new_time", None)
    response["parameters"].setdefault("stop_name", None)
    response["parameters"].setdefault("latitude", None)
    response["parameters"].setdefault("longitude", None)
    response["parameters"].setdefault("path_name", None)
    response["parameters"].setdefault("route_name", None)
    
    return response


async def _call_openai(text: str, config: Dict[str, Any], context: Optional[Dict] = None) -> Dict[str, Any]:
    """Call OpenAI API with function calling"""
    if not config["openai_api_key"]:
        raise ValueError("OPENAI_API_KEY not configured")
    
    client = AsyncOpenAI(api_key=config["openai_api_key"])
    
    # Build messages
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]
    
    # Add few-shot examples
    for example in FEW_SHOT_EXAMPLES:
        messages.append({"role": "user", "content": example["user"]})
        messages.append({"role": "assistant", "content": example["assistant"]})
    
    # Add context if provided
    if context:
        context_str = f"Context: Page={context.get('currentPage')}, Route={context.get('selectedRouteId')}"
        messages.append({"role": "system", "content": context_str})
    
    # Add user message
    messages.append({"role": "user", "content": text})
    
    try:
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model=config["model"],
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=500,
            ),
            timeout=config["timeout"]
        )
        
        content = response.choices[0].message.content
        logger.info(f"[LLM] OpenAI response: {content[:200]}...")
        
        parsed = json.loads(content)
        return _validate_llm_response(parsed)
        
    except asyncio.TimeoutError:
        logger.error("[LLM] OpenAI request timed out")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"[LLM] Failed to parse OpenAI JSON response: {e}")
        raise
    except Exception as e:
        logger.error(f"[LLM] OpenAI API error: {e}")
        raise


async def _call_ollama(text: str, config: Dict[str, Any], context: Optional[Dict] = None) -> Dict[str, Any]:
    """Call Ollama API with JSON mode"""
    # Build prompt with examples
    prompt = f"{SYSTEM_PROMPT}\n\nExamples:\n"
    for example in FEW_SHOT_EXAMPLES[:3]:  # Use fewer examples for Ollama
        prompt += f"\nUser: {example['user']}\nAssistant: {example['assistant']}\n"
    
    if context:
        prompt += f"\nContext: Page={context.get('currentPage')}, Route={context.get('selectedRouteId')}\n"
    
    prompt += f"\nUser: {text}\nAssistant: "
    
    try:
        async with httpx.AsyncClient(timeout=config["timeout"]) as client:
            response = await client.post(
                f"{config['ollama_base_url']}/api/generate",
                json={
                    "model": config["model"],
                    "prompt": prompt,
                    "format": "json",
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                    }
                }
            )
            response.raise_for_status()
            result = response.json()
            content = result.get("response", "")
            
            logger.info(f"[LLM] Ollama response: {content[:200]}...")
            
            parsed = json.loads(content)
            return _validate_llm_response(parsed)
            
    except asyncio.TimeoutError:
        logger.error("[LLM] Ollama request timed out")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"[LLM] Failed to parse Ollama JSON response: {e}")
        raise
    except Exception as e:
        logger.error(f"[LLM] Ollama API error: {e}")
        raise


def _fallback_intent_parse(text: str, context: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Fallback intent parser using keyword matching when LLM is unavailable or blocked.
    Used when Gemini safety filters block the response.
    """
    text_lower = text.lower().strip()
    
    # Get trip_id from context if available
    selected_trip_id = None
    if context:
        selected_trip_id = context.get('selectedTripId') or context.get('ui_context', {}).get('selectedTripId')
    
    # Default response structure
    result = {
        "action": "unknown",
        "target_label": None,
        "target_time": None,
        "target_trip_id": selected_trip_id,
        "target_path_id": None,
        "target_route_id": None,
        "parameters": {},
        "confidence": 0.7,  # Medium confidence for keyword matching
        "clarify": False,
        "clarify_options": [],
        "explanation": "Parsed using keyword fallback"
    }
    
    # Extract trip_id from text if mentioned (e.g., "trip 41", "trip #5")
    import re
    trip_match = re.search(r'trip\s*#?\s*(\d+)', text_lower)
    if trip_match:
        result["target_trip_id"] = int(trip_match.group(1))
    
    # Keyword patterns for actions
    action_patterns = {
        # Compound Actions (check first - more specific patterns)
        "assign_vehicle_and_driver": [
            "assign vehicle and driver", "vehicle and driver to", "vehicle with driver",
            "put vehicle and driver", "deploy vehicle and driver", "assign bus and driver"
        ],
        
        # Trip Management
        "remove_driver": ["remove driver", "unassign driver", "take driver off", "detach driver"],
        "remove_vehicle": ["remove vehicle", "unassign vehicle", "take vehicle off", "detach vehicle"],
        "assign_driver": ["assign driver", "put driver on", "set driver for"],
        "assign_vehicle": ["assign vehicle", "put vehicle on", "set vehicle for", "assign bus"],
        "cancel_trip": ["cancel trip", "cancel this", "delete trip", "abort trip"],
        "update_trip_status": [
            "update status", "change status", "set status", "put status", 
            "status to", "mark as", "in progress", "in_progress", "completed", "scheduled", "cancelled"
        ],
        "get_trip_status": ["status of", "trip status", "what is the status", "get status", "show status"],
        "get_trip_details": ["details for", "trip details", "show trip", "get details"],
        "get_unassigned_vehicles": ["unassigned vehicles", "available vehicles", "free vehicles", "unsigned vehicles"],
        
        # Fleet Management - Add new resources
        "add_driver": ["add driver", "create driver", "new driver", "add a driver", "register driver"],
        "add_vehicle": ["add vehicle", "create vehicle", "new vehicle", "add a vehicle", "register vehicle"],
        
        # Dashboard Intelligence
        "get_trips_needing_attention": ["trips needing attention", "problem trips", "what needs attention", "trips with issues"],
        "get_today_summary": ["today summary", "today's status", "operations summary", "daily summary"],
        "get_recent_changes": ["recent changes", "what changed", "last 10 minutes", "recent updates"],
        "get_high_demand_offices": ["high demand", "busiest office", "most bookings", "demand by office"],
        "get_most_used_vehicles": ["most used vehicle", "vehicle usage", "busiest vehicles"],
        "detect_overbooking": ["overbooked trips", "detect overbooking", "over capacity"],
        "predict_problem_trips": ["predict problems", "at risk trips", "failing trips", "risky trips"],
        
        # Vehicle Management
        "get_vehicle_status": ["vehicle status", "show vehicle", "check vehicle"],
        "block_vehicle": ["block vehicle", "disable vehicle", "vehicle unavailable"],
        "unblock_vehicle": ["unblock vehicle", "enable vehicle", "make vehicle available"],
        "get_vehicle_trips_today": ["vehicle trips today", "what trips has vehicle", "vehicle schedule"],
        "recommend_vehicle_for_trip": ["recommend vehicle", "suggest vehicle", "best vehicle", "which vehicle"],
        
        # Driver Management
        "get_driver_status": ["driver status", "show driver", "check driver"],
        "get_driver_trips_today": ["driver trips today", "what trips has driver", "driver schedule"],
        "set_driver_availability": ["set driver available", "driver is available", "driver unavailable", "mark driver"],
        
        # Booking Management
        "get_booking_count": ["booking count", "how many bookings", "bookings for trip"],
        "list_passengers": ["list passengers", "show passengers", "who is booked", "passenger list"],
        "cancel_all_bookings": ["cancel all bookings", "remove all passengers", "clear bookings"],
        "find_employee_trips": ["find employee", "employee trips", "trips for employee", "employee bookings"],
        "get_trip_stops": ["stops for trip", "trip stops", "what stops", "stops in trip", "stops on trip"],
        
        # Smart Automation
        "check_trip_readiness": ["can this trip run", "is trip ready", "check readiness", "trip ready"],
        "simulate_action": ["simulate", "what would happen if", "test action"],
        "explain_decision": ["explain", "why did you", "explain decision", "reasoning"],
        
        # Stops/Paths/Routes
        "list_all_stops": ["list stops", "all stops", "show stops"],
        "create_stop": ["create stop", "new stop", "add stop"],
        "delete_stop": ["delete stop", "remove stop"],
        "create_path": ["create path", "new path", "add path"],
        "delete_path": ["delete path", "remove path"],
        "create_route": ["create route", "new route", "add route"],
        "delete_route": ["delete route", "remove route"],
        "validate_route": ["validate route", "check route", "route valid"],
    }
    
    # Match action
    for action, patterns in action_patterns.items():
        for pattern in patterns:
            if pattern in text_lower:
                result["action"] = action
                result["confidence"] = 0.8
                result["explanation"] = f"Matched keyword pattern: '{pattern}'"
                logger.info(f"[FALLBACK] Matched action={action} from pattern='{pattern}'")
                
                # Extract vehicle and driver for compound command
                if action == "assign_vehicle_and_driver":
                    result["confidence"] = 0.9
                    # Extract vehicle registration (patterns like 'MH-12-7777', 'KA01AB1234')
                    vehicle_match = re.search(r"vehicle\s+['\"]?([A-Za-z]{2}[-\s]?\d{2}[-\s]?[A-Za-z]{0,2}[-\s]?\d{4})['\"]?", text, re.IGNORECASE)
                    if vehicle_match:
                        result["parameters"]["vehicle_registration"] = vehicle_match.group(1).upper().replace(" ", "-")
                        logger.info(f"[FALLBACK] Extracted vehicle_registration: {result['parameters']['vehicle_registration']}")
                    
                    # Extract driver name (patterns like "driver 'John Snow'" or "driver John Snow")
                    driver_match = re.search(r"driver\s+['\"]?([A-Za-z]+(?:\s+[A-Za-z]+)?)['\"]?", text, re.IGNORECASE)
                    if driver_match:
                        result["parameters"]["driver_name"] = driver_match.group(1).strip()
                        logger.info(f"[FALLBACK] Extracted driver_name: {result['parameters']['driver_name']}")
                    
                    # Extract trip ID
                    trip_match = re.search(r"trip\s+(\d+)", text, re.IGNORECASE)
                    if trip_match:
                        result["target_trip_id"] = int(trip_match.group(1))
                        logger.info(f"[FALLBACK] Extracted target_trip_id: {result['target_trip_id']}")
                
                # Extract status parameter for update_trip_status
                if action == "update_trip_status":
                    if "in progress" in text_lower or "in_progress" in text_lower:
                        result["parameters"]["new_status"] = "IN_PROGRESS"
                    elif "completed" in text_lower:
                        result["parameters"]["new_status"] = "COMPLETED"
                    elif "scheduled" in text_lower:
                        result["parameters"]["new_status"] = "SCHEDULED"
                    elif "cancelled" in text_lower or "canceled" in text_lower:
                        result["parameters"]["new_status"] = "CANCELLED"
                break
        if result["action"] != "unknown":
            break
    
    # Secondary check for compound vehicle+driver assignment if not already detected
    if result["action"] == "assign_vehicle" and "driver" in text_lower:
        # Check if there's ALSO a driver mentioned - upgrade to compound action
        if re.search(r"and\s+driver|driver\s+['\"]?\w+|with\s+driver", text, re.IGNORECASE):
            result["action"] = "assign_vehicle_and_driver"
            result["confidence"] = 0.9
            logger.info(f"[FALLBACK] Upgraded assign_vehicle to assign_vehicle_and_driver")
            
            # Extract vehicle registration
            vehicle_match = re.search(r"vehicle\s+['\"]?([A-Za-z]{2}[-\s]?\d{2}[-\s]?[A-Za-z]{0,2}[-\s]?\d{4})['\"]?", text, re.IGNORECASE)
            if vehicle_match:
                result["parameters"]["vehicle_registration"] = vehicle_match.group(1).upper().replace(" ", "-")
            
            # Extract driver name
            driver_match = re.search(r"driver\s+['\"]?([A-Za-z]+(?:\s+[A-Za-z]+)?)['\"]?", text, re.IGNORECASE)
            if driver_match:
                result["parameters"]["driver_name"] = driver_match.group(1).strip()
            
            # Extract trip ID
            trip_match = re.search(r"trip\s+(\d+)", text, re.IGNORECASE)
            if trip_match:
                result["target_trip_id"] = int(trip_match.group(1))
    
    # If no action matched but we have context, try simpler patterns
    if result["action"] == "unknown" and selected_trip_id:
        if "driver" in text_lower:
            if any(word in text_lower for word in ["remove", "unassign", "take off", "delete"]):
                result["action"] = "remove_driver"
            else:
                result["action"] = "assign_driver"
            result["confidence"] = 0.75
        elif "vehicle" in text_lower or "bus" in text_lower:
            if any(word in text_lower for word in ["remove", "unassign", "take off", "delete"]):
                result["action"] = "remove_vehicle"
            else:
                result["action"] = "assign_vehicle"
            result["confidence"] = 0.75
        elif "cancel" in text_lower:
            result["action"] = "cancel_trip"
            result["confidence"] = 0.75
        elif "status" in text_lower:
            # Check if it's a status update or status query
            if any(word in text_lower for word in ["to", "set", "change", "update", "put", "mark"]):
                result["action"] = "update_trip_status"
                # Try to extract the status
                if "in progress" in text_lower or "in_progress" in text_lower:
                    result["parameters"]["new_status"] = "IN_PROGRESS"
                elif "completed" in text_lower:
                    result["parameters"]["new_status"] = "COMPLETED"
                elif "scheduled" in text_lower:
                    result["parameters"]["new_status"] = "SCHEDULED"
                elif "cancelled" in text_lower:
                    result["parameters"]["new_status"] = "CANCELLED"
            else:
                result["action"] = "get_trip_status"
            result["confidence"] = 0.75
    
    # Handle very short/vague requests like "list them" - assume context from last action
    if result["action"] == "unknown" and len(text_lower.split()) <= 3:
        if any(word in text_lower for word in ["list", "show", "display", "them", "all"]):
            # Generic list request - could be vehicles, stops, etc.
            result["action"] = "get_unassigned_vehicles"  # Default to a common list action
            result["confidence"] = 0.6
            result["explanation"] = "Assumed list request based on vague input"
    
    # If still unknown and no context, request clarification
    if result["action"] == "unknown":
        result["clarify"] = True
        result["confidence"] = 0.3
        result["clarify_options"] = ["What action would you like to perform?"]
    
    logger.info(f"[FALLBACK] Final result: action={result['action']}, confidence={result['confidence']}")
    return result


async def _call_gemini(text: str, config: Dict[str, Any], context: Optional[Dict] = None) -> Dict[str, Any]:
    """Call Google Gemini API with JSON mode"""
    if not config["gemini_api_key"]:
        raise ValueError("GEMINI_API_KEY not configured")
    
    # Configure Gemini
    genai.configure(api_key=config["gemini_api_key"])
    
    # Use gemini-1.5-flash or gemini-1.5-pro (use stable v1 API, not beta)
    model_name = config.get("model", "gemini-1.5-flash")
    if not model_name.startswith("gemini"):
        model_name = "gemini-1.5-flash"  # Default Gemini model
    
    # Configure generation parameters
    generation_config = {
        "temperature": 0.3,
        "max_output_tokens": 500,
    }
    
    # Use JSON schema if supported, otherwise rely on prompt instructions
    try:
        generation_config["response_mime_type"] = "application/json"
    except Exception:
        pass  # Older API versions may not support this
    
    # Configure safety settings to allow transport operations
    safety_settings = [
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_NONE"
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_NONE"
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_NONE"
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_NONE"
        }
    ]
    
    # Create model with config
    model = genai.GenerativeModel(
        model_name=model_name,
        generation_config=generation_config,
        safety_settings=safety_settings
    )
    
    # Build prompt with examples
    prompt = f"{SYSTEM_PROMPT}\n\nExamples:\n"
    for example in FEW_SHOT_EXAMPLES[:5]:  # Use more examples for better accuracy
        prompt += f"\nUser: {example['user']}\nAssistant: {example['assistant']}\n"
    
    if context:
        prompt += f"\nCONTEXT:\n"
        prompt += f"Current Page: {context.get('currentPage', 'unknown')}\n"
        
        # Enhanced trip context
        selected_trip_id = context.get('selectedTripId') or context.get('ui_context', {}).get('selectedTripId')
        if selected_trip_id:
            prompt += f"Selected Trip ID: {selected_trip_id}\n"
            prompt += f"IMPORTANT: User is viewing trip {selected_trip_id}. For vague references like 'this trip', 'assign driver', 'cancel', use this trip ID.\n"
        
        if context.get('selectedRouteId'):
            prompt += f"Selected Route: {context.get('selectedRouteId')}\n"
            
        # Trip details if available
        trip_details = context.get('trip_details') or context.get('ui_context', {}).get('currentTrip')
        if trip_details:
            prompt += f"Trip Details: {trip_details}\n"
            
        # Conversation context
        if context.get('awaiting_selection'):
            prompt += f"Awaiting Selection: User is in selection mode from previous interaction\n"
            if context.get('last_offered_options'):
                prompt += f"Last Options: {context.get('last_offered_options')}\n"
                
        prompt += f"\nCONTEXT RULES:\n"
        prompt += f"- If selectedTripId exists and user mentions actions on 'this', 'that', 'it', 'here': USE selectedTripId as target_trip_id\n"
        prompt += f"- If user says vague commands like 'assign driver' without trip name: USE selectedTripId if available\n"
        prompt += f"- Only set clarify=true if no selectedTripId and user doesn't specify trip name\n"
        prompt += f"- Support casual/incomplete English: 'assign' → assign_driver, 'cancel' → cancel_trip\n"
        
        # PAGE CONTEXT ENFORCEMENT
        current_page = context.get('currentPage', 'unknown')
        prompt += f"\n⚠️ PAGE CONTEXT ENFORCEMENT (CRITICAL):\n"
        prompt += f"- Current Page: {current_page}\n"
        if current_page == 'busDashboard':
            prompt += f"- ALLOWED: Trip/Vehicle/Driver/Booking management actions (40 actions)\n"
            prompt += f"- BLOCKED: Route/Path/Stop creation/deletion → return action='context_mismatch'\n"
            prompt += f"- If user asks to create/delete route/path/stop → action='context_mismatch', explanation='This action is only available on Manage Route page.'\n"
        elif current_page == 'manageRoute':
            prompt += f"- ALLOWED: Route/Path/Stop management actions (15 actions)\n"
            prompt += f"- BLOCKED: Trip/Vehicle/Driver operations → return action='context_mismatch'\n"
            prompt += f"- If user asks to cancel/assign/modify trips → action='context_mismatch', explanation='This action is only available on Dashboard.'\n"
        prompt += f"\n"
    else:
        prompt += f"\nNO CONTEXT: User must specify trip/route explicitly or clarify=true\n\n"
    
    prompt += f"\nUser: {text}\nAssistant: "
    
    try:
        # Call Gemini API with increased timeout and retry logic
        response = await asyncio.wait_for(
            asyncio.to_thread(model.generate_content, prompt),
            timeout=30.0  # Increased from 10 to 30 seconds
        )
        
        # Handle safety filter blocks (finish_reason=2 means SAFETY)
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'finish_reason') and candidate.finish_reason == 2:
                logger.warning(f"[LLM] Gemini safety filter blocked response for: '{text}'")
                # Attempt to parse intent from text directly using keyword matching
                return _fallback_intent_parse(text, context)
        
        # Try to get text, with fallback for blocked responses
        try:
            content = response.text
        except ValueError as ve:
            if "finish_reason" in str(ve):
                logger.warning(f"[LLM] Gemini returned no content (likely safety filter): {ve}")
                return _fallback_intent_parse(text, context)
            raise
        
        logger.info(f"[LLM] Gemini response: {content[:400]}...")
        
        # Handle truncated JSON responses with robust fixing
        def fix_truncated_json(content: str) -> str:
            """Attempt to fix common JSON truncation issues"""
            content = content.strip()
            
            # Remove any trailing commas before attempting to close
            content = re.sub(r',\s*$', '', content)
            
            # Count open braces and brackets to determine what's missing
            open_braces = content.count('{') - content.count('}')
            open_brackets = content.count('[') - content.count(']')
            
            # Add missing closing characters
            for _ in range(open_brackets):
                content += ']'
            for _ in range(open_braces):
                content += '}'
                
            return content
        
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"[LLM] Failed to parse Gemini JSON response: {e}")
            logger.error(f"[LLM] Full response content: {content}")
            
            # Try to fix the JSON
            try:
                fixed_content = fix_truncated_json(content)
                parsed = json.loads(fixed_content)
                logger.info(f"[LLM] Successfully fixed truncated JSON")
            except json.JSONDecodeError as fix_error:
                logger.error(f"[LLM] Could not fix JSON: {fix_error}")
                logger.error(f"[LLM] Fixed content was: {fixed_content}")
                # Return a structured fallback response that matches expected schema
                return {
                    "action": "assign_vehicle",  # Use the action we can infer from original response
                    "target_label": None,
                    "target_time": None,
                    "target_trip_id": None,
                    "target_path_id": None,
                    "target_route_id": None,
                    "parameters": {
                        "vehicle_id": None,
                        "driver_id": None,
                        "vehicle_registration": None,
                        "driver_name": None,
                        "stop_ids": None
                    },
                    "confidence": 0.8,  # Set reasonable confidence since we can infer the intent
                    "clarify": True,
                    "clarify_options": ["Please select a specific vehicle for this trip"],
                    "explanation": "Detected vehicle assignment request but need clarification"
                }
        
        return _validate_llm_response(parsed)
        
    except asyncio.TimeoutError:
        logger.error("[LLM] Gemini request timed out")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"[LLM] Failed to parse Gemini JSON response: {e}")
        raise
    except Exception as e:
        logger.error(f"[LLM] Gemini API error: {e}")
        raise


async def parse_intent_with_llm(text: str, context: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Parse user intent using LLM
    
    Args:
        text: User's natural language input
        context: Optional context dict with currentPage, selectedRouteId, etc.
        
    Returns:
        Dict with structure:
        {
          "action": "cancel_trip" | "remove_vehicle" | "assign_vehicle" | "unknown",
          "target_label": "string|null",
          "target_time": "HH:MM|null",
          "target_trip_id": int|null,
          "parameters": { "vehicle_id":int|null, "driver_id":int|null },
          "confidence": 0.0-1.0,
          "clarify": bool,
          "clarify_options": [string],
          "explanation": "short",
        }
    """
    config = _get_llm_config()
    
    logger.info(f"[LLM] Parsing intent with {config['provider']}: '{text}'")
    
    # Check if LLM is configured
    if config["provider"] == "openai" and not config["openai_api_key"]:
        logger.warning("[LLM] OpenAI API key not configured, returning clarify mode")
        return {
            "action": "unknown",
            "target_label": None,
            "target_time": None,
            "target_trip_id": None,
            "parameters": {},
            "confidence": 0.0,
            "clarify": True,
            "clarify_options": [],
            "explanation": "LLM not configured. Please set OPENAI_API_KEY, GEMINI_API_KEY, or configure Ollama."
        }
    
    if config["provider"] == "gemini" and not config["gemini_api_key"]:
        logger.warning("[LLM] Gemini API key not configured, returning clarify mode")
        return {
            "action": "unknown",
            "target_label": None,
            "target_time": None,
            "target_trip_id": None,
            "parameters": {},
            "confidence": 0.0,
            "clarify": True,
            "clarify_options": [],
            "explanation": "LLM not configured. Please set GEMINI_API_KEY."
        }
    
    try:
        if config["provider"] == "openai":
            result = await _call_openai(text, config, context)
        elif config["provider"] == "gemini":
            # Retry logic for Gemini (handles timeouts)
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    result = await _call_gemini(text, config, context)
                    break  # Success, exit retry loop
                except TimeoutError:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                        logger.warning(f"[LLM] Gemini timeout on attempt {attempt + 1}/{max_retries}, retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"[LLM] Gemini timed out after {max_retries} attempts")
                        raise
        elif config["provider"] == "ollama":
            result = await _call_ollama(text, config, context)
        else:
            raise ValueError(f"Unsupported LLM provider: {config['provider']}")
        
        logger.info(
            f"[LLM] Parsed intent: action={result['action']}, "
            f"confidence={result['confidence']}, clarify={result['clarify']}"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"[LLM] Error parsing intent: {e}", exc_info=True)
        # Return safe fallback
        return {
            "action": "unknown",
            "target_label": None,
            "target_time": None,
            "target_trip_id": None,
            "parameters": {},
            "confidence": 0.0,
            "clarify": True,
            "clarify_options": [],
            "explanation": f"LLM error: {str(e)}"
        }
