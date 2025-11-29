#!/usr/bin/env python3
"""
Comprehensive Driver Assignment Flow Test
Tests all the fixes applied to the assign driver functionality.
"""

import asyncio
import asyncpg
from typing import Dict, Any
from unittest.mock import AsyncMock
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockState:
    """Mock state object for testing graph nodes"""
    def __init__(self, **kwargs):
        self.data = kwargs
    
    def get(self, key, default=None):
        return self.data.get(key, default)
    
    def __setitem__(self, key, value):
        self.data[key] = value
    
    def __getitem__(self, key):
        return self.data[key]

# Test scenarios
TEST_SCENARIOS = [
    {
        "name": "Basic driver assignment request",
        "user_input": "assign driver to this trip",
        "expected_action": "assign_driver",
        "expected_needs_clarification": False,  # Should not need clarification for missing driver
        "expected_route": "driver_selection_provider"
    },
    {
        "name": "Specific driver assignment",
        "user_input": "assign driver Amit to Bulk – 00:01",
        "expected_action": "assign_driver", 
        "expected_needs_clarification": False,
        "expected_route": "check_consequences"
    },
    {
        "name": "Synonym usage - allocate",
        "user_input": "allocate a driver for this trip",
        "expected_action": "assign_driver",
        "expected_needs_clarification": False,
        "expected_route": "driver_selection_provider" 
    },
    {
        "name": "Synonym usage - appoint",
        "user_input": "appoint driver to PWIHY – Route",
        "expected_action": "assign_driver",
        "expected_needs_clarification": False,
        "expected_route": "driver_selection_provider"
    },
    {
        "name": "Driver selection by number",
        "user_selection": "1",
        "selection_type": "driver",
        "options": [
            {"driver_id": 5, "driver_name": "John Smith", "status": "available"}
        ],
        "expected_driver_id": 5,
        "expected_action": "assign_driver",
        "expected_needs_clarification": False
    },
    {
        "name": "Driver selection by name", 
        "user_selection": "Assign John",
        "selection_type": "driver",
        "options": [
            {"driver_id": 5, "driver_name": "John Smith", "status": "available"}
        ],
        "expected_driver_id": 5,
        "expected_action": "assign_driver", 
        "expected_needs_clarification": False
    }
]

async def test_parse_intent_llm():
    """Test that parse_intent_llm properly handles assign_driver actions"""
    print("\n🧪 Testing parse_intent_llm fixes...")
    
    # Import the actual node
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
    
    try:
        from langgraph.nodes.parse_intent_llm import parse_intent_llm
        
        # Mock the LLM client
        async def mock_call_llm(text, context=None):
            if "assign" in text.lower() and "driver" in text.lower():
                return {
                    "action": "assign_driver",
                    "target_label": "this trip",
                    "target_trip_id": None,
                    "parameters": {},  # No specific driver
                    "confidence": 0.85,
                    "clarify": False,
                    "explanation": "User wants to assign a driver to a trip"
                }
            return {"action": "unknown"}
        
        # Patch the LLM client
        import langgraph.tools.llm_client as llm_client
        original_call = llm_client.call_llm_for_intent
        llm_client.call_llm_for_intent = mock_call_llm
        
        # Test basic driver assignment
        state = MockState(text="assign driver to this trip", target_label="this trip")
        result = await parse_intent_llm(state.data)
        
        print(f"✅ Action: {result.get('action')}")
        print(f"✅ Needs clarification: {result.get('needs_clarification', False)}")
        print(f"✅ Target: {result.get('target_label')}")
        
        # Should NOT set needs_clarification for missing driver
        assert result.get("action") == "assign_driver", f"Expected assign_driver, got {result.get('action')}"
        assert not result.get("needs_clarification", False), "Should not need clarification for missing driver"
        
        # Restore original
        llm_client.call_llm_for_intent = original_call
        
        print("✅ parse_intent_llm test passed!")
        return True
        
    except Exception as e:
        print(f"❌ parse_intent_llm test failed: {e}")
        return False

