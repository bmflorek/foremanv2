#!/usr/bin/env python3
"""
Test transcription API directly
"""

import httpx
import asyncio
import os
import base64
import io
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path('backend')
load_dotenv(ROOT_DIR / '.env')

async def test_transcription():
    api_key = os.getenv('EMERGENT_LLM_KEY')
    print(f"Using API key: {api_key[:10]}...")
    
    # Create a minimal audio file (silence)
    sample_audio_base64 = "SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4Ljc2LjEwMAAAAAAAAAAAAAAA//tQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAWGluZwAAAA8AAAAEAAABIADAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDV1dXV1dXV1dXV1dXV1dXV1dXV1dXV1dXV6urq6urq6urq6urq6urq6urq6urq6urq6v////////////////////////////////8AAAAATGF2YzU4LjEzAAAAAAAAAAAAAAAAJAAAAAAAAAAAASDs90hvAAAAAAAAAAAAAAAAAAAA//tQxAAAAAAAAAAAAAAAAAAAAAAASW5mbwAAAA8AAAAEAAABIADAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDV1dXV1dXV1dXV1dXV1dXV1dXV1dXV1dXV6urq6urq6urq6urq6urq6urq6urq6urq6v////////////////////////////////8AAAAATGF2YzU4LjEzAAAAAAAAAAAAAAAAJAAAAAAAAAAAASDs90hvAAAAAAAAAAAAAAAAAAAA"
    
    try:
        audio_bytes = base64.b64decode(sample_audio_base64)
        print(f"Audio bytes length: {len(audio_bytes)}")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            files = {'file': ('audio.mp3', io.BytesIO(audio_bytes), 'audio/mpeg')}
            data = {'model': 'whisper-1'}
            headers = {'Authorization': f'Bearer {api_key}'}
            
            print("Making request to OpenAI Whisper API...")
            response = await client.post(
                'https://api.openai.com/v1/audio/transcriptions',
                files=files,
                data=data,
                headers=headers
            )
            
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            print(f"Response text: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Transcription successful: {result}")
                return result.get('text', '')
            else:
                print(f"Transcription failed with status {response.status_code}")
                return None
                
    except Exception as e:
        print(f"Exception occurred: {e}")
        return None

if __name__ == "__main__":
    result = asyncio.run(test_transcription())
    print(f"Final result: {result}")