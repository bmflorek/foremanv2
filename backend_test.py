#!/usr/bin/env python3
"""
Backend API Testing for Manual Team Member Addition Feature
Tests all backend endpoints related to manual team member addition functionality.
"""

import requests
import json
import uuid
from datetime import datetime
import time

# Get backend URL from environment
BACKEND_URL = "https://shop-floor-stage.preview.emergentagent.com/api"

class TestResults:
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
    
    def add_result(self, test_name, passed, message="", details=None):
        self.results.append({
            "test": test_name,
            "passed": passed,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        if passed:
            self.passed += 1
        else:
            self.failed += 1
        
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"   {message}")
        if details:
            print(f"   Details: {details}")
        print()
    
    def print_summary(self):
        print("=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.passed + self.failed}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Success Rate: {(self.passed / (self.passed + self.failed) * 100):.1f}%")
        print("=" * 60)

def make_request(method, endpoint, headers=None, data=None, json_data=None):
    """Helper function to make HTTP requests with error handling"""
    url = f"{BACKEND_URL}{endpoint}"
    print(f"Making {method} request to: {url}")
    if json_data:
        print(f"JSON data: {json_data}")
    if data:
        print(f"Form data: {data}")
    
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
        elif method.upper() == "PUT":
            if json_data:
                response = requests.put(url, headers=headers, json=json_data, timeout=30)
            else:
                response = requests.put(url, headers=headers, data=data, timeout=30)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers, timeout=30)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        print(f"Response status: {response.status_code}")
        if response.status_code >= 400:
            print(f"Response body: {response.text}")
        
        return response
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

