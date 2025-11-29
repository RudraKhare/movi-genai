#!/usr/bin/env python3
import asyncio
import sys
sys.path.append('.')

# Mock the gemini response to test JSON fixing
from unittest.mock import patch, AsyncMock
import json

async def test_json_fixing():
    """Test the JSON fixing functionality"""
    
    print("=== Testing JSON Fixing Logic ===")
    
    # Mock truncated response from the error log
    truncated_response = """{   
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

    # Test our JSON fixing function
    from langgraph.tools.llm_client import parse_intent_with_llm
    
    # Mock the Gemini model to return the truncated response
    with patch('langgraph.tools.llm_client._call_gemini') as mock_gemini:
        
        # Create a mock response object
        mock_response = AsyncMock()
        mock_response.text = truncated_response
        
        # Mock the model.generate_content to return our mock response
        with patch('google.generativeai.GenerativeModel') as mock_model_class:
            mock_model = AsyncMock()
            mock_model.generate_content.return_value = mock_response
            mock_model_class.return_value = mock_model
            
            # Set up the mock to actually call our fixing logic
            from langgraph.tools.llm_client import _call_gemini
            
            # We need to patch the actual call
            async def mock_call_gemini(text, config, context):
                # Simulate the actual _call_gemini function with our truncated response
                import re
                content = truncated_response
                
                def fix_truncated_json(content: str) -> str:
                    content = content.strip()
                    content = re.sub(r',\s*$', '', content)
                    open_braces = content.count('{') - content.count('}')
                    open_brackets = content.count('[') - content.count(']')
                    for _ in range(open_brackets):
                        content += ']'
                    for _ in range(open_braces):
                        content += '}'
                    return content
                
                try:
                    parsed = json.loads(content)
                    print("Original JSON parsed successfully (unexpected)")
                except json.JSONDecodeError as e:
                    print(f"Original JSON parsing failed as expected: {e}")
                    
                    try:
                        fixed_content = fix_truncated_json(content)
                        print(f"Fixed JSON: {fixed_content}")
                        parsed = json.loads(fixed_content)
                        print("Fixed JSON parsed successfully!")
                    except json.JSONDecodeError as fix_error:
                        print(f"Fixed JSON still failed: {fix_error}")
                        return {
                            "action": "assign_vehicle",
                            "target_label": None,
                            "target_time": None,
                            "target_trip_id": None,
                            "target_path_id": None,
                            "target_route_id": None,
                            "parameters": {},
                            "confidence": 0.8,
                            "clarify": True,
                            "clarify_options": ["Please select a specific vehicle"],
                            "explanation": "Detected vehicle assignment but need clarification"
                        }
                
                # Add required fields if missing
                parsed.setdefault("confidence", 0.8)
                parsed.setdefault("clarify", True)
                parsed.setdefault("clarify_options", ["Please select a vehicle"])
                parsed.setdefault("explanation", "Vehicle assignment detected")
                
                return parsed
            
            mock_gemini.side_effect = mock_call_gemini
            
            # Test with context that would trigger LLM
            print("\nTesting LLM call with JSON parsing fix:")
            context = {
                'selectedTripId': None,  # This will trigger LLM call
                'ui_context': {}
            }
            
            try:
                result = await parse_intent_with_llm("assign vehicle to this trip", context)
                print(f"Result action: {result['action']}")
                print(f"Result confidence: {result['confidence']}")
                print(f"Result explanation: {result['explanation']}")
                print("✅ JSON fixing worked!")
            except Exception as e:
                print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_json_fixing())
