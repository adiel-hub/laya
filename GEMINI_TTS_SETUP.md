# Gemini Live TTS Server Setup Guide

This guide explains how to deploy and use the Gemini Live TTS server as a custom voice provider for VAPI.

## Overview

The Gemini TTS server acts as a bridge between VAPI and Google's Text-to-Speech services, allowing you to use Google's high-quality voices with your VAPI assistant.

## Prerequisites

1. Google Cloud account with billing enabled
2. Google Cloud API key or service account
3. Server to host the TTS webhook (e.g., Railway, Render, Google Cloud Run, AWS)

## Setup Steps

### 1. Google Cloud Setup

#### Option A: Using API Key (Simpler)
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Save it securely

#### Option B: Using Service Account (Recommended for Production)
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing one
3. Enable the Text-to-Speech API
4. Create a service account:
   - Go to IAM & Admin > Service Accounts
   - Create service account with "Cloud Text-to-Speech User" role
   - Create and download JSON key
5. Set environment variable: `GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json`

### 2. Install Dependencies

```bash
cd backend
pip install -r requirements-tts.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the `backend` directory:

```bash
GOOGLE_API_KEY=your_google_api_key_here
VAPI_SECRET=your_secure_secret_token
PORT=8080
```

### 4. Test Locally

```bash
cd backend
python gemini_tts_server.py
```

Test the server:
```bash
# Health check
curl http://localhost:8080/health

# Test synthesis
curl -X POST http://localhost:8080/synthesize \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_secure_secret_token" \
  -d '{
    "text": "Hello, this is a test of Gemini TTS!",
    "voiceId": "Zephyr"
  }' \
  --output test.wav
```

### 5. Deploy to Production

#### Option A: Deploy to Railway

1. Install Railway CLI:
   ```bash
   npm install -g @railway/cli
   ```

2. Login and deploy:
   ```bash
   railway login
   cd backend
   railway init
   railway up
   ```

3. Set environment variables in Railway dashboard:
   - `GOOGLE_API_KEY`
   - `VAPI_SECRET`

4. Get your deployment URL from Railway

#### Option B: Deploy to Google Cloud Run

1. Install Google Cloud CLI

2. Deploy:
   ```bash
   gcloud run deploy gemini-tts-server \
     --source backend \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars GOOGLE_API_KEY=your_key,VAPI_SECRET=your_secret
   ```

3. Note the service URL provided

#### Option C: Deploy to Render

1. Create account on [Render](https://render.com)
2. Create new Web Service
3. Connect your GitHub repository
4. Configure:
   - Build Command: `pip install -r requirements-tts.txt`
   - Start Command: `gunicorn -w 4 -b 0.0.0.0:$PORT gemini_tts_server:app`
5. Set environment variables in Render dashboard
6. Deploy

### 6. Update VAPI Assistant Configuration

Once deployed, update the `setup_vapi_assistant.py` script:

```python
"voice": {
    "provider": "custom-voice",
    "server": {
        "url": "https://your-deployed-server.com/synthesize",
        "secret": "your_secure_secret_token",
        "timeoutSeconds": 30
    }
}
```

Run the script to create/update your assistant:
```bash
python3 scripts/setup_vapi_assistant.py
```

## Available Voices

Currently configured voices:
- **Charon**: Male voice from Gemini Live
- **Puck**: Neutral voice from Gemini Live
- **Zephyr**: Neutral voice from Gemini Live (default)

You can extend this by modifying the `gemini_tts_server.py` file.

## Troubleshooting

### Issue: "Unauthorized" error
- Check that VAPI_SECRET matches in both server and VAPI configuration
- Verify Authorization header is being sent correctly

### Issue: "Failed to synthesize speech"
- Verify GOOGLE_API_KEY is set correctly
- Check Google Cloud billing is enabled
- Review server logs for detailed error messages

### Issue: Slow response times
- Consider deploying server closer to your users
- Use caching for frequently synthesized phrases
- Increase server resources (CPU/RAM)

### Issue: Audio quality problems
- Adjust sample rate in the request
- Try different voice IDs
- Check encoding format compatibility with VAPI

## Monitoring

View logs:
```bash
# Railway
railway logs

# Google Cloud Run
gcloud run logs read gemini-tts-server --limit 50

# Render
Check logs in Render dashboard
```

## Security Considerations

1. **Never commit API keys** to version control
2. Use **strong, unique secrets** for VAPI_SECRET
3. Consider **rate limiting** to prevent abuse
4. Use **HTTPS** only for production
5. Implement **request validation** and sanitization
6. Monitor **usage and costs** in Google Cloud Console

## Cost Optimization

- Google Text-to-Speech pricing: ~$4 per 1 million characters
- Use caching for repeated phrases
- Consider implementing a CDN for popular audio clips
- Monitor and set billing alerts in Google Cloud

## Next Steps

1. Test the assistant with a phone call
2. Fine-tune voice parameters (speed, pitch, etc.)
3. Add more voices from Google Cloud TTS
4. Implement caching layer for better performance
5. Set up monitoring and alerts

## Support

For issues with:
- Google TTS API: [Google Cloud Support](https://cloud.google.com/support)
- VAPI integration: [VAPI Documentation](https://docs.vapi.ai)
- This server: Check server logs and GitHub issues
