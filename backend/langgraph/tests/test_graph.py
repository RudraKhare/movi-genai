"""
Unit Tests for LangGraph Agent
Tests the graph flow, nodes, and runtime execution
"""
import pytest
import asyncio
from langgraph.graph_def import graph
from langgraph.runtime import GraphRuntime
from langgraph.nodes import (
    parse_intent,
    resolve_target,
    check_consequences,
    execute_action,
    report_result,
    fallback,
)


# ============================================================================
# Node Tests
# ============================================================================

@pytest.mark.asyncio
async def test_parse_intent_remove_vehicle():
    """Test parsing 'remove vehicle' intent"""
    state = {"text": "remove vehicle from Bulk - 00:01"}
    result = await parse_intent(state)
    
    assert result["action"] == "remove_vehicle"
    assert "error" not in result


@pytest.mark.asyncio
async def test_parse_intent_cancel_trip():
    """Test parsing 'cancel trip' intent"""
    state = {"text": "cancel trip Bulk - 00:01"}
    result = await parse_intent(state)
    
    assert result["action"] == "cancel_trip"
    assert "error" not in result


@pytest.mark.asyncio
async def test_parse_intent_assign_vehicle():
    """Test parsing 'assign vehicle' intent"""
    state = {"text": "assign vehicle to Bulk - 00:01"}
    result = await parse_intent(state)
    
    assert result["action"] == "assign_vehicle"
    assert "error" not in result


@pytest.mark.asyncio
async def test_parse_intent_unknown():
    """Test parsing unknown intent"""
    state = {"text": "do something random"}
    result = await parse_intent(state)
    
    assert result["action"] == "unknown"
    assert "message" in result


@pytest.mark.asyncio
async def test_parse_intent_empty():
    """Test parsing empty text"""
    state = {"text": ""}
    result = await parse_intent(state)
    
    assert result["action"] == "unknown"
    assert result.get("error") == "No input text provided"


# ============================================================================
# Resolve Target Tests
# ============================================================================

@pytest.mark.asyncio
async def test_resolve_target_with_error():
    """Test that resolve_target skips if there's an error"""
    state = {
        "text": "remove vehicle",
        "action": "remove_vehicle",
        "error": "previous_error"
    }
    result = await resolve_target(state)
    
    assert result["error"] == "previous_error"


# Note: Testing actual trip resolution requires database connection
# These would be integration tests


# ============================================================================
# Check Consequences Tests
# ============================================================================

@pytest.mark.asyncio
async def test_check_consequences_no_trip():
    """Test that check_consequences skips if no trip_id"""
    state = {"action": "remove_vehicle"}
    result = await check_consequences(state)
    
    # Should pass through unchanged
    assert "consequences" not in result


# ============================================================================
# Execute Action Tests
# ============================================================================

@pytest.mark.asyncio
async def test_execute_action_with_error():
    """Test that execute_action skips if there's an error"""
    state = {
        "action": "remove_vehicle",
        "trip_id": 1,
        "error": "previous_error"
    }
    result = await execute_action(state)
    
    assert result["error"] == "previous_error"


@pytest.mark.asyncio
async def test_execute_action_unknown():
    """Test execute_action with unknown action"""
    state = {
        "action": "unknown_action",
        "trip_id": 1,
        "user_id": 1
    }
    result = await execute_action(state)
    
    assert result.get("execution_result", {}).get("ok") == False


# ============================================================================
# Report Result Tests
# ============================================================================

@pytest.mark.asyncio
async def test_report_result_basic():
    """Test report_result formats output correctly"""
    state = {
        "action": "remove_vehicle",
        "trip_id": 12,
        "trip_label": "Bulk - 00:01",
        "status": "executed",
        "message": "Success"
    }
    result = await report_result(state)
    
    assert "final_output" in result
    assert result["final_output"]["action"] == "remove_vehicle"
    assert result["final_output"]["trip_id"] == 12


