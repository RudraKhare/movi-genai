#!/usr/bin/env python3
"""
Test vehicle assignment after removal
"""

import requests
import json
import uuid

# Configuration  
API_BASE = "http://localhost:8000"
API_KEY = "dev-key-change-in-production"

def test_full_vehicle_flow():
    """Test remove vehicle then assign new vehicle"""
    print("🧪 Testing full vehicle assignment flow...")
    
    # Step 1: Remove vehicle from trip 5
    print("Step 1: Removing vehicle from trip 5...")
    remove_input = {
        "text": "remove vehicle from trip 5",
        "user_id": 1,
        "session_id": str(uuid.uuid4())
    }
    
    try:
        response = requests.post(f"{API_BASE}/api/agent/message", json=remove_input,
                               headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
                               timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            agent_output = result.get("agent_output", {})
            print(f"   Remove status: {agent_output.get('status')}")
            print(f"   Remove message: {agent_output.get('message', '')[:80]}...")
            
            if agent_output.get("status") != "failed":
                # Step 2: Assign new vehicle
                print("\nStep 2: Assigning new vehicle...")
                assign_input = {
                    "text": "STRUCTURED_CMD:assign_vehicle|trip_id:5|vehicle_id:2|vehicle_name:TN01XY9999|driver_id:6|context:selection_ui",
                    "user_id": 1,
                    "session_id": str(uuid.uuid4())
                }
                
                assign_response = requests.post(f"{API_BASE}/api/agent/message", json=assign_input,
                                              headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
                                              timeout=15)
                
                if assign_response.status_code == 200:
                    assign_result = assign_response.json()
                    assign_output = assign_result.get("agent_output", {})
                    
                    print(f"   Assign status: {assign_output.get('status')}")
                    print(f"   Assign message: {assign_output.get('message', '')}")
                    
                    # Check if vehicle name appears
                    message = assign_output.get('message', '')
                    if "TN01XY9999" in message:
                        print("✅ Vehicle name found in structured command response!")
                        return True
                    else:
                        print(f"❌ Vehicle name not found in: {message}")
                        return False
                else:
                    print(f"❌ Assign request failed: {assign_response.status_code}")
                    return False
            else:
                print(f"❌ Remove failed: {agent_output.get('message')}")
                return False
        else:
            print(f"❌ Remove request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_full_vehicle_flow()
    print(f"\n🎯 Overall result: {'✅ SUCCESS' if success else '❌ FAILED'}")
