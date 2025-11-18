#!/usr/bin/env python3
"""
VAPI Assistant Setup Script
This script creates or updates an assistant in VAPI with custom voice and model providers.
"""

import requests
import json
import sys

# VAPI Configuration
VAPI_API_KEY = "e9a3ceee-8b25-411a-bf73-64a1a471dd4c"
VAPI_BASE_URL = "https://api.vapi.ai"

def create_assistant(name="Laya Assistant", first_message="Hello! How can I help you today?"):
    """
    Create a new assistant in VAPI with Google Gemini model and voice.

    Args:
        name: Name of the assistant
        first_message: The first message the assistant will say

    Returns:
        dict: The created assistant data
    """
    url = f"{VAPI_BASE_URL}/assistant"

    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }

    # Assistant configuration with Google Gemini model and custom voice provider
    # The voice/TTS is handled by the custom TTS server (gemini_tts_server.py)
    # which internally uses Gemini Live with native audio
    payload = {
        "name": name,
        "model": {
            "provider": "google",
            "model": "gemini-2.5-flash"
        },
        # Using custom-voice with Gemini Live TTS server
        # The TTS server handles Gemini Live voice synthesis internally
        # NOTE: VAPI automatically adds "voiceId": "sarah" to custom-voice configs
        # We don't include it here to avoid validation errors, but VAPI will add it after creation
        # The TTS server reads the voiceId from VAPI's webhook request dynamically
        "voice": {
            "provider": "custom-voice",
            "server": {
                "url": "https://unfriable-audacious-taisha.ngrok-free.dev/api/synthesize",
                "secret": "laya-tts-secret-2025",  # Same as VAPI_SECRET in gemini_tts_server.py
                "timeoutSeconds": 30
            }
        },
        "transcriber": {
            "language": "Hebrew",
            "model": "gemini-2.0-flash",
            "provider": "google"
        },
        "firstMessage": first_message,
        # Optional: Add more configuration as needed
        # "recordingEnabled": True,
        # "endCallMessage": "Thank you for calling. Goodbye!",
        # "endCallPhrases": ["goodbye", "bye", "end call"]
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        assistant_data = response.json()
        print("✅ Assistant created successfully!")
        print(f"Assistant ID: {assistant_data.get('id')}")
        print(f"Assistant Name: {assistant_data.get('name')}")
        print("\nFull response:")
        print(json.dumps(assistant_data, indent=2))

        return assistant_data

    except requests.exceptions.RequestException as e:
        print(f"❌ Error creating assistant: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        sys.exit(1)


def list_assistants():
    """
    List all assistants in the VAPI account.

    Returns:
        list: List of assistants
    """
    url = f"{VAPI_BASE_URL}/assistant"

    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        assistants = response.json()
        print(f"\n📋 Found {len(assistants)} assistant(s):")
        for assistant in assistants:
            print(f"  - {assistant.get('name')} (ID: {assistant.get('id')})")

        return assistants

    except requests.exceptions.RequestException as e:
        print(f"❌ Error listing assistants: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return []


def update_assistant(assistant_id, updates):
    """
    Update an existing assistant.

    Args:
        assistant_id: The ID of the assistant to update
        updates: Dictionary of fields to update

    Returns:
        dict: The updated assistant data
    """
    url = f"{VAPI_BASE_URL}/assistant/{assistant_id}"

    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.patch(url, headers=headers, json=updates)
        response.raise_for_status()

        assistant_data = response.json()
        print("✅ Assistant updated successfully!")
        print(json.dumps(assistant_data, indent=2))

        return assistant_data

    except requests.exceptions.RequestException as e:
        print(f"❌ Error updating assistant: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        sys.exit(1)


if __name__ == "__main__":
    print("🚀 VAPI Assistant Setup\n")
    print("=" * 50)

    # List existing assistants
    print("\nChecking existing assistants...")
    existing_assistants = list_assistants()

    # Create new assistant
    print("\n" + "=" * 50)
    print("\nCreating new assistant with Google Gemini Live native audio...")
    assistant = create_assistant(
        name="Laya Assistant - Gemini Live",
        first_message="Hello! I'm Laya, your AI assistant. How can I help you today?"
    )

    print("\n" + "=" * 50)
    print("\n✨ Setup complete!")
    print(f"\nYou can now use this assistant ID in your application:")
    print(f"Assistant ID: {assistant.get('id')}")
