"""
LangGraph Graph Definition for MOVI Agent
Defines the reasoning flow and node connections
"""
from typing import Dict, Callable, Optional, List
import logging
import os
from langgraph.nodes import (
    parse_intent,
    resolve_target,
    check_consequences,
    get_confirmation,
    execute_action,
    report_result,
    fallback,
)

# Phase 3: Conversational Creation Agent nodes
from langgraph.nodes.decision_router import decision_router, route_decision
from langgraph.nodes.suggestion_provider import suggestion_provider
from langgraph.nodes.vehicle_selection_provider import vehicle_selection_provider
from langgraph.nodes.driver_selection_provider import driver_selection_provider
from langgraph.nodes.create_trip_suggester import create_trip_suggester
from langgraph.nodes.trip_creation_wizard import trip_creation_wizard
from langgraph.nodes.collect_user_input import collect_user_input

# Tutorial: Import your new node
from langgraph.nodes.get_trip_summary import get_trip_summary

# Feature flag for LLM-based intent parsing - Default to TRUE for natural language support
USE_LLM_PARSE = os.getenv("USE_LLM_PARSE", "true").lower() == "true"

# Always try to import LLM node first
logger = logging.getLogger(__name__)
try:
    from langgraph.nodes.parse_intent_llm import parse_intent_llm
    LLM_AVAILABLE = True
    logger.info("🤖 LLM parse_intent_llm imported successfully")
except ImportError as e:
    LLM_AVAILABLE = False
    logger.error(f"Failed to import parse_intent_llm: {e}. Will fallback to classic parse.")

# Determine which parser to use
if USE_LLM_PARSE and LLM_AVAILABLE:
    logger.info("🤖 LLM parse mode enabled - Natural language support active")
else:
    logger.info("📝 Classic parse mode enabled - Regex-based parsing only")


class Graph:
    """
    Simple graph structure for managing agent workflow.
    """
    
    def __init__(self, name: str):
        self.name = name
        self.nodes: Dict[str, Callable] = {}
        self.edges: Dict[str, List[Dict]] = {}
        
    def add_node(self, name: str, func: Callable):
        """Add a node to the graph."""
        self.nodes[name] = func
        
    def add_edge(self, from_node: str, to_node: str, condition: Optional[Callable] = None):
        """Add an edge between nodes with optional condition."""
        if from_node not in self.edges:
            self.edges[from_node] = []
        self.edges[from_node].append({
            "to": to_node,
            "condition": condition
        })
        
    def get_next_node(self, current: str, state: Dict) -> Optional[str]:
        """Determine the next node based on current state."""
        if current not in self.edges:
            return None
            
        for edge in self.edges[current]:
            condition = edge["condition"]
            if condition is None or condition(state):
                return edge["to"]
        
        return None


# Create the MOVI agent graph
graph = Graph(name="movi_agent")

# Register parse intent node - Always prefer LLM if available
if USE_LLM_PARSE and LLM_AVAILABLE:
    graph.add_node("parse_intent", parse_intent_llm)
    logger.info("✅ Registered LLM parse_intent node - Natural language parsing enabled")
else:
    graph.add_node("parse_intent", parse_intent)
    logger.info("⚠️ Registered classic parse_intent node - Limited regex parsing only")

graph.add_node("resolve_target", resolve_target)
graph.add_node("check_consequences", check_consequences)
graph.add_node("get_confirmation", get_confirmation)
graph.add_node("execute_action", execute_action)
graph.add_node("report_result", report_result)
graph.add_node("fallback", fallback)

# Phase 3: Conversational nodes
graph.add_node("decision_router", decision_router)
graph.add_node("suggestion_provider", suggestion_provider)
graph.add_node("vehicle_selection_provider", vehicle_selection_provider)
graph.add_node("driver_selection_provider", driver_selection_provider)
graph.add_node("create_trip_suggester", create_trip_suggester)
graph.add_node("trip_creation_wizard", trip_creation_wizard)
graph.add_node("collect_user_input", collect_user_input)

# Tutorial: Register your new node
graph.add_node("get_trip_summary", get_trip_summary)
logger.info("✅ Registered get_trip_summary node - Tutorial example")

logger.info("Registered Phase 3 conversational nodes")

# === EDGES: Main Flow ===

# parse_intent → resolve_target (normal flow)
graph.add_edge("parse_intent", "resolve_target", condition=lambda s: s.get("next_node") != "execute_action")

# parse_intent → execute_action (for add_vehicle/add_driver wizard continuation)
graph.add_edge("parse_intent", "execute_action", condition=lambda s: s.get("next_node") == "execute_action")

# resolve_target → decision_router (Phase 3: new routing layer)
graph.add_edge(
    "resolve_target", 
    "decision_router",
    condition=lambda s: not s.get("error")
)
graph.add_edge(
    "resolve_target",
    "fallback",
    condition=lambda s: s.get("error")
)

