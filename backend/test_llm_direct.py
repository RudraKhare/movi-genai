"""Direct test of LLM parsing"""
import asyncio
import sys
import os
sys.path.insert(0, 'C:/Users/rudra/Desktop/movi/backend')

# Set env vars
os.environ['USE_LLM_PARSE'] = 'true'
os.environ['LLM_PROVIDER'] = 'gemini'
os.environ['GEMINI_API_KEY'] = 'AIzaSyC_iK4zBPNnseMMkEnobIYu9rWgjyoD3jQ'
os.environ['LLM_MODEL'] = 'gemini-2.5-flash'

async def test():
    try:
        from langgraph.tools.llm_client import parse_intent_with_llm
        
        print("Testing LLM parsing directly...")
        result = await parse_intent_with_llm("cancel the Bulk - 00:01 trip")
        
        print(f"\n✅ LLM Response:")
        import json
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(test())
