#!/usr/bin/env python3
"""
Gemini Live TTS Server for VAPI Custom Voice Integration

This server acts as a bridge between VAPI and Google Gemini Live API,
enabling Gemini Live native audio to be used as a custom voice provider in VAPI.
"""

from flask import Flask, request, jsonify, Response, stream_with_context
from flask_sock import Sock
import requests
import os
import json
import logging
import time
from io import BytesIO
import asyncio
import queue
import threading
from google import genai
from google.genai import types
from dotenv import load_dotenv
import struct
import numpy as np

# Load environment variables from .env file
load_dotenv()

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(level=getattr(logging, log_level))
logger = logging.getLogger(__name__)

app = Flask(__name__)
sock = Sock(app)  # Initialize Flask-Sock for WebSocket support

# Configuration from environment variables
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')  # Set your Google API key
VAPI_SECRET = os.getenv('VAPI_SECRET', 'your-secret-token')  # Secret for VAPI authentication
PORT = int(os.getenv('PORT', 8000))

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
    Synthesize speech from text using Google Gemini Live API with streaming.

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
        Streamed with chunked transfer encoding for low latency
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

        # Extract voice from URL parameter (e.g., /api/synthesize?voice=Zephyr)
        voice_name = request.args.get('voice', 'Zephyr')
        if voice_name not in ['Charon', 'Puck', 'Zephyr']:
            logger.warning(f"Invalid voice {voice_name}, using Zephyr")
            voice_name = 'Zephyr'

        # Authenticate request
        vapi_secret = request.headers.get('X-VAPI-SECRET') or request.headers.get('Authorization', '').replace('Bearer ', '')
        if vapi_secret != VAPI_SECRET:
            logger.warning("Unauthorized request to /api/synthesize")
            return jsonify({'error': 'Unauthorized'}), 401

        logger.info(f"🎙️ Streaming synthesis: '{text[:50]}...', voice={voice_name}, rate={sample_rate}Hz")

        if not client:
            logger.error("Google API client not initialized")
            return jsonify({'error': 'Google API client not initialized'}), 500

        # Create audio streaming generator
        def generate_audio():
            """Generator that streams audio chunks from Gemini Live"""
            # Performance tracking
            start_time = time.time()
            first_chunk_time = None

            # Create queue for async-to-sync bridge
            audio_queue = queue.Queue()

            # Start async streaming in background thread
            def run_async_stream():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(stream_gemini_live_audio(text, voice_name, audio_queue))
                loop.close()

            stream_thread = threading.Thread(target=run_async_stream, daemon=True)
            stream_thread.start()

            # Yield audio chunks as they arrive
            chunk_count = 0
            total_bytes = 0

            try:
                while True:
                    # Use timeout to prevent infinite blocking
                    try:
                        chunk = audio_queue.get(timeout=30)
                    except queue.Empty:
                        logger.error("⚠️ Timeout waiting for audio chunks (30s)")
                        break

                    if chunk is None:  # Stream complete
                        break

                    # Track time to first chunk
                    if first_chunk_time is None:
                        first_chunk_time = time.time()
                        time_to_first = (first_chunk_time - start_time) * 1000
                        logger.info(f"⚡ Time to first chunk: {time_to_first:.0f}ms")

                    # Resample if needed
                    if sample_rate != 24000:
                        chunk = resample_audio_chunk(chunk, 24000, sample_rate)

                    chunk_count += 1
                    total_bytes += len(chunk)
                    elapsed_ms = (time.time() - start_time) * 1000
                    logger.info(f"🔊 Chunk {chunk_count}: {len(chunk)} bytes @ {elapsed_ms:.0f}ms (total: {total_bytes} bytes)")
                    yield chunk

            except Exception as e:
                logger.error(f"❌ Error in audio generator: {e}")
                import traceback
                logger.error(traceback.format_exc())
            finally:
                stream_thread.join(timeout=5)
                total_time_ms = (time.time() - start_time) * 1000
                logger.info(f"✅ Stream complete: {chunk_count} chunks, {total_bytes} bytes, {total_time_ms:.0f}ms total")

        # Return streaming response with production headers
        response = Response(
            stream_with_context(generate_audio()),
            mimetype='application/octet-stream',
            headers={
                'Content-Type': 'application/octet-stream',
                'Transfer-Encoding': 'chunked',
                'X-Accel-Buffering': 'no',  # Disable Nginx buffering
                'Cache-Control': 'no-cache, no-store, must-revalidate'
            }
        )
        return response

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


