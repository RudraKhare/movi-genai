#!/usr/bin/env python3
"""
Debugging script for structured vehicle command
"""

import requests
import json
import uuid

# Configuration
API_BASE = "http://localhost:8000"
API_KEY = "dev-key-change-in-production"

def debug_structured_vehicle():
    """Debug structured vehicle command"""
    print("🔍 Debugging structured vehicle command...")
    
    test_input = {
        "text": "STRUCTURED_CMD:assign_vehicle|trip_id:3|vehicle_id:1|vehicle_name:TN01AB1234|driver_id:5|context:selection_ui",
        "user_id": 1,
        "session_id": str(uuid.uuid4())
    }
    
    try:
        response = requests.post(f"{API_BASE}/api/agent/message", json=test_input,
                               headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
                               timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            print(f"Full response:")
            print(json.dumps(result, indent=2))
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    debug_structured_vehicle()
