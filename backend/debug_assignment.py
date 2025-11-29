#!/usr/bin/env python3
"""
Debug script to see exact error details
"""

import requests
import json
import uuid

# Configuration  
API_BASE = "http://localhost:8000"
API_KEY = "dev-key-change-in-production"

def debug_assignment_error():
    """Debug the exact error in vehicle assignment"""
    print("🔍 Debugging vehicle assignment error...")
    
    test_input = {
        "text": "STRUCTURED_CMD:assign_vehicle|trip_id:5|vehicle_id:2|vehicle_name:TN01XY9999|driver_id:6|context:selection_ui",
        "user_id": 1,
        "session_id": str(uuid.uuid4())
    }
    
    try:
        response = requests.post(f"{API_BASE}/api/agent/message", json=test_input,
                               headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
                               timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            print("📋 Full Response:")
            print(json.dumps(result, indent=2))
            
            # Look specifically at execution_result for detailed error
            agent_output = result.get("agent_output", {})
            execution_result = agent_output.get("execution_result", {})
            
            if execution_result:
                print(f"\n🎯 Execution Result Details:")
                print(f"   OK: {execution_result.get('ok')}")
                print(f"   Message: {execution_result.get('message')}")
                print(f"   Action: {execution_result.get('action')}")
                
                # Check if it mentions the int conversion error
                error_msg = execution_result.get('message', '').lower()
                if "str' object cannot be interpreted as an integer" in error_msg:
                    print("❌ CONFIRMED: asyncpg int conversion error still present")
                elif "object cannot be interpreted" in error_msg:
                    print("❌ LIKELY: asyncpg type conversion error")
                else:
                    print("✅ No asyncpg int conversion error detected")
                    print(f"   Actual error: {execution_result.get('message')}")
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Debug failed: {e}")

if __name__ == "__main__":
    debug_assignment_error()
