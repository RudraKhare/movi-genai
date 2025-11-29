#!/usr/bin/env python3
"""
Simple test to trigger deployment check logs
"""

import requests
import json
import uuid
import time

print("🔧 Testing Deployment Check Fix...")
print("Waiting for backend to be ready...")
time.sleep(2)

# Test the deployment check with trip 5 
input_data = {
    'text': 'STRUCTURED_CMD:assign_vehicle|trip_id:5|vehicle_id:8|vehicle_name:Honda|context:selection_ui',
    'user_id': 1,
    'session_id': str(uuid.uuid4())
}

print("\n📡 Sending request...")
print(f"Input: {input_data['text']}")

try:
    response = requests.post('http://localhost:8000/api/agent/message', 
                            json=input_data,
                            headers={'x-api-key': 'dev-key-change-in-production', 'Content-Type': 'application/json'},
                            timeout=15)

    print(f"\n📋 Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        agent_output = result['agent_output']
        print(f"\n🎯 RESPONSE DETAILS:")
        print(f"   Action: {agent_output.get('action')}")
        print(f"   Status: {agent_output.get('status')}")
        print(f"   Message: {agent_output.get('message', '')}")
        print(f"   Error: {agent_output.get('error', '')}")
        print(f"   Success: {agent_output.get('success', False)}")
        
        print(f"\n🔍 DEBUGGING INFO:")
        print(f"   Trip ID: {agent_output.get('trip_id')}")
        print(f"   Trip Label: {agent_output.get('trip_label', '')}")
        
        # Check if our deployment check is working
        if agent_output.get('status') == 'failed' and agent_output.get('error') == 'already_deployed':
            print(f"\n✅ DEPLOYMENT CHECK WORKING!")
            print("   ✓ Status: failed")
            print("   ✓ Error: already_deployed") 
            print("   ✓ Structured commands properly blocked when trip has deployment")
        elif agent_output.get('error') == 'execution_failed':
            print(f"\n⚠️ DEPLOYMENT CHECK BYPASSED!")
            print("   ❌ Going to execution phase (should be blocked earlier)")
            print("   ❌ decision_router not catching the deployment conflict")
        else:
            print(f"\n❓ UNEXPECTED RESULT")
            print(f"   Status: {agent_output.get('status')}")
            print(f"   Error: {agent_output.get('error')}")
    else:
        print(f'❌ HTTP Error: {response.text}')
        
except Exception as e:
    print(f'❌ Exception: {e}')

print(f"\n" + "="*50)
print("Check the backend logs for decision_router debug info...")
print("Look for: 'Route G: Processing assign_vehicle'")
print("="*50)
