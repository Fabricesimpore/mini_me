"""Seed test data for the Digital Twin Platform"""
import requests
import json
from datetime import datetime, timedelta

API_URL = "http://localhost:8000"

# Test credentials
USERNAME = "test@example.com"
PASSWORD = "test123"

print("🌱 Seeding test data for Digital Twin Platform...")

# 1. Login to get token
print("\n1. Logging in...")
login_data = {
    "username": USERNAME,
    "password": PASSWORD
}
response = requests.post(
    f"{API_URL}/api/auth/token",
    data=login_data,
    headers={"Content-Type": "application/x-www-form-urlencoded"}
)

if response.status_code != 200:
    print(f"❌ Login failed: {response.text}")
    exit(1)

token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("✅ Logged in successfully")

# 2. Send some chat messages
print("\n2. Creating chat history...")
chat_messages = [
    "Hi, I'm starting to use this digital twin platform",
    "Can you help me understand my work patterns?",
    "I've been feeling more productive in the mornings",
    "What insights do you have about my communication style?",
    "I prefer visual learning and hands-on practice"
]

for msg in chat_messages:
    response = requests.post(
        f"{API_URL}/api/chat/message",
        json={"content": msg},
        headers=headers
    )
    if response.status_code == 200:
        print(f"✅ Sent: '{msg[:50]}...'")
    else:
        print(f"❌ Failed to send message: {response.text}")

# 3. Add behavioral data
print("\n3. Adding behavioral data...")
behavioral_data = [
    {
        "endpoint": "/api/behavioral/mood",
        "data": {"mood": "focused", "energy_level": 8, "notes": "Great morning session"}
    },
    {
        "endpoint": "/api/behavioral/activity-summary",
        "data": {
            "date": datetime.now().isoformat(),
            "activities": {
                "coding": 240,
                "meetings": 90,
                "email": 45,
                "break": 60
            }
        }
    }
]

for item in behavioral_data:
    response = requests.post(
        f"{API_URL}{item['endpoint']}",
        json=item["data"],
        headers=headers
    )
    if response.status_code == 200:
        print(f"✅ Added data to {item['endpoint']}")
    else:
        print(f"⚠️  {item['endpoint']}: {response.status_code}")

# 4. Add memory entries
print("\n4. Adding memory entries...")
memories = [
    {
        "content": "Completed the user authentication system using JWT tokens",
        "memory_type": "achievement",
        "tags": ["coding", "backend", "security"]
    },
    {
        "content": "Had a productive meeting about the new ML features",
        "memory_type": "event",
        "tags": ["meeting", "planning", "ml"]
    },
    {
        "content": "Learned about React hooks and state management",
        "memory_type": "learning",
        "tags": ["react", "frontend", "learning"]
    }
]

for memory in memories:
    response = requests.post(
        f"{API_URL}/api/memory/",
        json=memory,
        headers=headers
    )
    if response.status_code == 200:
        print(f"✅ Added memory: '{memory['content'][:50]}...'")
    else:
        print(f"⚠️  Memory creation: {response.status_code}")

# 5. Connect integrations (mock)
print("\n5. Connecting integrations...")
integrations = ["gmail", "calendar", "todoist"]

for integration in integrations:
    response = requests.post(
        f"{API_URL}/api/{integration}/connect",
        headers=headers
    )
    if response.status_code == 200:
        print(f"✅ Connected {integration.capitalize()}")
    else:
        print(f"⚠️  {integration}: {response.status_code}")

# 6. Analyze profile
print("\n6. Analyzing cognitive profile...")
response = requests.post(
    f"{API_URL}/api/profile/analyze?force_full_analysis=true",
    headers=headers
)
if response.status_code == 200:
    print("✅ Profile analysis completed")
else:
    print(f"⚠️  Profile analysis: {response.status_code}")

print("\n✨ Test data seeding completed!")
print("\nYou can now:")
print("- Login with test@example.com / test123")
print("- Check the chat history")
print("- View your cognitive profile")
print("- See behavioral analytics")
print("- Browse memory entries")
print("- Check integration statuses")