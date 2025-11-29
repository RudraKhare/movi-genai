#!/usr/bin/env python3
"""
Test script for context-aware natural language implementation
Tests the enhanced MOVI capabilities for handling vague/casual inputs
"""

import asyncio
import requests
import json
import uuid
from datetime import datetime

# Configuration
API_BASE = "http://localhost:5007"
API_KEY = "your-api-key"

# Test scenarios for context-aware implementation
TEST_SCENARIOS = [
    {
        "name": "Vague Assignment with UI Context",
        "description": "User says 'assign driver' while having a trip selected in UI",
        "input": {
            "text": "assign driver",
            "user_id": 1,
            "selectedTripId": 1,  # Trip is selected in UI
            "from_image": False,
            "conversation_history": []
        },
        "expected": {
            "should_succeed": True,
            "action": "assign_driver",
            "uses_context": True
        }
    },
    {
        "name": "Casual Language with Context",
        "description": "User says 'put someone on this' with trip selected",
        "input": {
            "text": "put someone on this",
            "user_id": 1,
            "selectedTripId": 1,
            "from_image": False,
            "conversation_history": []
        },
        "expected": {
            "should_succeed": True,
            "action": "assign_driver",
            "uses_context": True
        }
    },
    {
        "name": "Hinglish Input",
        "description": "User says 'driver dal do' (mix of English and Hindi)",
        "input": {
            "text": "driver dal do",
            "user_id": 1,
            "selectedTripId": 1,
            "from_image": False,
            "conversation_history": []
        },
        "expected": {
            "should_succeed": True,
            "action": "assign_driver",
            "uses_context": True
        }
    },
    {
        "name": "Structured Command from UI",
        "description": "Frontend sends structured command when user clicks driver option",
        "input": {
            "text": "STRUCTURED_CMD:assign_driver|trip_id:1|driver_id:2|driver_name:John Doe|context:selection_ui",
            "user_id": 1,
            "from_image": False,
            "conversation_history": []
        },
        "expected": {
            "should_succeed": True,
            "action": "assign_driver",
            "uses_structured": True
        }
    },
    {
        "name": "Conversational Follow-up",
        "description": "User refers to previous context with 'okay assign him'",
        "input": {
            "text": "okay assign him",
            "user_id": 1,
            "selectedTripId": 1,
            "from_image": False,
            "conversation_history": [
                {"role": "user", "content": "who are the available drivers?", "timestamp": "2024-01-01T10:00:00Z"},
                {"role": "agent", "content": "Here are the available drivers: John Doe, Jane Smith", "timestamp": "2024-01-01T10:00:01Z"}
            ]
        },
        "expected": {
            "should_succeed": True,
            "action": "assign_driver",
            "uses_context": True,
            "uses_history": True
        }
    }
]

def print_test_header(scenario_name, description):
    """Print a formatted test header"""
    print(f"\n{'='*80}")
    print(f"🧪 TEST: {scenario_name}")
    print(f"📝 {description}")
    print('='*80)

def print_result(passed, message):
    """Print test result with emoji"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {message}")

async def test_agent_endpoint(test_input):
    """Send request to agent endpoint and return response"""
    try:
        response = requests.post(
            f"{API_BASE}/agent",
            json=test_input,
            headers={
                "x-api-key": API_KEY,
                "Content-Type": "application/json"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"HTTP {response.status_code}: {response.text}"
            
    except requests.exceptions.RequestException as e:
        return None, f"Request failed: {str(e)}"

async def run_context_aware_tests():
    """Run all context-aware implementation tests"""
    
    print("🚀 Starting Context-Aware Natural Language Tests")
    print(f"⏰ Test started at: {datetime.now().isoformat()}")
    
    total_tests = len(TEST_SCENARIOS)
    passed_tests = 0
    
    for i, scenario in enumerate(TEST_SCENARIOS, 1):
        print_test_header(scenario["name"], scenario["description"])
        
        # Add session_id to test input
        test_input = scenario["input"].copy()
        test_input["session_id"] = str(uuid.uuid4())
        
        print(f"📤 Sending request:")
        print(f"   Text: '{test_input['text']}'")
        print(f"   Selected Trip ID: {test_input.get('selectedTripId', 'None')}")
        print(f"   History Length: {len(test_input.get('conversation_history', []))}")
        
        # Send request
        response_data, error = await test_agent_endpoint(test_input)
        
        if error:
            print_result(False, f"Request failed: {error}")
            continue
        
        # Extract response details
        agent_output = response_data.get("agent_output", {})
        action = agent_output.get("action", "unknown")
        status = agent_output.get("status", "unknown")
        source = agent_output.get("source", "unknown")
        confidence = agent_output.get("confidence", 0.0)
        
        print(f"📥 Response received:")
        print(f"   Action: {action}")
        print(f"   Status: {status}")
        print(f"   Source: {source}")
        print(f"   Confidence: {confidence}")
        
        # Validate response
        expected = scenario["expected"]
        test_passed = True
        
        # Check if action matches expected
        if expected.get("should_succeed"):
            if action != expected.get("action"):
                print_result(False, f"Expected action '{expected['action']}' but got '{action}'")
                test_passed = False
            elif status == "error":
                print_result(False, f"Request failed with status: {status}")
                test_passed = False
            else:
                print_result(True, f"Successfully parsed action: {action}")
        
        # Check context usage
        if expected.get("uses_context") and not agent_output.get("selectedTripId"):
            print_result(False, "Expected context usage but selectedTripId not found in response")
            test_passed = False
        
        # Check structured command handling
        if expected.get("uses_structured") and source != "structured_command":
            print_result(False, f"Expected structured command source but got: {source}")
            test_passed = False
        
        # Check conversation history usage
        if expected.get("uses_history") and confidence < 0.7:
            print_result(False, f"Expected high confidence from conversation history but got: {confidence}")
            test_passed = False
        
        if test_passed:
            passed_tests += 1
            print_result(True, f"Test scenario passed ({i}/{total_tests})")
        else:
            print_result(False, f"Test scenario failed ({i}/{total_tests})")
    
    # Print summary
    print(f"\n{'='*80}")
    print(f"📊 TEST SUMMARY")
    print(f"{'='*80}")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print(f"🎉 All tests passed! Context-aware implementation is working correctly.")
    else:
        print(f"⚠️  Some tests failed. Review the implementation for improvements.")

if __name__ == "__main__":
    asyncio.run(run_context_aware_tests())
