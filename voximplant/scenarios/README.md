# Voximplant VoxEngine Scenarios

This folder contains JavaScript scenarios that run in Voximplant's VoxEngine cloud.

## 📁 Scenarios

1. **`registration_recovery.js`** - Re-engages users who dropped off during registration
2. **`dormant_reactivation.js`** - Reactivates users who became inactive

## 🚀 Setup Instructions

### 1. Create Voximplant Account

1. Go to [voximplant.com](https://voximplant.com) and create an account
2. Navigate to Applications → Create Application
3. Name it "LAYA Calling Agent"

### 2. Upload Scenarios

#### For Registration Recovery:

1. In Voximplant Control Panel → Applications → LAYA Calling Agent
2. Click "Scenarios" → "Create Scenario"
3. Name: `registration_recovery`
4. Copy the content of `registration_recovery.js`
5. **Replace these values:**
   ```javascript
   const GEMINI_API_KEY = "YOUR_ACTUAL_GEMINI_API_KEY";
   const WEBHOOK_URL = "https://your-backend-url.com/webhook/voximplant";
   ```
6. Click "Save"
7. **Copy the Scenario ID** (you'll need this for backend .env)

#### For Dormant Reactivation:

1. Repeat the same steps with `dormant_reactivation.js`
2. Name: `dormant_reactivation`
3. Replace the same configuration values
4. Save and **copy the Scenario ID**

### 3. Create Routing Rules

#### Rule 1: Registration Recovery

1. Go to "Routing" → "Create Rule"
2. Name: `registration_recovery_rule`
3. Pattern: Select the scenario `registration_recovery`
4. Assign scenario to this rule
5. Save and **copy the Rule ID**

#### Rule 2: Dormant Reactivation

1. Create another rule: `dormant_reactivation_rule`
2. Assign the `dormant_reactivation` scenario
3. Save and **copy the Rule ID**

### 4. Get Credentials

1. Go to "Settings" → "API"
2. Copy your **Account ID**
3. Create an **API Key**
4. Copy both values

### 5. Update Backend Configuration

Add these to your backend `.env` file:

```env
VOXIMPLANT_ACCOUNT_ID=your_account_id
VOXIMPLANT_API_KEY=your_api_key
VOXIMPLANT_SCENARIO_ID_REGISTRATION=rule_id_for_registration
VOXIMPLANT_SCENARIO_ID_DORMANT=rule_id_for_dormant
GEMINI_API_KEY=your_gemini_api_key
```

### 6. Get Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the key
4. Add it to both:
   - VoxEngine scenarios (replace `YOUR_GEMINI_API_KEY`)
   - Backend `.env` file

---

## 🔧 How It Works

### Call Flow:

```
1. Backend triggers call → Voximplant API
2. Voximplant initiates call → User's phone
3. VoxEngine scenario starts → Answers call
4. Scenario connects to Gemini Live API
5. Audio flows: User ↔ Gemini (Hebrew conversation)
6. Gemini calls save_call_result function
7. VoxEngine sends webhook → Backend
8. Backend saves result to database
9. Call ends
```

### Hebrew Language:

Both scenarios are configured for Hebrew (`he-IL`):
```javascript
speechConfig: {
  languageCode: 'he-IL',
  voiceConfig: {
    prebuiltVoiceConfig: {
      voiceName: 'Kore'
    }
  }
}
```

### Function Calling:

Gemini is instructed to call `save_call_result` at the end of every call with:
- **disposition**: Call outcome (e.g., "COMPLETED_REGISTRATION", "REACTIVATED")
- **cx_score**: Customer satisfaction (1-10)
- **summary**: Hebrew summary of the conversation

---

## 🧪 Testing

### Test the Scenarios:

1. In Voximplant Control Panel → "Scenarios"
2. Click "Test" button next to your scenario
3. Use the built-in debugger to check logs

### Test with Real Call:

1. Make sure backend is running and accessible
2. Trigger a call from your dashboard
3. Check VoxEngine logs in Voximplant Control Panel
4. Check backend webhook logs

### Debug Tips:

- **Check VoxEngine logs**: Control Panel → Call History → Click call → Logs
- **Check webhook delivery**: Make sure `WEBHOOK_URL` is publicly accessible
- **Test Gemini API key**: Try it directly in Google AI Studio first
- **Verify audio**: Make sure `VoxEngine.sendMediaBetween(call, geminiClient)` is called

---

## 📊 Monitoring

### In Voximplant Dashboard:

- **Call History**: See all calls made
- **Scenario Logs**: Debug JavaScript execution
- **Usage Statistics**: Track costs and volume

### Expected Logs:

```
📞 Call answered
👤 Calling: Yossi Cohen (+972501234567)
🤖 Initializing Gemini Live API...
✅ Connected to Gemini Live API (Hebrew mode)
🔊 Audio bridge established: Call ↔ Gemini
🔧 Function called by Gemini:
   Name: save_call_result
   Parameters: {...}
💾 Saving call result...
📤 Webhook sent: call_result
✅ Call result saved
   Disposition: REACTIVATED
   CX Score: 8/10
👋 Hanging up call
📴 Call disconnected
```

---

## 🎙️ Voice Configuration

### Available Voices:

You can change the voice by modifying `voiceName` in the scenarios:

```javascript
voiceConfig: {
  prebuiltVoiceConfig: {
    voiceName: 'Kore'  // Change this to other available voices
  }
}
```

Gemini offers 30+ HD voices. Experiment to find the best one for your use case.

---

## 💰 Cost Monitoring

### Voximplant Costs:
- Outbound calls: ~$0.003/minute
- Data transfer: Minimal

### Gemini Costs:
- Audio input: $2.10 per million tokens (~25 tokens/second)
- Audio output: $8.50 per million tokens
- **Estimated**: ~$0.16 per 10-minute call

### Total per 3-minute call: ~$0.05-0.07

---

## 🐛 Troubleshooting

### "Gemini WebSocket closed immediately"
- Check API key is valid
- Verify you have Gemini API quota remaining
- Check internet connectivity from Voximplant

### "Webhook not received by backend"
- Make sure backend URL is publicly accessible (use ngrok for local testing)
- Check CORS and firewall settings
- Verify URL includes `/webhook/voximplant`

### "No audio / User can't hear agent"
- Verify `VoxEngine.sendMediaBetween(call, geminiClient)` is called
- Check that `responseModalities: ["AUDIO"]` is set
- Test with a simple TTS first: `call.say("שלום", {language: VoiceList.Microsoft.he_IL_Asaf})`

### "Function not being called"
- Check that system prompt instructs Gemini to call the function
- Verify tools are properly defined in connectConfig
- Test function schema in Google AI Studio first

---

## 📚 Resources

- [Voximplant Docs](https://voximplant.com/docs/)
- [VoxEngine API Reference](https://voximplant.com/docs/references/voxengine)
- [Gemini Live API Guide](https://voximplant.com/docs/voice-ai/google/gemini)
- [Google Gemini Docs](https://ai.google.dev/gemini-api/docs/live)

---

**Need help?** Check the main project README or contact the development team.
