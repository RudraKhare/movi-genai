"""Quick test to verify OpenAI API key works"""
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def test_openai_api():
    try:
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        print("🔄 Testing OpenAI API connection...")
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'API connection successful' in exactly 3 words."}
            ],
            max_tokens=10
        )
        
        result = response.choices[0].message.content
        print(f"✅ OpenAI API Response: {result}")
        print(f"✅ Model: {response.model}")
        print(f"✅ Tokens used: {response.usage.total_tokens}")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI API Error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_openai_api())
    if success:
        print("\n✅ OpenAI API key is valid and working!")
    else:
        print("\n❌ OpenAI API key test failed!")