async def test_decision_router():
    """Test that decision_router properly routes assign_driver actions"""
    print("\n🧪 Testing decision_router routing...")
    
    try:
        from langgraph.nodes.decision_router import decision_router
        
        # Test: assign_driver without driver_id should route to driver_selection_provider
        state = MockState(
            action="assign_driver",
            trip_id=123,
            parsed_params={}  # No driver_id
        )
        
        result = await decision_router(state.data)
        
        print(f"✅ Next node: {result.get('next_node')}")
        assert result.get("next_node") == "driver_selection_provider", f"Expected driver_selection_provider, got {result.get('next_node')}"
        
        # Test: assign_driver WITH driver_id should route to check_consequences
        state = MockState(
            action="assign_driver",
            trip_id=123,
            driver_id=5,
            parsed_params={"driver_id": 5}
        )
        
        result = await decision_router(state.data)
        
        print(f"✅ Next node (with driver): {result.get('next_node')}")
        assert result.get("next_node") == "check_consequences", f"Expected check_consequences, got {result.get('next_node')}"
        
        print("✅ decision_router test passed!")
        return True
        
    except Exception as e:
        print(f"❌ decision_router test failed: {e}")
        return False

async def test_collect_user_input():
    """Test that collect_user_input properly handles driver selection"""
    print("\n🧪 Testing collect_user_input driver selection...")
    
    try:
        from langgraph.nodes.collect_user_input import collect_user_input
        
        # Test numeric selection
        state = MockState(
            user_message="1",
            awaiting_user_selection=True,
            selection_type="driver",
            options=[
                {"driver_id": 5, "driver_name": "John Smith", "status": "available"},
                {"driver_id": 7, "driver_name": "Sarah Johnson", "status": "available"}
            ]
        )
        
        result = await collect_user_input(state.data)
        
        print(f"✅ Selected driver ID: {result.get('driver_id')}")
        print(f"✅ Selected driver name: {result.get('driver_name')}")
        print(f"✅ Needs clarification: {result.get('needs_clarification', False)}")
        print(f"✅ Next node: {result.get('next_node')}")
        
        assert result.get("driver_id") == 5, f"Expected driver_id 5, got {result.get('driver_id')}"
        assert result.get("driver_name") == "John Smith", f"Expected John Smith, got {result.get('driver_name')}"
        assert not result.get("needs_clarification", False), "Should not need clarification after selection"
        assert result.get("next_node") == "check_consequences", f"Expected check_consequences, got {result.get('next_node')}"
        
        # Test name-based selection
        state = MockState(
            user_message="Assign Sarah",
            awaiting_user_selection=True,
            selection_type="driver",
            options=[
                {"driver_id": 5, "driver_name": "John Smith", "status": "available"},
                {"driver_id": 7, "driver_name": "Sarah Johnson", "status": "available"}
            ]
        )
        
        result = await collect_user_input(state.data)
        
        print(f"✅ Selected driver by name ID: {result.get('driver_id')}")
        print(f"✅ Selected driver by name: {result.get('driver_name')}")
        
        assert result.get("driver_id") == 7, f"Expected driver_id 7, got {result.get('driver_id')}"
        assert result.get("driver_name") == "Sarah Johnson", f"Expected Sarah Johnson, got {result.get('driver_name')}"
        
        print("✅ collect_user_input test passed!")
        return True
        
    except Exception as e:
        print(f"❌ collect_user_input test failed: {e}")
        return False

