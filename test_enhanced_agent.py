#!/usr/bin/env python3
"""
Test Script for Enhanced MOVI Agent
Tests natural language understanding and driver assignment functionality
"""

import asyncio
import sys
import os
import json

# Add the backend directory to Python path
sys.path.append('/Users/rudra/Desktop/movi/backend')

from langgraph.runtime import runtime


async def test_natural_language_parsing():
    """Test natural language understanding capabilities"""
    
    test_cases = [
        # Natural language vehicle assignment
        {
            "input": "allocate a bus to the downtown route at 2pm",
            "expected_action": "assign_vehicle",
            "description": "Natural language vehicle allocation"
        },
        
        # Natural language driver assignment  
        {
            "input": "appoint John as driver for Bulk - 00:01",
            "expected_action": "assign_driver", 
            "description": "Natural language driver appointment"
        },
        
        # Colloquial expressions
        {
            "input": "put a driver on this trip", 
            "expected_action": "assign_driver",
            "description": "Colloquial driver assignment"
        },
        
        # Synonyms
        {
            "input": "give this trip a vehicle",
            "expected_action": "assign_vehicle", 
            "description": "Synonym-based vehicle assignment"
        },
        
        # Missing parameters - should ask for clarification
        {
            "input": "assign a driver",
            "expected_clarification": True,
            "description": "Missing trip identifier should trigger clarification"
        },
        
        # Vague instructions
        {
            "input": "please connect a driver to my trip",
            "expected_action": "assign_driver",
            "description": "Vague but understandable driver assignment"
        }
    ]
    
    print("🧪 Testing Natural Language Understanding...")
    print("=" * 60)
    
    success_count = 0
    
    for i, test in enumerate(test_cases):
        print(f"\n{i+1}. {test['description']}")
        print(f"   Input: '{test['input']}'")
        
        try:
            # Create input state
            state = {
                "text": test["input"],
                "user_id": 1,
                "currentPage": "busDashboard"
            }
            
            # Run the agent
            result = await runtime.run(state)
            
            # Check results
            action = result.get("action")
            needs_clarification = result.get("needs_clarification", False)
            
            if "expected_action" in test:
                if action == test["expected_action"]:
                    print(f"   ✅ Parsed action correctly: {action}")
                    success_count += 1
                else:
                    print(f"   ❌ Expected: {test['expected_action']}, Got: {action}")
            
            elif "expected_clarification" in test:
                if needs_clarification:
                    print(f"   ✅ Correctly identified missing information")
                    print(f"   💬 Clarification: {result.get('message', 'No message')}")
                    success_count += 1
                else:
                    print(f"   ❌ Expected clarification request, but didn't get one")
            
            # Show confidence and explanation
            confidence = result.get("confidence", 0)
            explanation = result.get("llm_explanation", "")
            print(f"   📊 Confidence: {confidence:.2f}")
            if explanation:
                print(f"   💭 LLM Reasoning: {explanation}")
                
        except Exception as e:
            print(f"   💥 Error: {str(e)}")
    
    print(f"\n🎯 Results: {success_count}/{len(test_cases)} tests passed")
    return success_count == len(test_cases)


async def test_driver_assignment_flow():
    """Test complete driver assignment workflow"""
    
    print("\n\n🚗 Testing Driver Assignment Flow...")
    print("=" * 60)
    
    # Test case: Assign specific driver to specific trip
    test_input = {
        "text": "assign driver John Smith to Bulk - 00:01",
        "user_id": 1,
        "currentPage": "busDashboard"
    }
    
    print(f"Input: '{test_input['text']}'")
    
    try:
        result = await runtime.run(test_input)
        
        print(f"Action: {result.get('action')}")
        print(f"Target: {result.get('target_label')}")
        print(f"Driver: {result.get('parsed_params', {}).get('driver_name')}")
        print(f"Status: {result.get('status')}")
        print(f"Message: {result.get('message')}")
        
        # Check if flow reached execution or properly asked for confirmation
        if result.get("status") in ["completed", "awaiting_confirmation"]:
            print("✅ Driver assignment flow working correctly")
            return True
        else:
            print("❌ Driver assignment flow incomplete")
            return False
            
    except Exception as e:
        print(f"💥 Error in driver assignment: {str(e)}")
        return False


async def main():
    """Run all tests"""
    print("🤖 MOVI Agent Enhanced Testing Suite")
    print("Testing natural language understanding and driver assignment")
    print()
    
    # Test 1: Natural language parsing
    nl_success = await test_natural_language_parsing()
    
    # Test 2: Driver assignment workflow
    driver_success = await test_driver_assignment_flow()
    
    # Final results
    print("\n" + "=" * 60)
    print("🏁 FINAL RESULTS")
    print("=" * 60)
    print(f"Natural Language Tests: {'✅ PASS' if nl_success else '❌ FAIL'}")
    print(f"Driver Assignment Test: {'✅ PASS' if driver_success else '❌ FAIL'}")
    
    if nl_success and driver_success:
        print("\n🎉 All tests passed! MOVI agent is working correctly.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    # Set environment variable for testing
    os.environ["USE_LLM_PARSE"] = "true"
    
    # Run tests
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