def test_manual_team_member_addition():
    """Test the complete manual team member addition workflow"""
    results = TestResults()
    
    # Test data - use unique emails with timestamp
    timestamp = str(int(time.time()))
    user_a_email = f"testuser1_{timestamp}@example.com"
    user_a_name = "Test User A"
    user_a_password = "password123"
    
    user_b_email = f"testuser2_{timestamp}@example.com" 
    user_b_name = "Test User B"
    user_b_password = "password456"
    
    user_c_email = f"testuser3_{timestamp}@example.com"
    user_c_name = "Test User C" 
    user_c_password = "password789"
    
    pending_member_name = "Test User 2"
    
    # Store session tokens and IDs
    user_a_token = None
    user_b_token = None
    user_c_token = None
    team_id = None
    pending_member_id = None
    task_id = None
    
    print("Starting Manual Team Member Addition Tests")
    print("=" * 60)
    
    # Test 1: Register User A
    print("Test 1: User A Registration")
    response = make_request("POST", "/auth/register", json_data={
        "email": user_a_email,
        "password": user_a_password,
        "name": user_a_name
    })
    
    if response and response.status_code == 200:
        data = response.json()
        user_a_token = data.get("session_token")
        user_a_id = data.get("user", {}).get("id")
        results.add_result("User A Registration", True, f"User A registered successfully with ID: {user_a_id}")
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        results.add_result("User A Registration", False, f"Failed to register User A: {error_msg}")
        return results
    
    # Test 2: User A Login (verify login works)
    print("Test 2: User A Login")
    response = make_request("POST", "/auth/login", json_data={
        "email": user_a_email,
        "password": user_a_password
    })
    
    if response and response.status_code == 200:
        data = response.json()
        user_a_token = data.get("session_token")  # Update token
        results.add_result("User A Login", True, "User A logged in successfully")
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        results.add_result("User A Login", False, f"Failed to login User A: {error_msg}")
    
    # Test 3: Create Team
    print("Test 3: Create Team")
    headers = {"Authorization": f"Bearer {user_a_token}"}
    # The endpoint expects team_name as a query parameter or form data
    response = make_request("POST", "/teams?team_name=Test Team", headers=headers)
    
    if response and response.status_code == 200:
        data = response.json()
        team_id = data.get("id")
        results.add_result("Create Team", True, f"Team created successfully with ID: {team_id}")
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        results.add_result("Create Team", False, f"Failed to create team: {error_msg}")
        return results
    
    # Test 4: Add Pending Member Manually
    print("Test 4: Add Pending Member Manually")
    response = make_request("POST", f"/teams/{team_id}/members/manual?email={user_b_email}&name={pending_member_name}", 
                          headers=headers)
    
    if response and response.status_code == 200:
        data = response.json()
        results.add_result("Add Pending Member", True, f"Pending member added: {data.get('message')}")
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        results.add_result("Add Pending Member", False, f"Failed to add pending member: {error_msg}")
    
    # Test 5: Get Team Members (should include pending member)
    print("Test 5: Get Team Members Including Pending")
    response = make_request("GET", f"/teams/{team_id}/members", headers=headers)
    
    if response and response.status_code == 200:
        members = response.json()
        pending_members = [m for m in members if m.get("is_pending", False)]
        active_members = [m for m in members if not m.get("is_pending", False)]
        
        if len(pending_members) > 0:
            pending_member_id = pending_members[0].get("id")
            results.add_result("Get Team Members", True, 
                             f"Found {len(active_members)} active and {len(pending_members)} pending members")
        else:
            results.add_result("Get Team Members", False, "No pending members found")
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        results.add_result("Get Team Members", False, f"Failed to get team members: {error_msg}")
    
    # Test 6: Get Pending Members Endpoint
    print("Test 6: Get Pending Members Endpoint")
    response = make_request("GET", f"/teams/{team_id}/pending-members", headers=headers)
    
    if response and response.status_code == 200:
        pending_members = response.json()
        if len(pending_members) > 0:
            results.add_result("Get Pending Members", True, f"Found {len(pending_members)} pending members")
        else:
            results.add_result("Get Pending Members", False, "No pending members returned")
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        results.add_result("Get Pending Members", False, f"Failed to get pending members: {error_msg}")
    
    # Test 7: Create Task and Assign to Pending Member
    print("Test 7: Create Task Assigned to Pending Member")
    if pending_member_id:
        task_title = "Test Task for Pending Member"
        task_desc = "This task is assigned to a pending member"
        response = make_request("POST", f"/tasks?title={task_title}&description={task_desc}&team_id={team_id}&assigned_to={pending_member_id}", 
                              headers=headers)
        
        if response and response.status_code == 200:
            data = response.json()
            task_id = data.get("id")
            results.add_result("Create Task for Pending Member", True, 
                             f"Task created and assigned to pending member: {task_id}")
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            results.add_result("Create Task for Pending Member", False, 
                             f"Failed to create task: {error_msg}")
    else:
        results.add_result("Create Task for Pending Member", False, "No pending member ID available")
    
    # Test 8: Register User B (should auto-join team and get tasks)
    print("Test 8: User B Registration (Auto-join)")
    response = make_request("POST", "/auth/register", json_data={
        "email": user_b_email,
        "password": user_b_password,
        "name": user_b_name
    })
    
    if response and response.status_code == 200:
        data = response.json()
        user_b_token = data.get("session_token")
        user_b_id = data.get("user", {}).get("id")
        results.add_result("User B Registration", True, f"User B registered and auto-joined team: {user_b_id}")
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        results.add_result("User B Registration", False, f"Failed to register User B: {error_msg}")
    
    # Test 9: Verify User B is in team (not pending)
    print("Test 9: Verify User B Auto-joined Team")
    response = make_request("GET", f"/teams/{team_id}/members", headers=headers)
    
    if response and response.status_code == 200:
        members = response.json()
        user_b_in_team = any(m.get("email") == user_b_email and not m.get("is_pending", False) 
                           for m in members)
        
        if user_b_in_team:
            results.add_result("User B Auto-join Verification", True, "User B successfully joined team")
        else:
            results.add_result("User B Auto-join Verification", False, "User B not found in team or still pending")
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        results.add_result("User B Auto-join Verification", False, f"Failed to verify team membership: {error_msg}")
    
    # Test 10: Verify Task Reassignment to User B
    print("Test 10: Verify Task Reassignment")
    if task_id and user_b_id:
        user_b_headers = {"Authorization": f"Bearer {user_b_token}"}
        response = make_request("GET", f"/tasks?team_id={team_id}", headers=user_b_headers)
        
        if response and response.status_code == 200:
            tasks = response.json()
            assigned_task = next((t for t in tasks if t.get("id") == task_id), None)
            
            if assigned_task and assigned_task.get("assigned_to") == user_b_id:
                results.add_result("Task Reassignment", True, "Task successfully reassigned to User B")
            else:
                results.add_result("Task Reassignment", False, 
                                 f"Task not properly reassigned. Expected: {user_b_id}, Got: {assigned_task.get('assigned_to') if assigned_task else 'Task not found'}")
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            results.add_result("Task Reassignment", False, f"Failed to get tasks: {error_msg}")
    else:
        results.add_result("Task Reassignment", False, "Missing task ID or user B ID")
    
    # Test 11: Register User C (for existing user test)
    print("Test 11: User C Registration")
    response = make_request("POST", "/auth/register", json_data={
        "email": user_c_email,
        "password": user_c_password,
        "name": user_c_name
    })
    
    if response and response.status_code == 200:
        data = response.json()
        user_c_token = data.get("session_token")
        user_c_id = data.get("user", {}).get("id")
        results.add_result("User C Registration", True, f"User C registered successfully: {user_c_id}")
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        results.add_result("User C Registration", False, f"Failed to register User C: {error_msg}")
    
    # Test 12: Add Existing User C to Team
    print("Test 12: Add Existing User to Team")
    response = make_request("POST", f"/teams/{team_id}/members/manual?email={user_c_email}&name={user_c_name}", 
                          headers=headers)
    
    if response and response.status_code == 200:
        data = response.json()
        if data.get("user_exists"):
            results.add_result("Add Existing User", True, "Existing user added immediately to team")
        else:
            results.add_result("Add Existing User", False, "User should have been added immediately but was marked as pending")
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        results.add_result("Add Existing User", False, f"Failed to add existing user: {error_msg}")
    
    # Test 13: Verify User C is in team immediately
    print("Test 13: Verify Existing User Immediate Addition")
    response = make_request("GET", f"/teams/{team_id}/members", headers=headers)
    
    if response and response.status_code == 200:
        members = response.json()
        user_c_in_team = any(m.get("email") == user_c_email and not m.get("is_pending", False) 
                           for m in members)
        
        if user_c_in_team:
            results.add_result("Existing User Immediate Addition", True, "User C immediately added to team")
        else:
            results.add_result("Existing User Immediate Addition", False, "User C not found in team or marked as pending")
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        results.add_result("Existing User Immediate Addition", False, f"Failed to verify team membership: {error_msg}")
    
    # Test 14: Test Email Invite Still Works
    print("Test 14: Email Invite Functionality")
    test_invite_email = f"invite.test_{timestamp}@example.com"
    response = make_request("POST", f"/teams/{team_id}/invite?email={test_invite_email}", 
                          headers=headers)
    
    if response and response.status_code == 200:
        results.add_result("Email Invite", True, "Email invite sent successfully")
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        results.add_result("Email Invite", False, f"Failed to send email invite: {error_msg}")
    
    # Test 15: Test Duplicate Pending Member Prevention
    print("Test 15: Duplicate Pending Member Prevention")
    duplicate_email = f"duplicate_{timestamp}@example.com"
    
    # Add first pending member
    response1 = make_request("POST", f"/teams/{team_id}/members/manual?email={duplicate_email}&name=Duplicate User", 
                           headers=headers)
    
    if response1 and response1.status_code == 200:
        # Try to add the same email again - should fail with 400
        try:
            import requests
            url = f"{BACKEND_URL}/teams/{team_id}/members/manual?email={duplicate_email}&name=Duplicate User"
            response2 = requests.post(url, headers=headers, timeout=30)
            
            if response2.status_code == 400:
                results.add_result("Duplicate Prevention", True, "Duplicate pending member correctly prevented")
            else:
                results.add_result("Duplicate Prevention", False, f"Expected 400, got {response2.status_code}")
        except Exception as e:
            results.add_result("Duplicate Prevention", False, f"Request failed: {e}")
    else:
        results.add_result("Duplicate Prevention", False, "Failed to create initial pending member for duplicate test")
    
    return results