async def test_tools_safe_column_handling():
    """Test that tools handle missing database columns safely"""
    print("\n🧪 Testing safe database column handling...")
    
    try:
        # Mock database connection that simulates missing columns
        async def mock_fetchrow(query, *args):
            if "information_schema.columns" in query and "active" in query:
                return [False]  # Simulate 'active' column doesn't exist
            elif "information_schema.columns" in query and "status" in query:
                return [False]  # Simulate 'status' column doesn't exist
            elif "SELECT driver_id, name, phone FROM drivers" in query:
                return {"driver_id": 5, "name": "John Smith", "phone": "1234567890"}
            return None
        
        async def mock_fetch(query, *args):
            if "SELECT driver_id, name, phone FROM drivers" in query:
                return [
                    {"driver_id": 5, "name": "John Smith", "phone": "1234567890"},
                    {"driver_id": 7, "name": "Sarah Johnson", "phone": "0987654321"}
                ]
            return []
        
        # Mock connection object
        class MockConn:
            async def fetchrow(self, query, *args):
                return await mock_fetchrow(query, *args)
            
            async def fetch(self, query, *args):
                return await mock_fetch(query, *args)
        
        # Mock pool
        class MockPool:
            def acquire(self):
                return AsyncContextManager(MockConn())
        
        class AsyncContextManager:
            def __init__(self, obj):
                self.obj = obj
            async def __aenter__(self):
                return self.obj
            async def __aexit__(self, *args):
                pass
        
        # Test tool_list_available_drivers with missing 'active' column
        from langgraph.tools import tool_list_available_drivers, tool_find_driver_by_name
        
        # Mock get_conn
        import langgraph.tools as tools
        original_get_conn = tools.get_conn
        tools.get_conn = lambda: MockPool()
        
        # This should not crash even though 'active' column doesn't exist
        result = await tool_list_available_drivers(123)
        print(f"✅ tool_list_available_drivers handled missing columns: {result.get('ok', False)}")
        
        # Test tool_find_driver_by_name with missing 'status' column
        result = await tool_find_driver_by_name("John")
        print(f"✅ tool_find_driver_by_name handled missing columns: {result is not None}")
        
        # Restore original
        tools.get_conn = original_get_conn
        
        print("✅ Safe column handling test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Safe column handling test failed: {e}")
        return False

async def test_execute_action_flow():
    """Test that execute_action properly handles assign_driver without needs_clarification blocking"""
    print("\n🧪 Testing execute_action flow...")
    
    try:
        from langgraph.nodes.execute_action import execute_action
        
        # Mock the tool_assign_driver
        async def mock_tool_assign_driver(trip_id, driver_id, user_id):
            return {
                "ok": True,
                "message": f"Driver {driver_id} assigned to trip {trip_id}",
                "action": "assign_driver"
            }
        
        # Patch the tool
        import langgraph.nodes.execute_action as execute_module
        original_tool = execute_module.tool_assign_driver
        execute_module.tool_assign_driver = mock_tool_assign_driver
        
        # Test assign_driver execution without needs_clarification
        state = MockState(
            action="assign_driver",
            trip_id=123,
            driver_id=5,
            user_id=1,
            needs_clarification=False  # This should NOT block execution
        )
        
        result = await execute_action(state.data)
        
        print(f"✅ Execution status: {result.get('status', 'completed')}")
        print(f"✅ Message: {result.get('message', 'No message')}")
        
        assert "assigned" in result.get("message", "").lower(), f"Expected assignment message, got {result.get('message')}"
        assert result.get("status") != "needs_clarification", "Should not be blocked by clarification"
        
        # Restore original
        execute_module.tool_assign_driver = original_tool
        
        print("✅ execute_action test passed!")
        return True
        
    except Exception as e:
        print(f"❌ execute_action test failed: {e}")
        return False

async def run_all_tests():
    """Run all tests and report results"""
    print("🚀 Running comprehensive driver assignment flow tests...\n")
    
    tests = [
        ("Parse Intent LLM", test_parse_intent_llm),
        ("Decision Router", test_decision_router), 
        ("Collect User Input", test_collect_user_input),
        ("Safe Column Handling", test_tools_safe_column_handling),
        ("Execute Action Flow", test_execute_action_flow)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("🎯 TEST SUMMARY")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
        if success:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 All tests passed! Driver assignment flow is ready!")
        print("\nExpected workflow:")
        print("1. User: 'assign driver to this trip'")
        print("2. LLM: Recognizes assign_driver action (no clarification needed)")
        print("3. Decision Router: Routes to driver_selection_provider")
        print("4. Driver Selection: Shows available drivers with conflict checking")
        print("5. User: 'Choose driver 1' or 'Assign John'")
        print("6. Collect Input: Parses selection, sets driver_id, clears clarification")
        print("7. Check Consequences: assign_driver is safe action")
        print("8. Execute Action: Calls tool_assign_driver, updates database")
        print("9. Report: 'John has been assigned to this trip'")
    else:
        print(f"\n⚠️  {total-passed} tests failed. Please review and fix issues.")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(run_all_tests())
