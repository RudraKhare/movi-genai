import sys
sys.path.insert(0, 'C:/Users/rudra/Desktop/movi/backend')

from dotenv import load_dotenv
load_dotenv()

try:
    from langgraph.nodes.parse_intent_llm import parse_intent_llm
    print('✅ parse_intent_llm import successful')
    print(f'   Function: {parse_intent_llm}')
except Exception as e:
    print(f'❌ parse_intent_llm import failed: {e}')
    import traceback
    traceback.print_exc()
