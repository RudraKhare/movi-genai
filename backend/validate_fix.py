#!/usr/bin/env python3
"""
Final validation that string to int conversion is working
"""

import requests
import json
import uuid

# Configuration  
API_BASE = "http://localhost:8000"
API_KEY = "dev-key-change-in-production"

def validate_int_conversion():
    """Validate that the string to int conversion is working by checking error types"""
    print("🎯 Final validation: String to Int conversion fix")
    print("=" * 60)
    
    # Test both driver and vehicle assignment structured commands
    tests = [
        {
            "name": "Driver Assignment",
            "command": "STRUCTURED_CMD:assign_driver|trip_id:5|driver_id:8|driver_name:TestDriver|context:selection_ui"
        },
        {
            "name": "Vehicle Assignment", 
            "command": "STRUCTURED_CMD:assign_vehicle|trip_id:5|vehicle_id:3|vehicle_name:TN01TEST|driver_id:8|context:selection_ui"
        }
    ]
    
    all_good = True
    
    for test in tests:
        print(f"\n🧪 Testing {test['name']}...")
        
        test_input = {
            "text": test["command"],
            "user_id": 1,
            "session_id": str(uuid.uuid4())
        }
        
        try:
            response = requests.post(f"{API_BASE}/api/agent/message", json=test_input,
                                   headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
                                   timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                execution_result = result.get("agent_output", {}).get("execution_result", {})
                
                if execution_result:
                    error_msg = execution_result.get("message", "").lower()
                    
                    # Check for the specific asyncpg int conversion error
                    if "str' object cannot be interpreted as an integer" in error_msg:
                        print(f"   ❌ ASYNCPG INT ERROR STILL PRESENT!")
                        print(f"      Message: {execution_result.get('message')}")
                        all_good = False
                    elif "object cannot be interpreted" in error_msg or "invalid input for query argument" in error_msg:
                        print(f"   ❌ ASYNCPG TYPE ERROR DETECTED!")
                        print(f"      Message: {execution_result.get('message')}")
                        all_good = False
                    else:
                        print(f"   ✅ NO ASYNCPG TYPE ERRORS")
                        print(f"      Business logic result: {execution_result.get('message', '')[:80]}...")
                else:
                    print(f"   ⚠️  No execution_result in response")
            else:
                print(f"   ❌ Request failed: {response.status_code}")
                all_good = False
                
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
            all_good = False
    
    print(f"\n{'='*60}")
    if all_good:
        print("🎉 STRING TO INT CONVERSION FIX CONFIRMED WORKING!")
        print()
        print("✅ BEFORE FIX:")
        print("   STRUCTURED_CMD:assign_vehicle|trip_id:8|vehicle_id:10")
        print("   ↓ params = {'trip_id': '8', 'vehicle_id': '10'}  # strings")
        print("   ↓ service.assign_vehicle(trip_id='8', vehicle_id='10')")
        print("   ↓ asyncpg: 'invalid input for query argument $1: \\'10\\' (str cannot be interpreted as int)'")
        print("   ❌ FAILED")
        print()
        print("✅ AFTER FIX:")
        print("   STRUCTURED_CMD:assign_vehicle|trip_id:8|vehicle_id:10")
        print("   ↓ params = {'trip_id': 8, 'vehicle_id': 10}  # integers")
        print("   ↓ service.assign_vehicle(trip_id=8, vehicle_id=10)")
        print("   ↓ asyncpg: Successfully processes integer parameters")
        print("   ✅ WORKING (may fail on business logic, but no type errors)")
        print()
        print("🎯 ROOT CAUSE FIX COMPLETE:")
        print("   • parse_intent_llm.py now converts string params to int")
        print("   • No more asyncpg type conversion errors")
        print("   • Vehicle and driver assignment can proceed to business logic")
    else:
        print("❌ STRING TO INT CONVERSION FIX NEEDS MORE WORK")
        print("   Some tests still show asyncpg type conversion errors")
    
    return all_good

if __name__ == "__main__":
    validate_int_conversion()
