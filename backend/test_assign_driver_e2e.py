#!/usr/bin/env python3
"""
End-to-end test for the assign_driver fix
Tests the actual LangGraph flow with driver assignment
"""

import asyncio
import requests
import json
import uuid
from datetime import datetime

# Configuration
API_BASE = "http://localhost:5007"
API_KEY = "your-api-key"

async def test_assign_driver_end_to_end():
    """Test the complete assign_driver flow"""
    print("🚀 Testing assign_driver end-to-end...")
    print("=" * 60)
    
    # Test scenarios for assign_driver
    test_cases = [
        {
            "name": "Structured Command Driver Assignment",
            "input": {
                "text": "STRUCTURED_CMD:assign_driver|trip_id:1|driver_id:2|driver_name:John Doe|context:selection_ui",
                "user_id": 1,
                "session_id": str(uuid.uuid4())
            },
            "description": "Direct structured command from frontend UI"
        },
        {
            "name": "Natural Language Driver Assignment",
            "input": {
                "text": "assign driver 2 to trip 1", 
                "user_id": 1,
                "session_id": str(uuid.uuid4())
            },
            "description": "Natural language with specific IDs"
        },
        {
            "name": "Context-Aware Driver Assignment",
            "input": {
                "text": "assign driver",
                "user_id": 1,
                "selectedTripId": 1,
                "session_id": str(uuid.uuid4())
            },
            "description": "Vague command with UI context"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['name']}")
        print(f"📝 {test_case['description']}")
        print(f"📤 Input: {test_case['input']['text']}")
        
        try:
            response = requests.post(
                f"{API_BASE}/agent",
                json=test_case["input"],
                headers={
                    "x-api-key": API_KEY,
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                agent_output = result.get("agent_output", {})
                
                action = agent_output.get("action", "unknown")
                status = agent_output.get("status", "unknown")
                message = agent_output.get("message", "No message")
                
                print(f"📥 Response:")
                print(f"   Action: {action}")
                print(f"   Status: {status}")
                print(f"   Message: {message}")
                
                if action == "assign_driver" and status != "error":
                    print("✅ Test PASSED - Driver assignment successful")
                else:
                    print("❌ Test FAILED - Assignment did not complete")
                    print(f"   Full response: {json.dumps(agent_output, indent=2)}")
                    
            else:
                print(f"❌ Test FAILED - HTTP {response.status_code}")
                print(f"   Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Test FAILED - Request error: {str(e)}")
        except Exception as e:
            print(f"❌ Test FAILED - Unexpected error: {str(e)}")
    
    print(f"\n{'=' * 60}")
    print("🏁 End-to-end testing complete")

if __name__ == "__main__":
    asyncio.run(test_assign_driver_end_to_end())
