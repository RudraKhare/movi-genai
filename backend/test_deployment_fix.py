#!/usr/bin/env python3
"""
Test the deployment check fix for structured commands
"""

import requests
import json
import uuid

# Test the deployment check with trip 5 (which already has deployment)
input_data = {
    'text': 'STRUCTURED_CMD:assign_vehicle|trip_id:5|vehicle_id:8|vehicle_name:Honda|context:selection_ui',
    'user_id': 1,
    'session_id': str(uuid.uuid4())
}

response = requests.post('http://localhost:8000/api/agent/message', 
                        json=input_data,
                        headers={'x-api-key': 'dev-key-change-in-production', 'Content-Type': 'application/json'},
                        timeout=15)

print('Status:', response.status_code)
if response.status_code == 200:
    result = response.json()
    agent_output = result['agent_output']
    print(f"Action: {agent_output.get('action')}")
    print(f"Status: {agent_output.get('status')}")
    print(f"Message: {agent_output.get('message', '')}")
    print(f"Error: {agent_output.get('error', '')}")
    print()
    
    if agent_output.get('status') == 'failed' and agent_output.get('error') == 'already_deployed':
        print("✅ DEPLOYMENT CHECK WORKING!")
        print("   Structured commands now properly blocked when trip has deployment")
    else:
        print("❌ Deployment check still not working for structured commands")
else:
    print('Error:', response.text)