async def stream_gemini_live_audio(text, voice_name, audio_queue):
    """
    Stream audio chunks from Gemini Live API to a queue.
    Runs in background thread and filters audio-only chunks.

    Args:
        text: Text to synthesize
        voice_name: Voice name (Charon, Puck, or Zephyr)
        audio_queue: Queue to put audio chunks into
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
            },
            "system_instruction": "read it correctly without missing or changing any words"
        }

        # Connect to Live API and send text
        async with client.aio.live.connect(model=model, config=config) as session:
            # Send text directly without wrapper for lower latency
            await session.send_client_content(
                turns=types.Content(
                    role='user',
                    parts=[types.Part(text=text)]
                )
            )

            # Stream audio chunks as they arrive
            async for response in session.receive():
                # ✅ Only process audio chunks (filter out text/thought parts)
                if response.data is not None:
                    audio_queue.put(response.data)
                    logger.info(f"Streamed {len(response.data)} bytes of audio data")
                # ❌ Ignore text/thought parts that caused previous streaming failure

        # Signal completion
        audio_queue.put(None)
        logger.info("Audio streaming completed")

    except Exception as e:
        logger.error(f"Error streaming from Gemini Live API: {e}")
        import traceback
        logger.error(traceback.format_exc())
        audio_queue.put(None)


async def synthesize_with_gemini_live(text, sample_rate=24000, voice_name='Zephyr'):
    """
    Synthesize speech using Gemini Live API with native audio.

    Args:
        text: Text to synthesize
        sample_rate: Audio sample rate (8000, 16000, 22050, or 24000)
        voice_name: Voice name (Charon, Puck, or Zephyr)

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
            },
            "system_instruction": "You are a text-to-speech system. When given text, speak it exactly as written without adding any additional commentary or thoughts. Only output audio."
        }

        # Collect audio bytes
        audio_buffer = BytesIO()

        # Connect to Live API and send text
        async with client.aio.live.connect(model=model, config=config) as session:
            # Send the text as input - prepend instruction for TTS behavior
            tts_prompt = f"Please say the following text: {text}"
            await session.send_client_content(
                turns=types.Content(
                    role='user',
                    parts=[types.Part(text=tts_prompt)]
                )
            )

            # Receive audio response
            async for response in session.receive():
                # Extract audio data directly from response
                if response.data is not None:
                    audio_buffer.write(response.data)
                    logger.info(f"Received {len(response.data)} bytes of audio data")
                else:
                    # Log if we got non-audio response
                    if hasattr(response, 'server_content') and response.server_content:
                        logger.warning(f"Received non-audio response: {response.server_content}")

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


def resample_audio_chunk(audio_chunk, from_rate, to_rate):
    """
    Fast per-chunk resampling using linear interpolation.
    Optimized for low latency streaming.

    Args:
        audio_chunk: Raw PCM audio bytes (16-bit signed integer, little-endian)
        from_rate: Source sample rate
        to_rate: Target sample rate

    Returns:
        bytes: Resampled PCM audio chunk
    """
    if from_rate == to_rate:
        return audio_chunk

    try:
        import numpy as np

        # Convert bytes to numpy array
        audio_array = np.frombuffer(audio_chunk, dtype=np.int16)

        # Calculate resampling ratio
        ratio = to_rate / from_rate
        num_samples = int(len(audio_array) * ratio)

        # Fast linear interpolation
        indices = np.linspace(0, len(audio_array) - 1, num_samples)
        resampled = np.interp(indices, np.arange(len(audio_array)), audio_array)

        # Convert back to int16 and bytes
        resampled_int16 = np.int16(resampled)
        return resampled_int16.tobytes()

    except Exception as e:
        logger.error(f"Error resampling audio chunk: {e}")
        return audio_chunk


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
        },
        {
            'id': 'Zephyr',
            'name': 'Zephyr',
            'language': 'en-US',
            'gender': 'NEUTRAL',
            'description': 'Gemini Live native voice - Zephyr'
        }
    ]

    return jsonify({'voices': voices}), 200


# ============================================================================
# CUSTOM TRANSCRIBER - WebSocket Support for VAPI
# ============================================================================

def extract_audio_channel(stereo_audio, channel_index):
    """
    Extract a single channel from stereo PCM audio.

    Args:
        stereo_audio: Raw PCM audio bytes (16-bit signed integer, stereo)
        channel_index: Channel to extract (0 = left/customer, 1 = right/assistant)

    Returns:
        bytes: Mono PCM audio data for the specified channel
    """
    try:
        # Convert stereo bytes to numpy array
        audio_array = np.frombuffer(stereo_audio, dtype=np.int16)

        # Extract the specified channel (every other sample starting at channel_index)
        mono_audio = audio_array[channel_index::2]

        return mono_audio.tobytes()

    except Exception as e:
        logger.error(f"Error extracting audio channel: {e}")
        return stereo_audio


