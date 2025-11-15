"""
List available Gemini models
"""
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure the client with your API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ GEMINI_API_KEY not found in .env file")
    exit(1)

genai.configure(api_key=api_key)

print("🔍 Available Gemini models that support generateContent:\n")

for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"✅ {m.name}")
        print(f"   Display Name: {m.display_name}")
        print(f"   Description: {m.description}")
        print()
