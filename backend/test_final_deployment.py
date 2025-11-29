#!/usr/bin/env python3
"""
Test deployment check end-to-end
"""

import requests
import json
import uuid
import time

print("🎉 FINAL DEPLOYMENT CHECK TEST")
print("="*50)

# Test deployment check with trip 5 (has deployment_id: 24)
input_data = {
    'text': 'STRUCTURED_CMD:assign_vehicle|trip_id:5|vehicle_id:8|vehicle_name:Honda|context:selection_ui',
    'user_id': 1,
    'session_id': str(uuid.uuid4())
}

print(f"📡 Testing with trip 5 (known to have deployment_id: 24)")
print(f"Input: {input_data['text']}")

try:
    # Make sure to use a reasonable timeout
    response = requests.post('http://localhost:8000/api/agent/message', 
                            json=input_data,
                            headers={'x-api-key': 'dev-key-change-in-production', 'Content-Type': 'application/json'},
                            timeout=10)

    print(f"\n📋 Response Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        agent_output = result['agent_output']
        
        print(f"\n🎯 RESULT:")
        print(f"   Action: {agent_output.get('action')}")
        print(f"   Status: {agent_output.get('status')}")
        print(f"   Error: {agent_output.get('error')}")
        print(f"   Message: {agent_output.get('message', '')}")
        
        # Check if deployment check worked
        if (agent_output.get('status') == 'failed' and 
            agent_output.get('error') == 'already_deployed' and
            'deployment' in agent_output.get('message', '').lower()):
            
            print(f"\n🎉 SUCCESS: DEPLOYMENT CHECK WORKING!")
            print(f"   ✅ Status: failed (correct)")
            print(f"   ✅ Error: already_deployed (correct)")
            print(f"   ✅ Caught at decision_router level (not execution)")
            print(f"   ✅ Clear message about deployment conflict")
            print(f"\n🏆 STRUCTURED COMMANDS NOW PROPERLY BLOCKED!")
            
        elif agent_output.get('error') == 'execution_failed':
            print(f"\n❌ FAILURE: Still going to execution")
            print(f"   Backend not using updated decision_router")
            
        else:
            print(f"\n❓ UNEXPECTED RESULT:")
            print(f"   Status: {agent_output.get('status')}")
            print(f"   Error: {agent_output.get('error')}")
    else:
        print(f'❌ HTTP Error {response.status_code}: {response.text}')
        
except requests.exceptions.ConnectinError:
    print("❌ Backend not running - start it first")
except Exception as e:
    print(f'❌ Exception: {e}')

print(f"\n" + "="*50)
print("🚀 DEPLOYMENT CHECK STATUS")
print("="*50)
