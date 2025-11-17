#!/usr/bin/env python3
"""
Gemini Live TTS Server for VAPI Custom Voice Integration

This server acts as a bridge between VAPI and Google Gemini Live API,
enabling Gemini Live native audio to be used as a custom voice provider in VAPI.
"""

from flask import Flask, request, jsonify, Response
import requests
import os
import json
import logging
from io import BytesIO
import asyncio
from google import genai
from google.genai import types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')  # Set your Google API key
VAPI_SECRET = os.getenv('VAPI_SECRET', 'your-secret-token')  # Secret for VAPI authentication
PORT = int(os.getenv('PORT', 8080))

# Configure Google Generative AI Client
client = None
if GOOGLE_API_KEY:
    client = genai.Client(api_key=GOOGLE_API_KEY)
    logger.info("Google Gemini Client initialized")
else:
    logger.warning("GOOGLE_API_KEY not set. Please set it in environment variables.")


def authenticate_request():
    """
    Authenticate incoming requests from VAPI.

    Returns:
        bool: True if authenticated, False otherwise
    """
    # Check for Authorization header
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        if token == VAPI_SECRET:
            return True

    # Check for secret in request body
    data = request.get_json(silent=True) or {}
    if data.get('secret') == VAPI_SECRET:
        return True

    return False


@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.
    """
    return jsonify({
        'status': 'healthy',
        'service': 'Gemini Live TTS Server',
        'version': '1.0.0'
    }), 200


@app.route('/synthesize', methods=['POST'])
def synthesize_speech():
    """
    Synthesize speech from text using Google Gemini Live API.

    Expected request format from VAPI:
    {
        "text": "Hello, how can I help you?",
        "voiceId": "Charon",  // Optional: Puck or Charon
        "encoding": "pcm_16000",  // Optional: audio encoding format
        "sampleRate": 16000  // Optional: sample rate
    }

    Returns:
        Audio stream or JSON error
    """
    # Parse request data first
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400

    # Authenticate request (now data is already parsed)
    auth_header = request.headers.get('Authorization')
    is_authenticated = False

    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        if token == VAPI_SECRET:
            is_authenticated = True

    if not is_authenticated and data.get('secret') == VAPI_SECRET:
        is_authenticated = True

    if not is_authenticated:
        logger.warning("Unauthorized request to /synthesize")
        return jsonify({'error': 'Unauthorized'}), 401

    text = data.get('text', '')
    if not text:
        return jsonify({'error': 'No text provided'}), 400

    voice_id = data.get('voiceId', 'Charon')  # Default to Charon
    encoding = data.get('encoding', 'pcm_16000')
    sample_rate = data.get('sampleRate', 16000)

    logger.info(f"Synthesizing: '{text[:50]}...' with voice: {voice_id}")

    try:
        if not client:
            return jsonify({'error': 'Google API client not initialized'}), 500

        # Use Gemini Live API with native audio
        audio_data = asyncio.run(synthesize_with_gemini_live(text, voice_id))

        if audio_data:
            # Return audio stream
            return Response(
                audio_data,
                mimetype='audio/pcm',
                headers={
                    'Content-Type': 'audio/pcm;rate=24000',
                    'Content-Disposition': 'inline; filename=speech.pcm'
                }
            )
        else:
            return jsonify({'error': 'Failed to synthesize speech'}), 500

    except Exception as e:
        logger.error(f"Error synthesizing speech: {e}")
        return jsonify({'error': str(e)}), 500


def synthesize_with_google_tts(text, voice_name='en-US-Studio-O'):
    """
    Synthesize speech using Google Cloud Text-to-Speech API.

    Args:
        text: Text to synthesize
        voice_name: Voice name to use

    Returns:
        bytes: Audio data
    """
    try:
        from google.cloud import texttospeech

        # Create a client
        client = texttospeech.TextToSpeechClient()

        # Set the text input
        synthesis_input = texttospeech.SynthesisInput(text=text)

        # Build the voice request
        voice = texttospeech.VoiceSelectionParams(
            language_code='en-US',
            name=voice_name
        )

        # Select the audio encoding
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000
        )

        # Perform the text-to-speech request
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )

        return response.audio_content

    except Exception as e:
        logger.error(f"Error with Google TTS: {e}")
        return None


async def synthesize_with_gemini_live(text, voice_name='Charon'):
    """
    Synthesize speech using Gemini Live API with native audio.

    Args:
        text: Text to synthesize
        voice_name: Voice name (Charon or Puck)

    Returns:
        bytes: Audio data in PCM format
    """
    try:
        # Model with native audio support
        model = "gemini-2.5-flash-native-audio-preview-09-2025"

        # Configuration for TTS
        config = {
            "response_modalities": ["AUDIO"],
            "speech_config": {
                "voice_config": {
                    "prebuilt_voice_config": {
                        "voice_name": voice_name
                    }
                }
            }
        }

        # Collect audio bytes
        audio_buffer = BytesIO()

        # Connect to Live API and send text
        async with client.aio.live.connect(model=model, config=config) as session:
            # Send the text as input
            await session.send(text, end_of_turn=True)

            # Receive audio response
            async for response in session.receive():
                # Check if response contains audio
                if response.server_content:
                    if hasattr(response.server_content, 'model_turn'):
                        for part in response.server_content.model_turn.parts:
                            if hasattr(part, 'inline_data') and part.inline_data:
                                # Extract audio data
                                audio_buffer.write(part.inline_data.data)

        audio_data = audio_buffer.getvalue()

        if audio_data:
            logger.info(f"Generated {len(audio_data)} bytes of audio")
            return audio_data
        else:
            logger.error("No audio data received from Gemini Live")
            return None

    except Exception as e:
        logger.error(f"Error with Gemini Live API: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


@app.route('/voices', methods=['GET'])
def list_voices():
    """
    List available voices.

    Returns:
        JSON list of available voices
    """
    voices = [
        {
            'id': 'Charon',
            'name': 'Charon',
            'language': 'en-US',
            'gender': 'MALE',
            'description': 'Gemini Live native voice - Charon'
        },
        {
            'id': 'Puck',
            'name': 'Puck',
            'language': 'en-US',
            'gender': 'NEUTRAL',
            'description': 'Gemini Live native voice - Puck'
        }
    ]

    return jsonify({'voices': voices}), 200


if __name__ == '__main__':
    logger.info(f"Starting Gemini Live TTS Server on port {PORT}")
    logger.info("Make sure to set GOOGLE_API_KEY environment variable")

    # Run the server
    app.run(
        host='0.0.0.0',
        port=PORT,
        debug=False
    )
