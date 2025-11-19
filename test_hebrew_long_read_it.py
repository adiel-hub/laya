#!/usr/bin/env python3
"""
Test script for long Hebrew text with "read it" system instruction
Testing Hebrew TTS performance and quality
"""
import requests
import time
import wave
import json

# Long Hebrew text for testing (about 58 words)
HEBREW_TEXT = """
שלום! אני נטלי, העוזרת הדיגיטלית שלך המבוססת על בינה מלאכותית.
אני כאן כדי לעזור לך עם מגוון רחב של משימות ושאלות.
אני יכולה לספק מידע, לענות על שאלות, לסייע בכתיבה, ולעזור בפתרון בעיות.
אני משתמשת בטכנולוגיה מתקדמת של סינתזת דיבור כדי להישמע טבעית ונעימה.
אני מדברת עברית בצורה שוטפת וברורה, ואני מסוגלת להבין ולהגיב למגוון רחב של נושאים.
"""

def test_long_hebrew_with_read_it():
    """Test TTS with long Hebrew text using 'read it' instruction"""

    url = "http://localhost:8000/api/synthesize"

    # Prepare request
    payload = {
        "message": {
            "type": "voice-request",
            "text": HEBREW_TEXT.strip(),
            "sampleRate": 24000
        }
    }

    headers = {
        "Content-Type": "application/json",
        "X-VAPI-SECRET": "laya-tts-secret-2025"
    }

    print("=" * 70)
    print("LONG HEBREW TEXT - TTS TEST WITH 'READ IT' INSTRUCTION")
    print("=" * 70)
    print(f"\nTest Text ({len(HEBREW_TEXT.split())} words):")
    print(f'"{HEBREW_TEXT.strip()[:150]}..."')
    print("\nSending request...")

    # Performance tracking
    start_time = time.time()
    first_chunk_time = None
    chunk_count = 0
    total_bytes = 0
    chunk_times = []

    # Make request with streaming
    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            stream=True,
            timeout=60
        )

        if response.status_code != 200:
            print(f"\n❌ Error: HTTP {response.status_code}")
            print(response.text)
            return

        print(f"✅ Connected! Status: {response.status_code}")
        print(f"📦 Headers: Transfer-Encoding={response.headers.get('Transfer-Encoding', 'N/A')}")
        print("\n" + "-" * 70)
        print("STREAMING CHUNKS:")
        print("-" * 70)

        # Collect audio data
        audio_data = bytearray()

        # Read chunks
        for chunk in response.iter_content(chunk_size=None):
            if chunk:
                current_time = time.time()
                elapsed_ms = (current_time - start_time) * 1000

                # Track first chunk
                if first_chunk_time is None:
                    first_chunk_time = current_time
                    time_to_first = (first_chunk_time - start_time) * 1000
                    print(f"⚡ FIRST CHUNK RECEIVED: {time_to_first:.0f}ms")
                    print("-" * 70)

                chunk_count += 1
                chunk_size = len(chunk)
                total_bytes += chunk_size
                chunk_times.append(elapsed_ms)

                print(f"🔊 Chunk #{chunk_count:3d}: {chunk_size:6d} bytes @ {elapsed_ms:7.0f}ms (total: {total_bytes:8d} bytes)")
                audio_data.extend(chunk)

        end_time = time.time()
        total_time_ms = (end_time - start_time) * 1000

        # Calculate statistics
        print("\n" + "=" * 70)
        print("PERFORMANCE SUMMARY:")
        print("=" * 70)
        print(f"⚡ Time to first chunk:  {(first_chunk_time - start_time) * 1000:.0f} ms")
        print(f"📊 Total chunks:         {chunk_count}")
        print(f"📦 Total bytes:          {total_bytes:,} bytes ({total_bytes / 1024:.1f} KB)")
        print(f"⏱️  Total time:           {total_time_ms:.0f} ms ({total_time_ms / 1000:.2f} seconds)")
        print(f"📏 Average chunk size:   {total_bytes / chunk_count if chunk_count > 0 else 0:.0f} bytes")

        if chunk_count > 1:
            avg_interval = (chunk_times[-1] - chunk_times[0]) / (chunk_count - 1)
            print(f"⏲️  Average chunk interval: {avg_interval:.0f} ms")

        # Audio duration
        sample_rate = 24000
        duration_seconds = total_bytes / (sample_rate * 2)  # 16-bit = 2 bytes per sample
        print(f"🎵 Audio duration:       {duration_seconds:.2f} seconds")
        print(f"📈 Real-time factor:     {total_time_ms / 1000 / duration_seconds:.2f}x")

        # Save as WAV
        output_file = "test_hebrew_long_read_it.wav"
        with wave.open(output_file, 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            wav.writeframes(bytes(audio_data))

        print(f"\n💾 Saved to: {output_file}")
        print("=" * 70)
        print("\n🎧 Play this file to hear the long Hebrew text with 'read it' instruction!")

    except requests.exceptions.Timeout:
        print("\n❌ Request timed out (60s)")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_long_hebrew_with_read_it()
