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


@app.route('/api/synthesize', methods=['POST'])
def synthesize_speech():
    """
    Synthesize speech from text using Google Gemini Live API.

    VAPI Request Format:
    {
        "message": {
            "type": "voice-request",
            "text": "Text to convert to speech",
            "sampleRate": 24000,
            "timestamp": 1677123456789,
            "call": {...},
            "assistant": {...},
            "customer": {...}
        }
    }

    Returns:
        Raw PCM audio data (16-bit signed integer, little-endian, mono)
    """
    try:
        # Parse request data
        data = request.get_json()
        if not data:
            logger.error("No JSON data provided")
            return jsonify({'error': 'No JSON data provided'}), 400

        # Extract message object
        message = data.get('message')
        if not message:
            logger.error("Missing message object")
            return jsonify({'error': 'Missing message object'}), 400

        # Validate message type
        msg_type = message.get('type')
        if msg_type != 'voice-request':
            logger.error(f"Invalid message type: {msg_type}")
            return jsonify({'error': 'Invalid message type'}), 400

        # Extract text
        text = message.get('text', '')
        if not text or not isinstance(text, str) or not text.strip():
            logger.error("Missing or invalid text")
            return jsonify({'error': 'Missing or invalid text'}), 400

        # Extract sample rate
        sample_rate = message.get('sampleRate', 24000)
        valid_sample_rates = [8000, 16000, 22050, 24000]
        if sample_rate not in valid_sample_rates:
            logger.error(f"Unsupported sample rate: {sample_rate}")
            return jsonify({
                'error': 'Unsupported sample rate',
                'supportedRates': valid_sample_rates
            }), 400

        # Authenticate request
        vapi_secret = request.headers.get('X-VAPI-SECRET') or request.headers.get('Authorization', '').replace('Bearer ', '')
        if vapi_secret != VAPI_SECRET:
            logger.warning("Unauthorized request to /api/synthesize")
            return jsonify({'error': 'Unauthorized'}), 401

        logger.info(f"Synthesizing: '{text[:50]}...', sampleRate={sample_rate}Hz")

        if not client:
            logger.error("Google API client not initialized")
            return jsonify({'error': 'Google API client not initialized'}), 500

        # Use Gemini Live API with native audio
        audio_data = asyncio.run(synthesize_with_gemini_live(text, sample_rate))

        if audio_data:
            # Return raw PCM audio
            response = Response(
                audio_data,
                mimetype='application/octet-stream',
                headers={
                    'Content-Type': 'application/octet-stream',
                    'Content-Length': str(len(audio_data))
                }
            )
            logger.info(f"TTS completed: {len(audio_data)} bytes")
            return response
        else:
            logger.error("No audio data generated")
            return jsonify({'error': 'Failed to synthesize speech'}), 500

    except Exception as e:
        logger.error(f"Error synthesizing speech: {e}")
        import traceback
        logger.error(traceback.format_exc())
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


async def synthesize_with_gemini_live(text, sample_rate=24000, voice_name='Charon'):
    """
    Synthesize speech using Gemini Live API with native audio.

    Args:
        text: Text to synthesize
        sample_rate: Audio sample rate (8000, 16000, 22050, or 24000)
        voice_name: Voice name (Charon or Puck)

    Returns:
        bytes: Raw PCM audio data (16-bit signed integer, little-endian, mono)
    """
    try:
        # Model with native audio support
        model = "gemini-2.5-flash-native-audio-preview-09-2025"

        # Configuration for TTS with native audio
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
            # Gemini Live returns audio at 24kHz
            # If VAPI requests a different sample rate, we need to resample
            if sample_rate != 24000:
                logger.info(f"Resampling from 24000Hz to {sample_rate}Hz")
                audio_data = resample_audio(audio_data, 24000, sample_rate)

            logger.info(f"Generated {len(audio_data)} bytes of PCM audio at {sample_rate}Hz")
            return audio_data
        else:
            logger.error("No audio data received from Gemini Live")
            return None

    except Exception as e:
        logger.error(f"Error with Gemini Live API: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


def resample_audio(audio_data, from_rate, to_rate):
    """
    Resample PCM audio data from one sample rate to another.

    Args:
        audio_data: Raw PCM audio bytes (16-bit signed integer, little-endian)
        from_rate: Source sample rate
        to_rate: Target sample rate

    Returns:
        bytes: Resampled PCM audio data
    """
    try:
        import numpy as np
        from scipy import signal

        # Convert bytes to numpy array
        audio_array = np.frombuffer(audio_data, dtype=np.int16)

        # Calculate resampling ratio
        num_samples = int(len(audio_array) * to_rate / from_rate)

        # Resample using scipy
        resampled = signal.resample(audio_array, num_samples)

        # Convert back to int16 and bytes
        resampled_int16 = np.int16(resampled)
        return resampled_int16.tobytes()

    except Exception as e:
        logger.error(f"Error resampling audio: {e}")
        # If resampling fails, return original audio
        return audio_data


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
