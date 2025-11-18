"""
Test script for lead creation
"""
import requests
import json

BASE_URL = "http://localhost:8000"

# Test 1: Drop-off lead
print("=" * 60)
print("Test 1: Creating drop-off lead")
print("=" * 60)

drop_off_lead = {
    "name": "יוסי כהן",
    "phone": "+972501234567",
    "type": "drop-off",
    "drop_stage": "identity_verify",
    "notes": "Test lead from script"
}

print(f"\n📤 Sending: {json.dumps(drop_off_lead, ensure_ascii=False, indent=2)}")

try:
    response = requests.post(
        f"{BASE_URL}/api/leads/",
        json=drop_off_lead,
        headers={"Content-Type": "application/json"}
    )
    print(f"\n📊 Status Code: {response.status_code}")
    print(f"📋 Response: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

    if response.status_code == 201:
        print("\n✅ Drop-off lead created successfully!")
    else:
        print(f"\n❌ Failed to create drop-off lead")

except Exception as e:
    print(f"\n❌ Error: {e}")

print("\n" + "=" * 60)
print("Test 2: Creating dormant lead")
print("=" * 60)

dormant_lead = {
    "name": "שרה לוי",
    "phone": "+972507654321",
    "type": "dormant",
    "last_active": "2024-01-15T10:30:00.000Z",
    "notes": "Test dormant lead"
}

print(f"\n📤 Sending: {json.dumps(dormant_lead, ensure_ascii=False, indent=2)}")

try:
    response = requests.post(
        f"{BASE_URL}/api/leads/",
        json=dormant_lead,
        headers={"Content-Type": "application/json"}
    )
    print(f"\n📊 Status Code: {response.status_code}")
    print(f"📋 Response: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

    if response.status_code == 201:
        print("\n✅ Dormant lead created successfully!")
    else:
        print(f"\n❌ Failed to create dormant lead")

except Exception as e:
    print(f"\n❌ Error: {e}")

print("\n" + "=" * 60)