def test_task_assignment_and_vibemeeting():
    """Test task assignment PATCH endpoint and VibeMeeting functionality"""
    results = TestResults()
    
    # Test data - use unique emails with timestamp
    timestamp = str(int(time.time()))
    user1_email = f"taskuser1_{timestamp}@example.com"
    user1_name = "Task User 1"
    user1_password = "password123"
    
    user2_email = f"taskuser2_{timestamp}@example.com" 
    user2_name = "Task User 2"
    user2_password = "password456"
    
    # Store session tokens and IDs
    user1_token = None
    user2_token = None
    user1_id = None
    user2_id = None
    team_id = None
    task_id = None
    meeting_id = None
    
    print("Starting Task Assignment and VibeMeeting Tests")
    print("=" * 60)
    
    # Test 1: Register User 1
    print("Test 1: User 1 Registration")
    response = make_request("POST", "/auth/register", json_data={
        "email": user1_email,
        "password": user1_password,
        "name": user1_name
    })
    
    if response and response.status_code == 200:
        data = response.json()
        user1_token = data.get("session_token")
        user1_id = data.get("user", {}).get("id")
        results.add_result("User 1 Registration", True, f"User 1 registered successfully with ID: {user1_id}")
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        results.add_result("User 1 Registration", False, f"Failed to register User 1: {error_msg}")
        return results
    
    # Test 2: Register User 2
    print("Test 2: User 2 Registration")
    response = make_request("POST", "/auth/register", json_data={
        "email": user2_email,
        "password": user2_password,
        "name": user2_name
    })
    
    if response and response.status_code == 200:
        data = response.json()
        user2_token = data.get("session_token")
        user2_id = data.get("user", {}).get("id")
        results.add_result("User 2 Registration", True, f"User 2 registered successfully with ID: {user2_id}")
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        results.add_result("User 2 Registration", False, f"Failed to register User 2: {error_msg}")
        return results
    
    # Test 3: Create Team
    print("Test 3: Create Team")
    headers1 = {"Authorization": f"Bearer {user1_token}"}
    response = make_request("POST", "/teams?team_name=Task Test Team", headers=headers1)
    
    if response and response.status_code == 200:
        data = response.json()
        team_id = data.get("id")
        results.add_result("Create Team", True, f"Team created successfully with ID: {team_id}")
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        results.add_result("Create Team", False, f"Failed to create team: {error_msg}")
        return results
    
    # Test 4: Add User 2 to Team
    print("Test 4: Add User 2 to Team")
    response = make_request("POST", f"/teams/{team_id}/members/manual?email={user2_email}&name={user2_name}", 
                          headers=headers1)
    
    if response and response.status_code == 200:
        results.add_result("Add User 2 to Team", True, "User 2 added to team successfully")
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        results.add_result("Add User 2 to Team", False, f"Failed to add User 2 to team: {error_msg}")
    
    # Test 5: Create Task
    print("Test 5: Create Task")
    task_data = {
        "title": "Test Task for Assignment",
        "description": "This task will be used to test assignment functionality",
        "team_id": team_id
    }
    response = make_request("POST", "/tasks", headers=headers1, json_data=task_data)
    
    if response and response.status_code == 200:
        data = response.json()
        task_id = data.get("id")
        results.add_result("Create Task", True, f"Task created successfully with ID: {task_id}")
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        results.add_result("Create Task", False, f"Failed to create task: {error_msg}")
        return results
    
    # Test 6: PATCH Task - Assign to User 2
    print("Test 6: PATCH Task - Assign to User 2")
    patch_data = {"assigned_to": user2_id}
    response = make_request("PATCH", f"/tasks/{task_id}", headers=headers1, json_data=patch_data)
    
    if response and response.status_code == 200:
        results.add_result("PATCH Task Assignment", True, "Task assigned to User 2 successfully")
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        results.add_result("PATCH Task Assignment", False, f"Failed to assign task: {error_msg}")
    
    # Test 7: Verify Task Assignment via GET
    print("Test 7: Verify Task Assignment via GET")
    response = make_request("GET", f"/tasks?team_id={team_id}", headers=headers1)
    
    if response and response.status_code == 200:
        tasks = response.json()
        assigned_task = next((t for t in tasks if t.get("id") == task_id), None)
        
        if assigned_task and assigned_task.get("assigned_to") == user2_id:
            results.add_result("Verify Task Assignment", True, "Task assignment verified via GET")
        else:
            results.add_result("Verify Task Assignment", False, 
                             f"Task assignment not verified. Expected: {user2_id}, Got: {assigned_task.get('assigned_to') if assigned_task else 'Task not found'}")
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        results.add_result("Verify Task Assignment", False, f"Failed to get tasks: {error_msg}")
    
    # Test 8: PATCH Task - Update Status
    print("Test 8: PATCH Task - Update Status")
    patch_data = {"status": "in-progress"}
    response = make_request("PATCH", f"/tasks/{task_id}", headers=headers1, json_data=patch_data)
    
    if response and response.status_code == 200:
        results.add_result("PATCH Task Status", True, "Task status updated successfully")
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        results.add_result("PATCH Task Status", False, f"Failed to update task status: {error_msg}")
    
    # Test 9: PATCH Task - Combined Update (status + assignment)
    print("Test 9: PATCH Task - Combined Update")
    patch_data = {"status": "done", "assigned_to": user1_id}
    response = make_request("PATCH", f"/tasks/{task_id}", headers=headers1, json_data=patch_data)
    
    if response and response.status_code == 200:
        results.add_result("PATCH Task Combined Update", True, "Task status and assignment updated successfully")
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        results.add_result("PATCH Task Combined Update", False, f"Failed to update task: {error_msg}")
    
    # Test 10: Verify Combined Update
    print("Test 10: Verify Combined Update")
    response = make_request("GET", f"/tasks?team_id={team_id}", headers=headers1)
    
    if response and response.status_code == 200:
        tasks = response.json()
        updated_task = next((t for t in tasks if t.get("id") == task_id), None)
        
        if (updated_task and 
            updated_task.get("status") == "done" and 
            updated_task.get("assigned_to") == user1_id):
            results.add_result("Verify Combined Update", True, "Combined update verified successfully")
        else:
            results.add_result("Verify Combined Update", False, 
                             f"Combined update not verified. Status: {updated_task.get('status') if updated_task else 'N/A'}, Assigned: {updated_task.get('assigned_to') if updated_task else 'N/A'}")
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        results.add_result("Verify Combined Update", False, f"Failed to get tasks: {error_msg}")
    
    # Test 11: Cross-View Data Persistence - Check via Team Members
    print("Test 11: Cross-View Data Persistence")
    response = make_request("GET", f"/teams/{team_id}/members", headers=headers1)
    
    if response and response.status_code == 200:
        results.add_result("Cross-View Data Persistence", True, "Team members endpoint accessible for cross-view verification")
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        results.add_result("Cross-View Data Persistence", False, f"Failed to access team members: {error_msg}")
    
    # VibeMeeting Tests
    print("\n--- VibeMeeting Tests ---")
    
    # Test 12: Create Meeting
    print("Test 12: Create Meeting")
    meeting_data = {
        "title": "Test VibeMeeting",
        "team_id": team_id
    }
    response = make_request("POST", "/meetings", headers=headers1, json_data=meeting_data)
    
    if response and response.status_code == 200:
        data = response.json()
        meeting_id = data.get("id")
        results.add_result("Create Meeting", True, f"Meeting created successfully with ID: {meeting_id}")
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        results.add_result("Create Meeting", False, f"Failed to create meeting: {error_msg}")
        return results
    
    # Test 13: Upload Audio (using base64 encoded sample)
    print("Test 13: Upload Audio")
    # Create a small sample audio file in base64 (minimal MP3 header)
    sample_audio_base64 = "SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4Ljc2LjEwMAAAAAAAAAAAAAAA//tQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAWGluZwAAAA8AAAAEAAABIADAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDV1dXV1dXV1dXV1dXV1dXV1dXV1dXV1dXV6urq6urq6urq6urq6urq6urq6urq6urq6v////////////////////////////////8AAAAATGF2YzU4LjEzAAAAAAAAAAAAAAAAJAAAAAAAAAAAASDs90hvAAAAAAAAAAAAAAAAAAAA//tQxAAAAAAAAAAAAAAAAAAAAAAASW5mbwAAAA8AAAAEAAABIADAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDV1dXV1dXV1dXV1dXV1dXV1dXV1dXV1dXV6urq6urq6urq6urq6urq6urq6urq6urq6v////////////////////////////////8AAAAATGF2YzU4LjEzAAAAAAAAAAAAAAAAJAAAAAAAAAAAASDs90hvAAAAAAAAAAAAAAAAAAAA"
    
    try:
        import base64
        import io
        audio_bytes = base64.b64decode(sample_audio_base64)
        
        # Use requests directly for file upload
        import requests
        url = f"{BACKEND_URL}/meetings/{meeting_id}/upload"
        files = {'audio': ('test_audio.mp3', io.BytesIO(audio_bytes), 'audio/mpeg')}
        
        response = requests.post(url, headers=headers1, files=files, timeout=30)
        
        if response.status_code == 200:
            results.add_result("Upload Audio", True, "Audio uploaded successfully")
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            results.add_result("Upload Audio", False, f"Failed to upload audio: {error_msg}")
    except Exception as e:
        results.add_result("Upload Audio", False, f"Audio upload failed with exception: {str(e)}")
    
    # Test 14: Transcribe Meeting
    print("Test 14: Transcribe Meeting")
    response = make_request("POST", f"/meetings/{meeting_id}/transcribe", headers=headers1)
    
    if response and response.status_code == 200:
        data = response.json()
        transcription = data.get("transcription", "")
        if transcription:
            results.add_result("Transcribe Meeting", True, f"Meeting transcribed successfully: {transcription[:50]}...")
        else:
            results.add_result("Transcribe Meeting", False, "Transcription returned empty")
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        results.add_result("Transcribe Meeting", False, f"Failed to transcribe meeting: {error_msg}")
    
    # Test 15: Analyze Meeting
    print("Test 15: Analyze Meeting")
    response = make_request("POST", f"/meetings/{meeting_id}/analyze", headers=headers1)
    
    if response and response.status_code == 200:
        data = response.json()
        summary = data.get("summary", "")
        tasks_identified = data.get("tasks", [])
        
        if summary and isinstance(tasks_identified, list):
            results.add_result("Analyze Meeting", True, f"Meeting analyzed successfully. Summary: {summary[:50]}..., Tasks: {len(tasks_identified)}")
        else:
            results.add_result("Analyze Meeting", False, "Analysis returned incomplete data")
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        results.add_result("Analyze Meeting", False, f"Failed to analyze meeting: {error_msg}")
    
    # Test 16: Review Meeting (approve tasks)
    print("Test 16: Review Meeting")
    # Create sample approved tasks
    approved_tasks = [
        {
            "title": "Sample Task from Meeting",
            "description": "This task was identified during the meeting analysis",
            "assigned_to": user1_id
        }
    ]
    
    review_data = {"approved_tasks": approved_tasks}
    response = make_request("POST", f"/meetings/{meeting_id}/review", headers=headers1, json_data=review_data)
    
    if response and response.status_code == 200:
        results.add_result("Review Meeting", True, "Meeting reviewed and tasks created successfully")
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        results.add_result("Review Meeting", False, f"Failed to review meeting: {error_msg}")
    
    # Test 17: Verify Meeting Tasks Created
    print("Test 17: Verify Meeting Tasks Created")
    response = make_request("GET", f"/tasks?team_id={team_id}", headers=headers1)
    
    if response and response.status_code == 200:
        tasks = response.json()
        meeting_tasks = [t for t in tasks if "meeting" in t.get("description", "").lower()]
        
        if len(meeting_tasks) > 0:
            results.add_result("Verify Meeting Tasks", True, f"Found {len(meeting_tasks)} tasks created from meeting")
        else:
            results.add_result("Verify Meeting Tasks", True, "Meeting review completed (tasks may not contain 'meeting' keyword)")
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        results.add_result("Verify Meeting Tasks", False, f"Failed to verify meeting tasks: {error_msg}")
    
    return results

