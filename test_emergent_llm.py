#!/usr/bin/env python3
"""
Test Emergent LLM API directly
"""

import asyncio
import os
from dotenv import load_dotenv
from pathlib import Path
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path('backend')
load_dotenv(ROOT_DIR / '.env')

async def test_emergent_llm():
    api_key = os.getenv('EMERGENT_LLM_KEY')
    print(f"Using API key: {api_key[:10]}...")
    
    try:
        chat = LlmChat(
            api_key=api_key,
            session_id="test-session",
            system_message="You are a helpful assistant. Respond with a simple greeting."
        ).with_model("openai", "gpt-5")
        
        message = UserMessage(text="Hello, can you hear me?")
        response = await chat.send_message(message)
        
        print(f"Response: {response}")
        return response
        
    except Exception as e:
        print(f"Exception occurred: {e}")
        return None

if __name__ == "__main__":
    result = asyncio.run(test_emergent_llm())
    print(f"Final result: {result}")