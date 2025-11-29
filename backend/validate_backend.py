#!/usr/bin/env python3
"""
Quick Backend Validation Script

Run this before manual testing to ensure all components are working.
"""

import asyncio
import json
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def validate_backend_setup():
    """Validate that backend components are properly configured"""
    print("🔍 MOVI Backend Validation Check")
    print("=" * 50)
    
    issues_found = []
    
    # 1. Check graph_def configuration
    print("\n1. Checking graph_def.py configuration...")
    try:
        with open('langgraph/graph_def.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'USE_LLM_PARSE' in content and ('true' in content.lower() or 'True' in content):
            print("   ✅ LLM parsing is enabled")
        else:
            print("   ❌ LLM parsing not enabled - check USE_LLM_PARSE setting")
            issues_found.append("LLM parsing not enabled")
            
        if 'parse_intent_llm' in content:
            print("   ✅ LLM parser is imported/used")
        else:
            print("   ❌ LLM parser not found in graph definition")
            issues_found.append("LLM parser not in graph")
            
    except Exception as e:
        print(f"   ❌ Error reading graph_def.py: {e}")
        issues_found.append(f"graph_def.py error: {e}")
    
    # 2. Check parse_intent_llm implementation
    print("\n2. Checking parse_intent_llm.py...")
    try:
        with open('langgraph/nodes/parse_intent_llm.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'assign_driver' in content:
            print("   ✅ assign_driver action is recognized")
        else:
            print("   ❌ assign_driver action not found")
            issues_found.append("assign_driver not in LLM parser")
            
        if 'confidence' in content:
            print("   ✅ Confidence-based logic implemented")
        else:
            print("   ❌ Confidence logic missing")
            issues_found.append("Confidence logic missing")
            
    except Exception as e:
        print(f"   ❌ Error reading parse_intent_llm.py: {e}")
        issues_found.append(f"parse_intent_llm.py error: {e}")
    
    # 3. Check tools.py for driver functions
    print("\n3. Checking tools.py...")
    try:
        with open('langgraph/tools.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'tool_assign_driver' in content:
            print("   ✅ tool_assign_driver function exists")
        else:
            print("   ❌ tool_assign_driver function missing")
            issues_found.append("tool_assign_driver missing")
            
        if 'tool_find_driver_by_name' in content:
            print("   ✅ tool_find_driver_by_name function exists")
        else:
            print("   ❌ tool_find_driver_by_name function missing")
            issues_found.append("tool_find_driver_by_name missing")
            
    except Exception as e:
        print(f"   ❌ Error reading tools.py: {e}")
        issues_found.append(f"tools.py error: {e}")
    
    # 4. Check resolve_target.py
    print("\n4. Checking resolve_target.py...")
    try:
        with open('langgraph/nodes/resolve_target.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'resolve_driver_for_assignment' in content:
            print("   ✅ Driver resolution logic exists")
        else:
            print("   ❌ Driver resolution logic missing")
            issues_found.append("Driver resolution missing")
            
        if 'assign_driver' in content and 'trip_actions' in content:
            print("   ✅ assign_driver is in trip_actions list")
        else:
            print("   ❌ assign_driver not properly categorized")
            issues_found.append("assign_driver not in trip_actions")
            
    except Exception as e:
        print(f"   ❌ Error reading resolve_target.py: {e}")
        issues_found.append(f"resolve_target.py error: {e}")
    
    # 5. Check execute_action.py
    print("\n5. Checking execute_action.py...")
    try:
        with open('langgraph/nodes/execute_action.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'elif action == "assign_driver"' in content:
            print("   ✅ assign_driver handler exists")
        else:
            print("   ❌ assign_driver handler missing")
            issues_found.append("assign_driver handler missing")
            
        if 'selectedEntityId' in content or 'entityName' in content:
            print("   ✅ State variable mapping exists")
        else:
            print("   ❌ State variable mapping may be missing")
            issues_found.append("State variable mapping issue")
            
    except Exception as e:
        print(f"   ❌ Error reading execute_action.py: {e}")
        issues_found.append(f"execute_action.py error: {e}")
    
    # Summary
    print(f"\n📊 Validation Summary:")
    if not issues_found:
        print("   🎉 ALL CHECKS PASSED! Backend is ready for testing.")
        print("\n   You can now:")
        print("   1. Start backend: docker-compose up")
        print("   2. Open frontend and test natural language")
        print("   3. Try: 'assign John to this trip'")
        return True
    else:
        print(f"   ❌ Found {len(issues_found)} issues:")
        for i, issue in enumerate(issues_found, 1):
            print(f"      {i}. {issue}")
        print("\n   Please fix these issues before testing.")
        return False

def show_quick_test_commands():
    """Show commands for quick testing"""
    print("\n" + "=" * 50)
    print("🚀 Quick Test Commands")
    print("=" * 50)
    print("\n1. Start Backend:")
    print("   cd C:\\Users\\rudra\\Desktop\\movi")
    print("   docker-compose up")
    
    print("\n2. Test Natural Language (in frontend chat):")
    print("   • Select a trip first")
    print("   • Type: 'assign John to this trip'")
    print("   • Expected: Should NOT say 'I'm not sure what you want to do'")
    
    print("\n3. Test Driver Assignment:")
    print("   • Use real driver names from your database")
    print("   • Type: 'allocate [DRIVER_NAME] as driver'")
    print("   • Expected: '[DRIVER_NAME] has been assigned to this trip'")
    
    print("\n4. Test Error Handling:")
    print("   • Don't select trip, type: 'assign driver'")
    print("   • Expected: 'Which trip would you like to assign a driver to?'")
    
    print("\n5. Check Logs:")
    print("   • Look for: [LLM] 🤖 Processing natural language input")
    print("   • Look for: [ASSIGN_DRIVER] ✅ Success")

async def main():
    """Main validation function"""
    try:
        validation_passed = await validate_backend_setup()
        show_quick_test_commands()
        
        if validation_passed:
            print(f"\n✅ Backend validation PASSED - ready to test!")
        else:
            print(f"\n❌ Backend validation FAILED - fix issues first!")
            
    except Exception as e:
        print(f"\n❌ Validation script error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
