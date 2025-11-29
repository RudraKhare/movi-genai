#!/usr/bin/env python3
"""
Test vehicle assignment with an available driver
"""

import requests
import json
import uuid

# Configuration  
API_BASE = "http://localhost:8000"
API_KEY = "dev-key-change-in-production"

def test_with_available_driver():
    """Test vehicle assignment using an available driver"""
    print("🧪 Testing vehicle assignment with available driver...")
    
    # First, let's get available drivers for trip 5
    print("Step 1: Getting available drivers for trip 5...")
    drivers_input = {
        "text": "assign driver to trip 5",
        "user_id": 1,
        "selectedTripId": 5,
        "session_id": str(uuid.uuid4())
    }
    
    try:
        response = requests.post(f"{API_BASE}/api/agent/message", json=drivers_input,
                               headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
                               timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            options = result.get("agent_output", {}).get("options", [])
            
            if options:
                available_driver = options[0]  # Take first available driver
                driver_id = available_driver["driver_id"]
                driver_name = available_driver["driver_name"]
                
                print(f"   Found available driver: {driver_name} (ID: {driver_id})")
                
                # Step 2: Test vehicle assignment with this available driver
                print(f"Step 2: Testing vehicle assignment with driver {driver_name}...")
                
                assign_input = {
                    "text": f"STRUCTURED_CMD:assign_vehicle|trip_id:5|vehicle_id:2|vehicle_name:TN01XY9999|driver_id:{driver_id}|context:selection_ui",
                    "user_id": 1,
                    "session_id": str(uuid.uuid4())
                }
                
                assign_response = requests.post(f"{API_BASE}/api/agent/message", json=assign_input,
                                              headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
                                              timeout=15)
                
                if assign_response.status_code == 200:
                    assign_result = assign_response.json()
                    assign_output = assign_result.get("agent_output", {})
                    execution_result = assign_output.get("execution_result", {})
                    
                    print(f"📝 Vehicle Assignment Result:")
                    print(f"   Status: {assign_output.get('status')}")
                    print(f"   Message: {assign_output.get('message')}")
                    print(f"   Execution OK: {execution_result.get('ok')}")
                    print(f"   Execution Message: {execution_result.get('message')}")
                    
                    # Check for success
                    if execution_result.get('ok') and assign_output.get('status') != 'failed':
                        print("✅ COMPLETE SUCCESS: String to int conversion + vehicle assignment working!")
                        
                        # Check if vehicle name is displayed
                        if "TN01XY9999" in assign_output.get('message', ''):
                            print("✅ BONUS: Vehicle name properly displayed in success message!")
                        
                        return True
                    else:
                        print(f"❌ Assignment failed: {execution_result.get('message')}")
                        
                        # Check if it's still the int conversion error
                        error_msg = execution_result.get('message', '').lower()
                        if "str' object cannot be interpreted" in error_msg:
                            print("❌ Int conversion fix not working")
                        else:
                            print("✅ Int conversion working, but other business logic issue")
                        return False
                else:
                    print(f"❌ Assignment request failed: {assign_response.status_code}")
                    return False
            else:
                print("   No available drivers found - cannot test")
                return False
        else:
            print(f"❌ Failed to get drivers: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Vehicle Assignment with Available Driver Test")
    print("=" * 60)
    
    success = test_with_available_driver()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 STRING TO INT CONVERSION FIX CONFIRMED WORKING!")
        print("   ✅ No more asyncpg type conversion errors")
        print("   ✅ Structured commands now pass integers to service layer")
        print("   ✅ Vehicle assignment working end-to-end")
    else:
        print("⚠️ Need to investigate further...")
