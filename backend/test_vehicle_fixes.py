#!/usr/bin/env python3
"""
Test script for vehicle assignment after driver assignment issue (Fix 1)
"""

import requests
import json
import uuid
from datetime import datetime

# Configuration
API_BASE = "http://localhost:8000"
API_KEY = "dev-key-change-in-production"

def test_vehicle_assignment_after_driver():
    """Test that vehicle assignment is rejected when trip already has deployment"""
    print("🧪 Testing vehicle assignment after driver assignment...")
    
    # Step 1: First assign a driver to trip 1
    driver_assignment = {
        "text": "STRUCTURED_CMD:assign_driver|trip_id:1|driver_id:3|driver_name:Anil|context:selection_ui",
        "user_id": 1,
        "session_id": str(uuid.uuid4())
    }
    
    try:
        response = requests.post(f"{API_BASE}/api/agent/message", json=driver_assignment,
                               headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
                               timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Driver assignment successful")
            
            # Step 2: Now try to assign vehicle to same trip
            vehicle_assignment = {
                "text": "assign vehicle to trip 1",
                "user_id": 1,
                "session_id": str(uuid.uuid4())
            }
            
            vehicle_response = requests.post(f"{API_BASE}/api/agent/message", json=vehicle_assignment,
                                           headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
                                           timeout=15)
            
            if vehicle_response.status_code == 200:
                vehicle_result = vehicle_response.json()
                agent_output = vehicle_result.get("agent_output", {})
                
                print(f"📝 Vehicle assignment response:")
                print(f"   Status: {agent_output.get('status')}")
                print(f"   Error: {agent_output.get('error')}")
                print(f"   Message: {agent_output.get('message', '')[:100]}...")
                
                # Check if properly rejected
                if agent_output.get("error") == "already_deployed":
                    print("✅ Vehicle assignment properly rejected - trip already has deployment")
                    return True
                else:
                    print("❌ Vehicle assignment should have been rejected")
                    return False
            else:
                print(f"❌ Vehicle assignment request failed: {vehicle_response.status_code}")
                return False
                
        else:
            print(f"❌ Driver assignment failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_structured_vehicle_command():
    """Test structured vehicle command with proper vehicle name"""
    print("\n🧪 Testing structured vehicle command...")
    
    test_input = {
        "text": "STRUCTURED_CMD:assign_vehicle|trip_id:2|vehicle_id:1|vehicle_name:TN01AB1234|driver_id:5|context:selection_ui",
        "user_id": 1,
        "session_id": str(uuid.uuid4())
    }
    
    try:
        response = requests.post(f"{API_BASE}/api/agent/message", json=test_input,
                               headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
                               timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            agent_output = result.get("agent_output", {})
            
            print(f"📝 Response:")
            print(f"   Action: {agent_output.get('action')}")
            print(f"   Status: {agent_output.get('status')}")
            print(f"   Message: {agent_output.get('message', '')}")
            
            # Check if vehicle name is preserved properly
            message = agent_output.get('message', '')
            if "TN01AB1234" in message or "tn01ab1234" in message.lower():
                print("✅ Vehicle name properly preserved in structured command")
                return True
            else:
                print("❌ Vehicle name not found in response message")
                return False
        else:
            print(f"❌ Request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Vehicle Assignment Fix Validation")
    print(f"⏰ {datetime.now().isoformat()}")
    print("=" * 60)
    
    test1_result = test_vehicle_assignment_after_driver()
    test2_result = test_structured_vehicle_command()
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    print(f"1. Vehicle assignment after driver: {'✅ PASS' if test1_result else '❌ FAIL'}")
    print(f"2. Structured vehicle command: {'✅ PASS' if test2_result else '❌ FAIL'}")
    
    if test1_result and test2_result:
        print("🎉 All vehicle assignment fixes working correctly!")
    else:
        print("⚠️ Some fixes need attention.")
