"""
LLM Client for Intent Parsing
Supports OpenAI, Google Gemini, and Ollama with structured JSON output
"""
import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
import httpx
import google.generativeai as genai

logger = logging.getLogger(__name__)

# System prompt for LLM
SYSTEM_PROMPT = """You are MoviAgent's intent parser. Parse transport operations commands into structured JSON only.

Return ONLY valid JSON following this schema:

{
 "action":"cancel_trip|remove_vehicle|assign_vehicle|update_trip_time|get_unassigned_vehicles|get_trip_status|get_trip_details|list_all_stops|list_stops_for_path|list_routes_using_path|create_stop|create_path|create_route|rename_stop|duplicate_route|create_new_route_help|context_mismatch|unknown",
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
   "route_name":"string"|null
 },
 "confidence":0.0-1.0,
 "clarify":boolean,
 "clarify_options":[string],
 "explanation":"short"
}

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

Dashboard-Only Actions (currentPage="busDashboard"):
- cancel_trip, remove_vehicle, assign_vehicle, update_trip_time
- get_trip_status, get_trip_details, get_unassigned_vehicles
If user requests these on manageRoute → return action="context_mismatch" with explanation.

ManageRoute-Only Actions (currentPage="manageRoute"):
- create_stop, create_path, create_route, rename_stop, duplicate_route
- list_all_stops, list_stops_for_path, list_routes_using_path, create_new_route_help
If user requests these on busDashboard → return action="context_mismatch" with explanation.

Examples of context_mismatch:
- User on busDashboard asks "create a route" → action="context_mismatch", explanation="Route creation is only available on Manage Route page."
- User on manageRoute asks "cancel trip" → action="context_mismatch", explanation="Trip cancellations are only available on Dashboard."

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
        "assistant": '{"action":"assign_vehicle","target_label":"Bulk - 00:01","target_time":"00:01","target_trip_id":null,"target_path_id":null,"target_route_id":null,"parameters":{"vehicle_id":8,"driver_id":3},"confidence":0.92,"clarify":false,"clarify_options":[],"explanation":"User wants to assign vehicle and driver"}'
    },
    {
        "user": "Assign vehicle MH-12-3456 and driver Amit to trip 5",
        "assistant": '{"action":"assign_vehicle","target_label":null,"target_time":null,"target_trip_id":5,"target_path_id":null,"target_route_id":null,"parameters":{"vehicle_registration":"MH-12-3456","driver_name":"Amit"},"confidence":0.88,"clarify":false,"clarify_options":[],"explanation":"User wants to assign vehicle by registration and driver by name"}'
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
    
    # Validate action - ALL ACTIONS (Phase 1-3)
    valid_actions = [
        # Dynamic READ
        "get_unassigned_vehicles", "get_trip_status", "get_trip_details",
        # Static READ
        "list_all_stops", "list_stops_for_path", "list_routes_using_path",
        # Dynamic MUTATE
        "cancel_trip", "remove_vehicle", "assign_vehicle", "update_trip_time",
        # Static MUTATE
        "create_stop", "create_path", "create_route", "rename_stop", "duplicate_route",
        # Helper
        "create_new_route_help",
        # Phase 3: Conversational actions
        "wizard_step_input",        # User response during wizard
        "show_trip_suggestions",    # Manually request suggestions
        "create_trip_from_scratch", # Explicit trip creation
        "create_followup_trip",     # Create follow-up trip
        "duplicate_trip",           # Duplicate existing trip
        "change_driver",            # Change driver assignment
        "get_trip_bookings",        # View bookings for trip
        "start_trip_wizard",        # Start trip creation wizard
        "cancel_wizard",            # Cancel active wizard
        # Special
        "context_mismatch",
        # Fallback
        "unknown"
    ]
    if response["action"] not in valid_actions:
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
        prompt += f"\nContext: Page={context.get('currentPage')}, Route={context.get('selectedRouteId')}\n"
        if context.get('selectedTripId'):
            prompt += f"Selected Trip: {context.get('selectedTripId')}\n"
        prompt += f"\nREMEMBER: Enforce page context rules! Return action='context_mismatch' if user requests wrong-page action.\n"
    
    prompt += f"\nUser: {text}\nAssistant: "
    
    try:
        # Call Gemini API with increased timeout and retry logic
        response = await asyncio.wait_for(
            asyncio.to_thread(model.generate_content, prompt),
            timeout=30.0  # Increased from 10 to 30 seconds
        )
        
        content = response.text
        logger.info(f"[LLM] Gemini response: {content[:200]}...")
        
        parsed = json.loads(content)
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