# === EDGES: Decision Router (Phase 3) ===

# decision_router routes to multiple paths based on next_node
def route_to_suggestion_provider(state):
    return state.get("next_node") == "suggestion_provider"

def route_to_vehicle_selection_provider(state):
    return state.get("next_node") == "vehicle_selection_provider"

def route_to_driver_selection_provider(state):
    return state.get("next_node") == "driver_selection_provider"

def route_to_create_trip_suggester(state):
    return state.get("next_node") == "create_trip_suggester"

def route_to_trip_creation_wizard(state):
    return state.get("next_node") == "trip_creation_wizard"

def route_to_check_consequences(state):
    return state.get("next_node") == "check_consequences"

def route_to_report_result(state):
    return state.get("next_node") == "report_result"

# Tutorial: Add routing function for our new node
def route_to_get_trip_summary(state):
    return state.get("next_node") == "get_trip_summary"

def route_to_collect_user_input(state):
    return state.get("next_node") == "collect_user_input"

# From decision_router
graph.add_edge("decision_router", "suggestion_provider", condition=route_to_suggestion_provider)
graph.add_edge("decision_router", "vehicle_selection_provider", condition=route_to_vehicle_selection_provider)
graph.add_edge("decision_router", "driver_selection_provider", condition=route_to_driver_selection_provider)
graph.add_edge("decision_router", "create_trip_suggester", condition=route_to_create_trip_suggester)
graph.add_edge("decision_router", "trip_creation_wizard", condition=route_to_trip_creation_wizard)
graph.add_edge("decision_router", "check_consequences", condition=route_to_check_consequences)
graph.add_edge("decision_router", "collect_user_input", condition=lambda s: s.get("next_node") == "collect_user_input")  # For wizard input
graph.add_edge("decision_router", "report_result", condition=route_to_report_result)

# Tutorial: Add edge from decision_router to our new node
graph.add_edge("decision_router", "get_trip_summary", condition=route_to_get_trip_summary)

# === EDGES: Wizard Flow (Phase 3) ===

# suggestion_provider → report_result (shows suggestions)
graph.add_edge("suggestion_provider", "report_result")

# vehicle_selection_provider → report_result (shows vehicle options)
graph.add_edge("vehicle_selection_provider", "report_result")

# driver_selection_provider → report_result (shows driver options)
graph.add_edge("driver_selection_provider", "report_result")

# create_trip_suggester → report_result (shows offer)
graph.add_edge("create_trip_suggester", "report_result")

# Tutorial: Our node goes to report_result to show the summary
graph.add_edge("get_trip_summary", "report_result")

# trip_creation_wizard → collect_user_input (get wizard input) - ONLY if explicitly routed there
graph.add_edge("trip_creation_wizard", "collect_user_input", condition=lambda s: s.get("next_node") == "collect_user_input")

# trip_creation_wizard → report_result (wizard asking for input OR wizard completed/error)
# The wizard now returns to report_result to show the prompt to the user
graph.add_edge("trip_creation_wizard", "report_result", condition=lambda s: s.get("next_node") == "report_result" or s.get("next_node") != "collect_user_input")

# collect_user_input routes back
graph.add_edge("collect_user_input", "trip_creation_wizard", condition=lambda s: s.get("next_node") == "trip_creation_wizard")
graph.add_edge("collect_user_input", "decision_router", condition=lambda s: s.get("next_node") == "decision_router")
graph.add_edge("collect_user_input", "parse_intent", condition=lambda s: s.get("next_node") == "parse_intent")
graph.add_edge("collect_user_input", "report_result", condition=lambda s: s.get("next_node") == "report_result")

# === EDGES: Original Flow (unchanged) ===
# === EDGES: Original Flow (unchanged) ===

# check_consequences → get_confirmation (if needs confirmation) OR execute_action (if safe to proceed)
graph.add_edge(
    "check_consequences",
    "get_confirmation",
    condition=lambda s: s.get("needs_confirmation") and not s.get("error")
)
graph.add_edge(
    "check_consequences",
    "execute_action",
    condition=lambda s: not s.get("needs_confirmation") and not s.get("error")
)
graph.add_edge(
    "check_consequences",
    "fallback",
    condition=lambda s: s.get("error")
)

# get_confirmation → report_result (always - waits for user confirmation)
graph.add_edge("get_confirmation", "report_result")

# execute_action → report_result (always)
graph.add_edge("execute_action", "report_result")

# fallback → END (no further edges)
# report_result → END (no further edges)


logger.info(f"Graph '{graph.name}' initialized with {len(graph.nodes)} nodes")
logger.info(f"Phase 3: Conversational agent with wizards and suggestions enabled")