async def transcribe_with_gemini_live(audio_data, sample_rate=16000, language='Hebrew'):
    """
    Transcribe audio using Gemini Live API.

    Args:
        audio_data: Raw PCM audio bytes (16-bit signed integer, mono)
        sample_rate: Audio sample rate (default 16000 for VAPI)
        language: Language hint for transcription

    Returns:
        str: Transcribed text, or None if transcription fails
    """
    try:
        if not client:
            logger.error("Google API client not initialized")
            return None

        # Model with native audio support
        model = "gemini-2.5-flash-native-audio-preview-09-2025"

        # Configuration for transcription
        config = {
            "response_modalities": ["TEXT"],
            "system_instruction": f"Transcribe the following {language} audio accurately. Only return the transcription, no additional text."
        }

        # Connect to Live API and send audio
        async with client.aio.live.connect(model=model, config=config) as session:
            # Send audio data as input
            await session.send_client_content(
                turns=types.Content(
                    role='user',
                    parts=[types.Part(inline_data=types.Blob(
                        mime_type=f'audio/pcm;rate={sample_rate}',
                        data=audio_data
                    ))]
                )
            )

            # Receive transcription response
            transcription = ""
            async for response in session.receive():
                # Extract text from response
                if hasattr(response, 'server_content') and response.server_content:
                    if hasattr(response.server_content, 'model_turn'):
                        for part in response.server_content.model_turn.parts:
                            if hasattr(part, 'text'):
                                transcription += part.text

            logger.info(f"Transcription: {transcription[:100]}")
            return transcription.strip()

    except Exception as e:
        logger.error(f"Error transcribing with Gemini Live: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


# ============================================================================
# WebSocket Handler for VAPI Custom Transcriber using Flask-Sock
# ============================================================================

@sock.route('/')
def handle_transcriber_websocket(ws):
    """
    Handle WebSocket connection for VAPI custom transcriber.

    This function implements the VAPI custom transcriber protocol:
    1. Receives initial start message from VAPI
    2. Streams audio data from VAPI
    3. Sends transcription results back to VAPI

    Args:
        ws: WebSocket connection object from Flask-Sock
    """
    try:
        logger.info(f"🔌 WebSocket connection established")

        # Log headers for debugging
        logger.info(f"Request headers: {dict(request.headers)}")

        # Validate authentication from request headers (optional - VAPI may not send this in WebSocket upgrade)
        vapi_secret = request.headers.get('x-vapi-secret') or request.headers.get('X-VAPI-SECRET')
        if vapi_secret and vapi_secret != VAPI_SECRET:
            logger.warning(f"❌ Invalid secret provided")
            ws.close(1008, "Unauthorized")
            return

        logger.info(f"✅ WebSocket authenticated (secret: {bool(vapi_secret)})")

        # Session state
        sample_rate = 16000
        channels = 2
        audio_buffer = bytearray()
        buffer_size_limit = 48000  # ~1.5 seconds at 16kHz (16000 * 2 bytes * 1.5)

        # Process messages from VAPI
        while True:
            try:
                message = ws.receive()
                if message is None:
                    break

                # Try parsing as JSON (start message)
                if isinstance(message, str):
                    data = json.loads(message)
                    msg_type = data.get('type')

                    if msg_type == 'start':
                        sample_rate = data.get('sampleRate', 16000)
                        channels = data.get('channels', 2)
                        encoding = data.get('encoding', 'linear16')
                        logger.info(f"🎙️ Transcription session started: {sample_rate}Hz, {channels} channels, {encoding}")

                # Binary audio data
                elif isinstance(message, bytes):
                    logger.info(f"🔊 Received audio chunk: {len(message)} bytes")

                    # Buffer audio data
                    audio_buffer.extend(message)

                    # Process buffer when it reaches a certain size
                    if len(audio_buffer) >= buffer_size_limit:
                        # Extract customer channel (channel 0) from stereo audio
                        mono_audio = extract_audio_channel(bytes(audio_buffer), channel_index=0)

                        # Transcribe the audio synchronously
                        def transcribe_sync():
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            result = loop.run_until_complete(
                                transcribe_with_gemini_live(mono_audio, sample_rate=sample_rate, language='Hebrew')
                            )
                            loop.close()
                            return result

                        transcription = transcribe_sync()

                        if transcription:
                            # Send transcription back to VAPI
                            response = {
                                'type': 'transcriber-response',
                                'transcription': transcription,
                                'channel': 'customer'
                            }
                            ws.send(json.dumps(response))
                            logger.info(f"📝 Sent transcription: {transcription[:50]}...")

                        # Clear buffer
                        audio_buffer.clear()

            except json.JSONDecodeError:
                logger.error(f"Failed to decode JSON message")
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                import traceback
                logger.error(traceback.format_exc())

        logger.info(f"🔌 WebSocket connection closed")

    except Exception as e:
        logger.error(f"❌ Error in WebSocket handler: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == '__main__':
    logger.info(f"Starting Gemini Live Server on port {PORT}")
    logger.info("Make sure to set GOOGLE_API_KEY environment variable")
    logger.info("Endpoints:")
    logger.info(f"  - HTTP (TTS):        http://0.0.0.0:{PORT}/api/synthesize")
    logger.info(f"  - WebSocket (STT):   ws://0.0.0.0:{PORT}/")
    logger.info("")
    logger.info("Note: Both HTTP and WebSocket run on the same port")

    # Run Flask server with WebSocket support
    app.run(
        host='0.0.0.0',
        port=PORT,
        debug=False,
        threaded=True
    )
