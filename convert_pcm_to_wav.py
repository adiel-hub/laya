#!/usr/bin/env python3
"""
Convert PCM audio files to WAV format
"""
import wave
import sys

def pcm_to_wav(pcm_file, wav_file, sample_rate=24000, channels=1, sample_width=2):
    """
    Convert raw PCM audio to WAV format

    Args:
        pcm_file: Input PCM file path
        wav_file: Output WAV file path
        sample_rate: Sample rate in Hz (default: 24000)
        channels: Number of audio channels (default: 1 for mono)
        sample_width: Sample width in bytes (default: 2 for 16-bit)
    """
    # Read PCM data
    with open(pcm_file, 'rb') as f:
        pcm_data = f.read()

    # Write WAV file
    with wave.open(wav_file, 'wb') as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(sample_width)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm_data)

    print(f"Converted {pcm_file} to {wav_file}")
    print(f"  Sample rate: {sample_rate}Hz")
    print(f"  Channels: {channels}")
    print(f"  Duration: {len(pcm_data) / (sample_rate * channels * sample_width):.2f} seconds")

if __name__ == '__main__':
    # Convert test files
    pcm_to_wav('test_hebrew_zephyr.pcm', 'test_hebrew_zephyr.wav', sample_rate=24000)
    pcm_to_wav('test_english_zephyr.pcm', 'test_english_zephyr.wav', sample_rate=24000)