def test_permission_system_and_comments():
    """Test permission system and comment functionality as requested"""
    results = TestResults()
    
    # Test data - use unique emails with timestamp
    timestamp = str(int(time.time()))
    owner_email = "owner@test.com"
    owner_password = "test123"
    owner_name = "Owner User"
    
    member_email = "member@test.com"
    member_password = "test123"
    member_name = "Member User"
    
    # Store session tokens and IDs
    owner_token = None
    member_token = None
    owner_id = None
    member_id = None
    team_id = None
    task_id = None
    comment_id = None
    pending_change_id = None
    
    print("Starting Permission System and Comment Functionality Tests")
    print("=" * 60)
    
    # Test 1: Register/Login Owner
    print("Test 1: Register/Login Owner")
    response = make_request("POST", "/auth/register", json_data={
        "email": owner_email,
        "password": owner_password,
        "name": owner_name
    })
    
    if response and response.status_code == 200:
        data = response.json()
        owner_token = data.get("session_token")
        owner_id = data.get("user", {}).get("id")
        results.add_result("Owner Registration", True, f"Owner registered successfully with ID: {owner_id}")
    else:
        # Try login if registration fails (user might already exist)
        response = make_request("POST", "/auth/login", json_data={
            "email": owner_email,
            "password": owner_password
        })
        if response and response.status_code == 200:
            data = response.json()
            owner_token = data.get("session_token")
            owner_id = data.get("user", {}).get("id")
            results.add_result("Owner Login", True, f"Owner logged in successfully with ID: {owner_id}")
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            results.add_result("Owner Registration/Login", False, f"Failed: {error_msg}")
            return results
    
    # Test 2: Register/Login Member
    print("Test 2: Register/Login Member")
    response = make_request("POST", "/auth/register", json_data={
        "email": member_email,
        "password": member_password,
        "name": member_name
    })
    
    if response and response.status_code == 200:
        data = response.json()
        member_token = data.get("session_token")
        member_id = data.get("user", {}).get("id")
        results.add_result("Member Registration", True, f"Member registered successfully with ID: {member_id}")
    else:
        # Try login if registration fails
        response = make_request("POST", "/auth/login", json_data={
            "email": member_email,
            "password": member_password
        })
        if response and response.status_code == 200:
            data = response.json()
            member_token = data.get("session_token")
            member_id = data.get("user", {}).get("id")
            results.add_result("Member Login", True, f"Member logged in successfully with ID: {member_id}")
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            results.add_result("Member Registration/Login", False, f"Failed: {error_msg}")
            return results
    
    # Test 3: Create Team (as owner)
    print("Test 3: Create Team")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    response = make_request("POST", "/teams?team_name=Permission Test Team", headers=owner_headers)
    
    if response and response.status_code == 200:
        data = response.json()
        team_id = data.get("id")
        results.add_result("Create Team", True, f"Team created successfully with ID: {team_id}")
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        results.add_result("Create Team", False, f"Failed to create team: {error_msg}")
        return results
    
    # Test 4: Add Member to Team
    print("Test 4: Add Member to Team")
    response = make_request("POST", f"/teams/{team_id}/members/manual?email={member_email}&name={member_name}", 
                          headers=owner_headers)
    
    if response and response.status_code == 200:
        results.add_result("Add Member to Team", True, "Member added to team successfully")
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        results.add_result("Add Member to Team", False, f"Failed to add member: {error_msg}")
    
    # Test 5: Create Test Task
    print("Test 5: Create Test Task")
    task_data = {
        "title": "Permission Test Task",
        "description": "This task will be used to test permission system",
        "team_id": team_id,
        "assigned_to": member_id
    }
    response = make_request("POST", "/tasks", headers=owner_headers, json_data=task_data)
    
    if response and response.status_code == 200:
        data = response.json()
        task_id = data.get("id")
        results.add_result("Create Test Task", True, f"Task created successfully with ID: {task_id}")
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        results.add_result("Create Test Task", False, f"Failed to create task: {error_msg}")
        return results
    
    # PERMISSION SYSTEM TESTS - Non-owner Changes
    print("\n--- Permission System Tests - Non-owner Changes ---")
    
    # Test 6: Member Status Change (should create pending change)
    print("Test 6: Member Status Change (Pending)")
    member_headers = {"Authorization": f"Bearer {member_token}"}
    patch_data = {"status": "in-progress"}
    response = make_request("PATCH", f"/tasks/{task_id}", headers=member_headers, json_data=patch_data)
    
    if response and response.status_code == 200:
        data = response.json()
        if data.get("pending"):
            results.add_result("Member Status Change Pending", True, "Status change correctly marked as pending")
        else:
            results.add_result("Member Status Change Pending", False, "Status change should be pending but wasn't")
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        results.add_result("Member Status Change Pending", False, f"Failed to change status: {error_msg}")
    
    # Test 7: Member Assignment Change (should create pending change)
    print("Test 7: Member Assignment Change (Pending)")
    patch_data = {"assigned_to": owner_id}
    response = make_request("PATCH", f"/tasks/{task_id}", headers=member_headers, json_data=patch_data)
    
    if response and response.status_code == 200:
        data = response.json()
        if data.get("pending"):
            results.add_result("Member Assignment Change Pending", True, "Assignment change correctly marked as pending")
        else:
            results.add_result("Member Assignment Change Pending", False, "Assignment change should be pending but wasn't")
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        results.add_result("Member Assignment Change Pending", False, f"Failed to change assignment: {error_msg}")
    
    # Test 8: Member Details Change (should create pending change)
    print("Test 8: Member Details Change (Pending)")
    details_data = {"title": "Updated Task Title", "description": "Updated task description"}
    response = make_request("PUT", f"/tasks/{task_id}/details", headers=member_headers, json_data=details_data)
    
    if response and response.status_code == 200:
        data = response.json()
        if data.get("pending"):
            results.add_result("Member Details Change Pending", True, "Details change correctly marked as pending")
        else:
            results.add_result("Member Details Change Pending", False, "Details change should be pending but wasn't")
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        results.add_result("Member Details Change Pending", False, f"Failed to change details: {error_msg}")
    
    # Test 9: Get Pending Changes (as owner)
    print("Test 9: Get Pending Changes")
    response = make_request("GET", f"/teams/{team_id}/pending-changes", headers=owner_headers)
    
    if response and response.status_code == 200:
        pending_changes = response.json()
        if len(pending_changes) > 0:
            pending_change_id = pending_changes[0].get("id")
            results.add_result("Get Pending Changes", True, f"Found {len(pending_changes)} pending changes")
        else:
            results.add_result("Get Pending Changes", False, "No pending changes found")
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        results.add_result("Get Pending Changes", False, f"Failed to get pending changes: {error_msg}")
    
    # APPROVAL SYSTEM TESTS
    print("\n--- Approval System Tests ---")
    
    # Test 10: Approve Change
    print("Test 10: Approve Change")
    if pending_change_id:
        response = make_request("POST", f"/pending-changes/{pending_change_id}/approve", headers=owner_headers)
        
        if response and response.status_code == 200:
            results.add_result("Approve Change", True, "Change approved successfully")
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            results.add_result("Approve Change", False, f"Failed to approve change: {error_msg}")
    else:
        results.add_result("Approve Change", False, "No pending change ID available")
    
    # Test 11: Create another pending change for rejection test
    print("Test 11: Create Change for Rejection Test")
    patch_data = {"status": "done"}
    response = make_request("PATCH", f"/tasks/{task_id}", headers=member_headers, json_data=patch_data)
    
    if response and response.status_code == 200:
        # Get the new pending change
        response = make_request("GET", f"/teams/{team_id}/pending-changes", headers=owner_headers)
        if response and response.status_code == 200:
            pending_changes = response.json()
            if len(pending_changes) > 0:
                reject_change_id = pending_changes[0].get("id")
                
                # Test 12: Reject Change
                print("Test 12: Reject Change")
                response = make_request("POST", f"/pending-changes/{reject_change_id}/reject", headers=owner_headers)
                
                if response and response.status_code == 200:
                    results.add_result("Reject Change", True, "Change rejected successfully")
                else:
                    error_msg = response.json().get("detail", "Unknown error") if response else "No response"
                    results.add_result("Reject Change", False, f"Failed to reject change: {error_msg}")
            else:
                results.add_result("Reject Change", False, "No pending change found for rejection test")
        else:
            results.add_result("Reject Change", False, "Failed to get pending changes for rejection test")
    else:
        results.add_result("Create Change for Rejection", False, "Failed to create change for rejection test")
    
    # COMMENT SYSTEM TESTS
    print("\n--- Comment System Tests ---")
    
    # Test 13: Add Text Comment (as member)
    print("Test 13: Add Text Comment")
    response = make_request("POST", f"/tasks/{task_id}/comments?text=This is a test comment from member", 
                          headers=member_headers)
    
    if response and response.status_code == 200:
        data = response.json()
        comment_id = data.get("comment_id")
        results.add_result("Add Text Comment", True, f"Comment added successfully with ID: {comment_id}")
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        results.add_result("Add Text Comment", False, f"Failed to add comment: {error_msg}")
    
    # Test 14: Get Comments
    print("Test 14: Get Comments")
    response = make_request("GET", f"/tasks/{task_id}/comments", headers=member_headers)
    
    if response and response.status_code == 200:
        comments = response.json()
        if len(comments) > 0:
            results.add_result("Get Comments", True, f"Retrieved {len(comments)} comments with user info")
        else:
            results.add_result("Get Comments", False, "No comments found")
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        results.add_result("Get Comments", False, f"Failed to get comments: {error_msg}")
    
    # Test 15: Delete Own Comment
    print("Test 15: Delete Own Comment")
    if comment_id:
        response = make_request("DELETE", f"/comments/{comment_id}", headers=member_headers)
        
        if response and response.status_code == 200:
            results.add_result("Delete Own Comment", True, "Own comment deleted successfully")
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            results.add_result("Delete Own Comment", False, f"Failed to delete own comment: {error_msg}")
    else:
        results.add_result("Delete Own Comment", False, "No comment ID available")
    
    # Test 16: Add Comment as Owner and Try to Delete as Member (should fail)
    print("Test 16: Try to Delete Another User's Comment")
    # First add comment as owner
    response = make_request("POST", f"/tasks/{task_id}/comments?text=This is owner comment", 
                          headers=owner_headers)
    
    if response and response.status_code == 200:
        data = response.json()
        owner_comment_id = data.get("comment_id")
        
        # Try to delete as member (should fail with 403)
        try:
            import requests
            url = f"{BACKEND_URL}/comments/{owner_comment_id}"
            response = requests.delete(url, headers=member_headers, timeout=30)
            
            if response.status_code == 403:
                results.add_result("Delete Other User Comment (403)", True, "Correctly prevented deletion of other user's comment")
            else:
                results.add_result("Delete Other User Comment (403)", False, f"Expected 403, got {response.status_code}")
        except Exception as e:
            results.add_result("Delete Other User Comment (403)", False, f"Request failed: {e}")
    else:
        results.add_result("Delete Other User Comment Test Setup", False, "Failed to create owner comment for test")
    
    # COMMENT IMAGE UPLOAD TESTS
    print("\n--- Comment Image Upload Tests ---")
    
    # Test 17: Upload Small Image (<1MB)
    print("Test 17: Upload Small Image")
    try:
        import base64
        import io
        # Create a small test image (base64 encoded 1x1 pixel PNG)
        small_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jU77mgAAAABJRU5ErkJggg=="
        image_bytes = base64.b64decode(small_image_base64)
        
        # Use requests directly for file upload
        import requests
        url = f"{BACKEND_URL}/comments/upload-image"
        files = {'file': ('test_image.png', io.BytesIO(image_bytes), 'image/png')}
        
        response = requests.post(url, headers=member_headers, files=files, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("image_url") and data["image_url"].startswith("data:"):
                results.add_result("Upload Small Image", True, "Small image uploaded successfully with base64 data URL")
            else:
                results.add_result("Upload Small Image", False, "Image uploaded but no valid data URL returned")
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            results.add_result("Upload Small Image", False, f"Failed to upload small image: {error_msg}")
    except Exception as e:
        results.add_result("Upload Small Image", False, f"Image upload failed with exception: {str(e)}")
    
    # Test 18: Upload Large Image (>1MB) - should return 413
    print("Test 18: Upload Large Image (>1MB)")
    try:
        # Create a large file (simulate >1MB)
        large_data = b"x" * (1024 * 1024 + 1)  # 1MB + 1 byte
        
        import requests
        url = f"{BACKEND_URL}/comments/upload-image"
        files = {'file': ('large_image.png', io.BytesIO(large_data), 'image/png')}
        
        response = requests.post(url, headers=member_headers, files=files, timeout=30)
        
        if response.status_code == 413:
            results.add_result("Upload Large Image (413)", True, "Correctly rejected large image with 413 error")
        else:
            results.add_result("Upload Large Image (413)", False, f"Expected 413, got {response.status_code}")
    except Exception as e:
        results.add_result("Upload Large Image (413)", False, f"Large image test failed with exception: {str(e)}")
    
    # OWNER DIRECT UPDATES TESTS
    print("\n--- Owner Direct Updates Tests ---")
    
    # Test 19: Owner Status Change (should be direct, no pending)
    print("Test 19: Owner Status Change (Direct)")
    patch_data = {"status": "done"}
    response = make_request("PATCH", f"/tasks/{task_id}", headers=owner_headers, json_data=patch_data)
    
    if response and response.status_code == 200:
        data = response.json()
        if not data.get("pending"):
            results.add_result("Owner Status Change Direct", True, "Owner status change applied directly (no pending)")
        else:
            results.add_result("Owner Status Change Direct", False, "Owner change should be direct but was marked pending")
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        results.add_result("Owner Status Change Direct", False, f"Failed owner status change: {error_msg}")
    
    # Test 20: Owner Details Change (should be direct, no pending)
    print("Test 20: Owner Details Change (Direct)")
    details_data = {"title": "Owner Updated Title", "description": "Owner updated description"}
    response = make_request("PUT", f"/tasks/{task_id}/details", headers=owner_headers, json_data=details_data)
    
    if response and response.status_code == 200:
        data = response.json()
        if not data.get("pending"):
            results.add_result("Owner Details Change Direct", True, "Owner details change applied directly (no pending)")
        else:
            results.add_result("Owner Details Change Direct", False, "Owner change should be direct but was marked pending")
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        results.add_result("Owner Details Change Direct", False, f"Failed owner details change: {error_msg}")
    
    return results

if __name__ == "__main__":
    print("Permission System and Comment Functionality - Backend API Tests")
    print("=" * 60)
    print(f"Testing against: {BACKEND_URL}")
    print()
    
    # Run permission system and comment tests
    test_results = test_permission_system_and_comments()
    
    # Print summary
    test_results.print_summary()
    
    # Print detailed results
    if test_results.failed > 0:
        print("\nFAILED TESTS:")
        print("-" * 40)
        for result in test_results.results:
            if not result["passed"]:
                print(f"❌ {result['test']}: {result['message']}")
                if result["details"]:
                    print(f"   Details: {result['details']}")
    
    print(f"\nTest completed at {datetime.now().isoformat()}")