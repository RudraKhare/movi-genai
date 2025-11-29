#!/usr/bin/env python3
"""
Find a trip without deployment to test vehicle assignment
"""

import requests
import json

# Configuration  
API_BASE = "http://localhost:8000"
API_KEY = "dev-key-change-in-production"

def find_empty_trip():
    """Find a trip without deployment"""
    print("🔍 Looking for trips without deployments...")
    
    # First, let's see what trips exist  
    test_input = {
        "text": "get trip status for trip 5",
        "user_id": 1,
    }
    
    try:
        response = requests.post(f"{API_BASE}/api/agent/message", json=test_input,
                               headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
                               timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            print("Trip 5 status:")
            print(json.dumps(result, indent=2))
        else:
            print(f"Failed to get trip status: {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")

def test_vehicle_on_trip_5():
    """Test vehicle assignment on trip 5"""
    print("\n🧪 Testing vehicle assignment on trip 5...")
    
    test_input = {
        "text": "STRUCTURED_CMD:assign_vehicle|trip_id:5|vehicle_id:2|vehicle_name:TN01XY9999|driver_id:6|context:selection_ui",
        "user_id": 1,
    }
    
    try:
        response = requests.post(f"{API_BASE}/api/agent/message", json=test_input,
                               headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
                               timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            agent_output = result.get("agent_output", {})
            
            print(f"Response:")
            print(f"   Status: {agent_output.get('status')}")
            print(f"   Message: {agent_output.get('message')}")
            
            # Check if vehicle name appears
            message = agent_output.get('message', '')
            if "TN01XY9999" in message:
                print("✅ Vehicle name found in response!")
                return True
            else:
                print(f"❌ Vehicle name not found. Full message: {message}")
                return False
        else:
            print(f"Failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    find_empty_trip()
    test_vehicle_on_trip_5()
