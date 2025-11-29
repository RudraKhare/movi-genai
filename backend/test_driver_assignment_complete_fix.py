#!/usr/bin/env python3
"""
Comprehensive test script for driver assignment fixes
Tests all the issues mentioned in the original problem
"""

import asyncio
import requests
import json
import uuid
from datetime import datetime

# Configuration
API_BASE = "http://localhost:5007"
API_KEY = "your-api-key"

def print_test_header(test_name, description):
    """Print formatted test header"""
    print(f"\n{'='*80}")
    print(f"🧪 {test_name}")
    print(f"📝 {description}")
    print('='*80)

def print_result(passed, message, details=None):
    """Print test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {message}")
    if details and not passed:
        print(f"   Details: {details}")

async def test_structured_command_flow():
    """Test Fix 1: Structured commands should bypass LLM and go directly to action"""
    print_test_header("TEST 1: Structured Command Flow", 
                     "Verify STRUCTURED_CMD bypasses OCR/LLM and goes directly to execution")
    
    test_input = {
        "text": "STRUCTURED_CMD:assign_driver|trip_id:1|driver_id:2|driver_name:John Doe|context:selection_ui",
        "user_id": 1,
        "session_id": str(uuid.uuid4())
    }
    
    try:
        response = requests.post(f"{API_BASE}/agent", json=test_input, 
                               headers={"x-api-key": API_KEY, "Content-Type": "application/json"}, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            agent_output = result.get("agent_output", {})
            
            # Check expectations
            action = agent_output.get("action")
            source = agent_output.get("source")
            needs_clarification = agent_output.get("needs_clarification", False)
            message = agent_output.get("message", "")
            
            print(f"📥 Response: action={action}, source={source}, clarify={needs_clarification}")
            
            # Test expectations
            tests = [
                (action == "assign_driver", "Action should be assign_driver", f"Got: {action}"),
                (source == "structured_command", "Source should be structured_command", f"Got: {source}"),
                (not needs_clarification, "Should not need clarification", f"Clarify: {needs_clarification}"),
                ("john doe" in message.lower() or "assigned" in message.lower(), "Should mention driver name in result", f"Message: {message}")
            ]
            
            passed_tests = 0
            for test_passes, test_desc, fail_detail in tests:
                print_result(test_passes, test_desc, None if test_passes else fail_detail)
                if test_passes:
                    passed_tests += 1
            
            return passed_tests == len(tests)
            
        else:
            print_result(False, f"HTTP Error {response.status_code}", response.text)
            return False
            
    except Exception as e:
        print_result(False, "Request failed", str(e))
        return False

async def test_context_aware_assignment():
    """Test Fix 2: Context-aware assignment with selectedTripId should work"""
    print_test_header("TEST 2: Context-Aware Assignment", 
                     "Verify 'assign driver' with selectedTripId works without clarification")
    
    test_input = {
        "text": "assign driver",
        "user_id": 1,
        "selectedTripId": 1,
        "session_id": str(uuid.uuid4())
    }
    
    try:
        response = requests.post(f"{API_BASE}/agent", json=test_input, 
                               headers={"x-api-key": API_KEY, "Content-Type": "application/json"}, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            agent_output = result.get("agent_output", {})
            
            action = agent_output.get("action")
            options = agent_output.get("options", [])
            needs_clarification = agent_output.get("needs_clarification", False)
            
            print(f"📥 Response: action={action}, options_count={len(options)}, clarify={needs_clarification}")
            
            # Should show driver options, not ask for trip clarification
            tests = [
                (action == "assign_driver", "Action should be assign_driver", f"Got: {action}"),
                (len(options) > 0, "Should provide driver options", f"Options: {len(options)}"),
                (not needs_clarification, "Should not need clarification (has selectedTripId)", f"Clarify: {needs_clarification}")
            ]
            
            passed_tests = 0
            for test_passes, test_desc, fail_detail in tests:
                print_result(test_passes, test_desc, None if test_passes else fail_detail)
                if test_passes:
                    passed_tests += 1
            
            return passed_tests == len(tests)
            
        else:
            print_result(False, f"HTTP Error {response.status_code}", response.text)
            return False
            
    except Exception as e:
        print_result(False, "Request failed", str(e))
        return False

async def test_driver_availability_logic():
    """Test Fix 3: Driver availability should show correctly available drivers"""
    print_test_header("TEST 3: Driver Availability Logic", 
                     "Verify available drivers shown are actually available for assignment")
    
    # First, get available drivers
    test_input = {
        "text": "assign driver to trip 1", 
        "user_id": 1,
        "session_id": str(uuid.uuid4())
    }
    
    try:
        response = requests.post(f"{API_BASE}/agent", json=test_input, 
                               headers={"x-api-key": API_KEY, "Content-Type": "application/json"}, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            agent_output = result.get("agent_output", {})
            
            options = agent_output.get("options", [])
            print(f"📥 Found {len(options)} available drivers")
            
            if len(options) > 0:
                # Try to assign the first available driver
                first_driver = options[0]
                driver_id = first_driver.get("driver_id")
                driver_name = first_driver.get("driver_name", "Unknown")
                
                print(f"🔄 Testing assignment of {driver_name} (ID: {driver_id})")
                
                assign_input = {
                    "text": f"STRUCTURED_CMD:assign_driver|trip_id:1|driver_id:{driver_id}|driver_name:{driver_name}|context:selection_ui",
                    "user_id": 1,
                    "session_id": str(uuid.uuid4())
                }
                
                assign_response = requests.post(f"{API_BASE}/agent", json=assign_input,
                                              headers={"x-api-key": API_KEY, "Content-Type": "application/json"}, timeout=30)
                
                if assign_response.status_code == 200:
                    assign_result = assign_response.json()
                    assign_output = assign_result.get("agent_output", {})
                    assign_status = assign_output.get("status")
                    assign_message = assign_output.get("message", "")
                    
                    print(f"📥 Assignment result: status={assign_status}")
                    print(f"📝 Message: {assign_message}")
                    
                    # Check if assignment succeeded
                    success = (assign_status != "error" and 
                              "not available" not in assign_message.lower() and
                              "failed" not in assign_message.lower())
                    
                    print_result(success, "Driver shown as available should be assignable", 
                               None if success else assign_message)
                    return success
                else:
                    print_result(False, "Assignment request failed", assign_response.text)
                    return False
            else:
                print_result(True, "No drivers available (this is acceptable)", None)
                return True
                
        else:
            print_result(False, f"HTTP Error {response.status_code}", response.text)
            return False
            
    except Exception as e:
        print_result(False, "Request failed", str(e))
        return False

async def test_no_ocr_override_for_structured():
    """Test Fix 4: OCR should not override structured commands"""
    print_test_header("TEST 4: No OCR Override for Structured Commands", 
                     "Verify structured commands don't get overridden by OCR selectedTripId")
    
    test_input = {
        "text": "STRUCTURED_CMD:assign_driver|trip_id:2|driver_id:3|driver_name:Jane Smith|context:selection_ui",
        "user_id": 1,
        "selectedTripId": 999,  # Different trip ID from OCR/stale context
        "from_image": False,    # Not from current image
        "session_id": str(uuid.uuid4())
    }
    
    try:
        response = requests.post(f"{API_BASE}/agent", json=test_input, 
                               headers={"x-api-key": API_KEY, "Content-Type": "application/json"}, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            agent_output = result.get("agent_output", {})
            
            message = agent_output.get("message", "")
            
            print(f"📥 Response message: {message}")
            
            # Should use trip_id:2 from structured command, not selectedTripId:999
            uses_correct_trip = ("trip 2" in message.lower() or 
                               "trip_id:2" in message or
                               not "trip 999" in message.lower())
            
            print_result(uses_correct_trip, "Should use trip_id from structured command, not OCR", 
                        None if uses_correct_trip else message)
            return uses_correct_trip
            
        else:
            print_result(False, f"HTTP Error {response.status_code}", response.text)
            return False
            
    except Exception as e:
        print_result(False, "Request failed", str(e))
        return False

async def test_casual_language_processing():
    """Test Fix 5: Casual language should work with context"""
    print_test_header("TEST 5: Casual Language Processing", 
                     "Verify casual phrases work with UI context")
    
    casual_phrases = [
        "put someone on this",
        "assign a driver",
        "give this trip a driver",
        "dal do driver"  # Hinglish
    ]
    
    passed_tests = 0
    total_tests = len(casual_phrases)
    
    for phrase in casual_phrases:
        print(f"\n🔤 Testing phrase: '{phrase}'")
        
        test_input = {
            "text": phrase,
            "user_id": 1,
            "selectedTripId": 1,  # Provide context
            "session_id": str(uuid.uuid4())
        }
        
        try:
            response = requests.post(f"{API_BASE}/agent", json=test_input, 
                                   headers={"x-api-key": API_KEY, "Content-Type": "application/json"}, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                agent_output = result.get("agent_output", {})
                
                action = agent_output.get("action")
                needs_clarification = agent_output.get("needs_clarification", False)
                
                # Should recognize as assign_driver action
                success = (action == "assign_driver" and not needs_clarification)
                
                print_result(success, f"Should recognize '{phrase}' as assign_driver", 
                           None if success else f"action={action}, clarify={needs_clarification}")
                
                if success:
                    passed_tests += 1
                    
            else:
                print_result(False, f"HTTP Error {response.status_code}", response.text)
                
        except Exception as e:
            print_result(False, "Request failed", str(e))
    
    return passed_tests == total_tests

async def run_all_tests():
    """Run all driver assignment fix tests"""
    print("🚀 Starting Driver Assignment Fix Validation")
    print(f"⏰ Test started at: {datetime.now().isoformat()}")
    
    tests = [
        ("Structured Command Flow", test_structured_command_flow),
        ("Context-Aware Assignment", test_context_aware_assignment), 
        ("Driver Availability Logic", test_driver_availability_logic),
        ("No OCR Override", test_no_ocr_override_for_structured),
        ("Casual Language Processing", test_casual_language_processing)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🏃 Running {test_name}...")
        try:
            result = await test_func()
            results.append(result)
        except Exception as e:
            print_result(False, f"{test_name} failed with exception", str(e))
            results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(tests)
    
    print(f"\n{'='*80}")
    print(f"📊 TEST SUMMARY")
    print(f"{'='*80}")
    
    for i, (test_name, _) in enumerate(tests):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"{i+1}. {test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 All driver assignment fixes are working correctly!")
    else:
        print("⚠️ Some fixes need attention. Check the failed tests above.")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(run_all_tests())
