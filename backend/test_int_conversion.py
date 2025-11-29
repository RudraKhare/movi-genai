#!/usr/bin/env python3
"""
Test the string to int conversion fix for structured commands
"""

import requests
import json
import uuid

# Configuration  
API_BASE = "http://localhost:8000"
API_KEY = "dev-key-change-in-production"

def test_int_conversion_fix():
    """Test that structured command parameters are properly converted to integers"""
    print("🧪 Testing string to int conversion fix...")
    
    # Step 1: Remove vehicle from a trip first
    print("Step 1: Removing vehicle to make space...")
    remove_input = {
        "text": "STRUCTURED_CMD:remove_vehicle|trip_id:5|context:selection_ui",
        "user_id": 1,
        "session_id": str(uuid.uuid4())
    }
    
    try:
        remove_response = requests.post(f"{API_BASE}/api/agent/message", json=remove_input,
                                      headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
                                      timeout=15)
        
        if remove_response.status_code == 200:
            remove_result = remove_response.json()
            remove_output = remove_result.get("agent_output", {})
            print(f"   Remove result: {remove_output.get('status', 'unknown')}")
            
            if remove_output.get("needs_confirmation"):
                # Confirm the removal
                print("   Confirming removal...")
                confirm_input = {
                    "text": "yes, proceed",
                    "user_id": 1,
                    "session_id": remove_output.get("session_id"),
                    "confirmed": True
                }
                
                confirm_response = requests.post(f"{API_BASE}/api/agent/confirm", json=confirm_input,
                                               headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
                                               timeout=15)
                
                if confirm_response.status_code == 200:
                    print("   ✅ Vehicle removal confirmed")
                else:
                    print(f"   ❌ Confirmation failed: {confirm_response.status_code}")
        
        # Step 2: Now test vehicle assignment with the fix
        print("\nStep 2: Testing vehicle assignment with int conversion...")
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
            
            print(f"📝 Vehicle Assignment Result:")
            print(f"   Status: {assign_output.get('status')}")
            print(f"   Error: {assign_output.get('error')}")
            print(f"   Message: {assign_output.get('message', '')}")
            
            # Check for the specific asyncpg error
            message = assign_output.get('message', '').lower()
            error_msg = assign_output.get('error', '')
            
            if "str' object cannot be interpreted as an integer" in message:
                print("❌ STRING TO INT CONVERSION NOT FIXED - asyncpg error still present")
                return False
            elif assign_output.get('status') == 'executed' or assign_output.get('status') == 'completed':
                print("✅ STRING TO INT CONVERSION FIXED - Vehicle assignment successful!")
                if "TN01XY9999" in assign_output.get('message', ''):
                    print("✅ BONUS: Vehicle name properly displayed!")
                return True
            else:
                print(f"ℹ️ Assignment blocked for other reason: {error_msg}")
                # Check if it's not the int conversion error
                if "already has" in message or "already deployed" in error_msg:
                    print("✅ STRING TO INT CONVERSION LIKELY FIXED (blocked by business logic, not asyncpg)")
                    return True
                else:
                    print("❌ Unknown error - may still be int conversion issue")
                    return False
        else:
            print(f"❌ Vehicle assignment request failed: {assign_response.status_code}")
            print(f"Response: {assign_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 String to Int Conversion Fix Test")
    print("=" * 60)
    
    success = test_int_conversion_fix()
    
    print("\n" + "=" * 60)
    print(f"🎯 Final Result: {'✅ FIX WORKING' if success else '❌ STILL BROKEN'}")
    
    if success:
        print("🎉 Structured command parameters now properly converted to integers!")
        print("   - No more asyncpg 'str cannot be interpreted as int' errors")
        print("   - Vehicle and driver assignment should work end-to-end")
    else:
        print("⚠️ String to int conversion may still need work")
        print("   - Check logs for asyncpg errors")
        print("   - Verify parameter conversion in parse_intent_llm.py")
