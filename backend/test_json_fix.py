#!/usr/bin/env python3
import json
import re

def fix_truncated_json(content: str) -> str:
    """Attempt to fix common JSON truncation issues"""
    content = content.strip()
    
    # Remove any trailing commas before attempting to close
    content = re.sub(r',\s*$', '', content)
    
    # Count open braces and brackets to determine what's missing
    open_braces = content.count('{') - content.count('}')
    open_brackets = content.count('[') - content.count(']')
    
    # Add missing closing characters
    for _ in range(open_brackets):
        content += ']'
    for _ in range(open_braces):
        content += '}'
        
    return content

# Test with the exact content from the error log
test_content = """{   
 "action": "assign_vehicle",
 "target_label": null,
 "target_time": null,
 "target_trip_id": null,
 "target_path_id": null,
 "target_route_id": null,
 "parameters": {
  "vehicle_id": null,
  "driver_id": null,
  "vehicle_registration": null,
  "driver_name": null,
  "stop_ids": null,"""

print("Testing JSON fixing...")
print(f"Original content:\n{test_content}")
print(f"Length: {len(test_content)}")

try:
    # Try original parsing
    parsed = json.loads(test_content)
    print("Original JSON parsing successful!")
except json.JSONDecodeError as e:
    print(f"Original JSON parsing failed: {e}")
    
    # Try fixing
    try:
        fixed_content = fix_truncated_json(test_content)
        print(f"\nFixed content:\n{fixed_content}")
        
        parsed = json.loads(fixed_content)
        print("Fixed JSON parsing successful!")
        print(f"Parsed action: {parsed.get('action')}")
        print(f"Full parsed: {parsed}")
        
    except json.JSONDecodeError as fix_error:
        print(f"Fixed JSON parsing still failed: {fix_error}")