@pytest.mark.asyncio
async def test_report_result_with_confirmation():
    """Test report_result with confirmation required"""
    state = {
        "action": "cancel_trip",
        "needs_confirmation": True,
        "confirmation_required": True,
        "status": "awaiting_confirmation"
    }
    result = await report_result(state)
    
    assert result["final_output"]["needs_confirmation"] == True
    assert result["final_output"]["confirmation_required"] == True


# ============================================================================
# Fallback Tests
# ============================================================================

@pytest.mark.asyncio
async def test_fallback_trip_not_found():
    """Test fallback with trip_not_found error"""
    state = {
        "action": "remove_vehicle",
        "error": "trip_not_found"
    }
    result = await fallback(state)
    
    assert "final_output" in result
    assert result["final_output"]["success"] == False
    assert "couldn't find" in result["final_output"]["message"].lower()


@pytest.mark.asyncio
async def test_fallback_unknown():
    """Test fallback with unknown error"""
    state = {
        "action": "remove_vehicle",
        "error": "unknown"
    }
    result = await fallback(state)
    
    assert "final_output" in result
    assert result["final_output"]["success"] == False


# ============================================================================
# Graph Runtime Tests
# ============================================================================

@pytest.mark.asyncio
async def test_graph_runtime_initialization():
    """Test that GraphRuntime initializes correctly"""
    rt = GraphRuntime(graph)
    
    assert rt.graph == graph
    assert rt.max_iterations == 20


@pytest.mark.asyncio
async def test_graph_runtime_parse_intent():
    """Test runtime execution stops at unknown action"""
    rt = GraphRuntime(graph)
    result = await rt.run({"text": "do something random"})
    
    assert result["action"] == "unknown"
    assert "final_output" in result or "message" in result


@pytest.mark.asyncio
async def test_graph_runtime_max_iterations():
    """Test that runtime has safety limit"""
    rt = GraphRuntime(graph)
    
    # Should not run forever
    result = await rt.run({"text": "cancel trip"})
    assert "final_output" in result or "error" in result


# ============================================================================
# Integration Tests (Basic Flow)
# ============================================================================

@pytest.mark.asyncio
async def test_agent_unknown_action_flow():
    """Test end-to-end flow for unknown action"""
    rt = GraphRuntime(graph)
    result = await rt.run({
        "text": "do something weird",
        "user_id": 1
    })
    
    assert "action" in result
    assert result["action"] == "unknown"


@pytest.mark.asyncio
async def test_agent_error_handling():
    """Test that agent handles errors gracefully"""
    rt = GraphRuntime(graph)
    result = await rt.run({
        "text": "",
        "user_id": 1
    })
    
    # Should not crash, should return some output
    assert "action" in result or "error" in result


# ============================================================================
# Graph Structure Tests
# ============================================================================

def test_graph_has_required_nodes():
    """Test that graph has all required nodes"""
    required_nodes = [
        "parse_intent",
        "resolve_target",
        "check_consequences",
        "get_confirmation",
        "execute_action",
        "report_result",
        "fallback"
    ]
    
    for node in required_nodes:
        assert node in graph.nodes, f"Node '{node}' not found in graph"


def test_graph_has_edges():
    """Test that graph has edge connections"""
    assert len(graph.edges) > 0, "Graph has no edges defined"


def test_graph_parse_intent_connected():
    """Test that parse_intent has outgoing edges"""
    assert "parse_intent" in graph.edges
    assert len(graph.edges["parse_intent"]) > 0


# ============================================================================
# Utility Functions
# ============================================================================

def test_graph_get_next_node():
    """Test graph.get_next_node logic"""
    # Test with a state that should go from parse_intent to resolve_target
    state = {"action": "remove_vehicle", "trip_id": None}
    next_node = graph.get_next_node("parse_intent", state)
    
    assert next_node == "resolve_target"


# ============================================================================
# Run all tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
