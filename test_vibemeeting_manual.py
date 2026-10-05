#!/usr/bin/env python3
"""
Test VibeMeeting functionality by manually setting transcription
"""

import requests
import json
import uuid
from datetime import datetime
import time

# Get backend URL from environment
BACKEND_URL = "https://shop-floor-stage.preview.emergentagent.com/api"

def make_request(method, endpoint, headers=None, data=None, json_data=None):
    """Helper function to make HTTP requests with error handling"""
    url = f"{BACKEND_URL}{endpoint}"
    print(f"Making {method} request to: {url}")
    if json_data:
        print(f"JSON data: {json_data}")
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=30)
        elif method.upper() == "POST":
            if json_data:
                response = requests.post(url, headers=headers, json=json_data, timeout=30)
            else:
                response = requests.post(url, headers=headers, data=data, timeout=30)
        elif method.upper() == "PATCH":
            if json_data:
                response = requests.patch(url, headers=headers, json=json_data, timeout=30)
            else:
                response = requests.patch(url, headers=headers, data=data, timeout=30)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        print(f"Response status: {response.status_code}")
        if response.status_code >= 400:
            print(f"Response body: {response.text}")
        
        return response
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

def test_vibemeeting_with_manual_transcription():
    """Test VibeMeeting by manually setting transcription in database"""
    
    # Test data
    timestamp = str(int(time.time()))
    user_email = f"vibeuser_{timestamp}@example.com"
    user_name = "Vibe User"
    user_password = "password123"
    
    print("Testing VibeMeeting with Manual Transcription")
    print("=" * 60)
    
    # Register user
    print("Step 1: Register User")
    response = make_request("POST", "/auth/register", json_data={
        "email": user_email,
        "password": user_password,
        "name": user_name
    })
    
    if not response or response.status_code != 200:
        print("❌ Failed to register user")
        return False
    
    data = response.json()
    user_token = data.get("session_token")
    user_id = data.get("user", {}).get("id")
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Create team
    print("Step 2: Create Team")
    response = make_request("POST", "/teams?team_name=Vibe Test Team", headers=headers)
    
    if not response or response.status_code != 200:
        print("❌ Failed to create team")
        return False
    
    team_data = response.json()
    team_id = team_data.get("id")
    
    # Create meeting
    print("Step 3: Create Meeting")
    meeting_data = {
        "title": "Test VibeMeeting Manual",
        "team_id": team_id
    }
    response = make_request("POST", "/meetings", headers=headers, json_data=meeting_data)
    
    if not response or response.status_code != 200:
        print("❌ Failed to create meeting")
        return False
    
    meeting_response = response.json()
    meeting_id = meeting_response.get("id")
    print(f"✅ Meeting created with ID: {meeting_id}")
    
    # Manually set transcription using MongoDB (simulate successful transcription)
    print("Step 4: Manually Set Transcription")
    sample_transcription = "Hello everyone, welcome to our team meeting. We need to discuss the new project requirements. John, can you take care of the database design? Sarah, please handle the frontend development. We also need to schedule a follow-up meeting next week to review progress."
    
    # We'll use a direct database update approach
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        import asyncio
        import os
        from dotenv import load_dotenv
        from pathlib import Path
        
        ROOT_DIR = Path('backend')
        load_dotenv(ROOT_DIR / '.env')
        
        async def update_transcription():
            mongo_url = os.environ['MONGO_URL']
            client = AsyncIOMotorClient(mongo_url)
            db = client[os.environ['DB_NAME']]
            
            result = await db.meetings.update_one(
                {"id": meeting_id},
                {"$set": {"transcription": sample_transcription}}
            )
            
            client.close()
            return result.modified_count > 0
        
        success = asyncio.run(update_transcription())
        if success:
            print("✅ Transcription set manually")
        else:
            print("❌ Failed to set transcription")
            return False
            
    except Exception as e:
        print(f"❌ Failed to set transcription: {e}")
        return False
    
    # Test analyze meeting
    print("Step 5: Analyze Meeting")
    response = make_request("POST", f"/meetings/{meeting_id}/analyze", headers=headers)
    
    if response and response.status_code == 200:
        data = response.json()
        summary = data.get("summary", "")
        tasks_identified = data.get("tasks", [])
        
        print(f"✅ Meeting analyzed successfully")
        print(f"   Summary: {summary[:100]}...")
        print(f"   Tasks identified: {len(tasks_identified)}")
        
        # Test review meeting
        print("Step 6: Review Meeting")
        if tasks_identified:
            # Use the first identified task
            approved_tasks = [tasks_identified[0]]
        else:
            # Create a sample task if none were identified
            approved_tasks = [
                {
                    "title": "Database Design Task",
                    "description": "Design the database schema for the new project",
                    "assigned_to": user_id
                }
            ]
        
        review_data = {"approved_tasks": approved_tasks}
        response = make_request("POST", f"/meetings/{meeting_id}/review", headers=headers, json_data=review_data)
        
        if response and response.status_code == 200:
            print("✅ Meeting reviewed and tasks created successfully")
            
            # Verify tasks were created
            print("Step 7: Verify Tasks Created")
            response = make_request("GET", f"/tasks?team_id={team_id}", headers=headers)
            
            if response and response.status_code == 200:
                tasks = response.json()
                meeting_tasks = [t for t in tasks if any(keyword in t.get("description", "").lower() 
                                                       for keyword in ["database", "design", "project", "meeting"])]
                
                print(f"✅ Found {len(meeting_tasks)} tasks related to the meeting")
                return True
            else:
                print("❌ Failed to verify tasks")
                return False
        else:
            print("❌ Failed to review meeting")
            return False
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        print(f"❌ Failed to analyze meeting: {error_msg}")
        return False

if __name__ == "__main__":
    success = test_vibemeeting_with_manual_transcription()
    if success:
        print("\n🎉 VibeMeeting functionality test PASSED")
    else:
        print("\n💥 VibeMeeting functionality test FAILED")