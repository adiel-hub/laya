# 🎯 LAYA AI Calling Agent

Hebrew-speaking AI voice agent powered by Voximplant & Google Gemini for re-engaging dropped registration users and reactivating dormant customers.

## 📋 Project Overview

This system enables LAYA (digital wallet company) to automatically call users who:
1. **Dropped off during registration** - Follow up and help complete signup
2. **Became inactive** - Re-engage dormant wallet users

### Key Features
- ✅ **Native Hebrew support** via Google Gemini
- ✅ **Real-time voice conversations** via Voximplant + Gemini Live API
- ✅ **Automatic CX scoring & disposition tracking**
- ✅ **React dashboard** for lead management and analytics
- ✅ **SQLite database** for simple data management
- ✅ **WebSocket real-time updates** for live call monitoring

---

## 🏗️ Architecture

```
React Dashboard ←→ Python Backend (FastAPI + SQLite) ←→ Voximplant ←→ Gemini Live API
```

**The magic:** Voximplant handles all the complexity:
- Phone call infrastructure
- Hebrew STT (Speech-to-Text)
- Gemini AI integration
- Hebrew TTS (Text-to-Speech)
- Function calling for CX scoring

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Voximplant account
- Google Gemini API key

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your credentials

# Run the server
uvicorn main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### Voximplant Setup

1. Create account at [voximplant.com](https://voximplant.com)
2. Create two scenarios (see `voximplant/scenarios/`)
3. Get scenario IDs and add to `.env`
4. Configure webhooks to point to your backend URL

---

## 📁 Project Structure

```
laya-calling-agent/
├── backend/                  # Python FastAPI backend
│   ├── database/            # SQLAlchemy models & DB setup
│   ├── services/            # Business logic
│   ├── api/                 # REST API endpoints
│   ├── webhooks/            # Voximplant webhook handlers
│   ├── schemas/             # Pydantic models
│   ├── config/              # Configuration
│   └── main.py              # FastAPI app
├── frontend/                 # React dashboard
│   └── src/
│       ├── components/      # React components
│       ├── pages/           # Page components
│       └── services/        # API clients
└── voximplant/
    └── scenarios/           # VoxEngine JavaScript files
```

---

## 🔧 Configuration

### Environment Variables

**Backend (.env):**
```env
VOXIMPLANT_ACCOUNT_ID=your_account_id
VOXIMPLANT_API_KEY=your_api_key
VOXIMPLANT_SCENARIO_ID_REGISTRATION=scenario_id
VOXIMPLANT_SCENARIO_ID_DORMANT=scenario_id
GEMINI_API_KEY=your_gemini_key
DATABASE_URL=sqlite:///./database.db
BACKEND_URL=http://localhost:8000
CORS_ORIGINS=http://localhost:5173
```

---

## 📊 Database Schema

### Tables:
1. **leads** - Customer contact information
2. **calls** - Call session records
3. **call_results** - Call outcomes with CX scores

---

## 🎤 Voice Agent System

### How It Works:

1. User triggers call from dashboard
2. Backend creates call record and triggers Voximplant
3. VoxEngine scenario answers call and connects to Gemini
4. Gemini conducts Hebrew conversation:
   - Automatic STT (speech-to-text)
   - AI reasoning and response generation
   - Automatic TTS (text-to-speech)
5. At end of call, Gemini calls function with disposition + CX score
6. VoxEngine sends webhook to backend
7. Backend saves result to database
8. Dashboard shows result in real-time

### Conversation Prompts:

Two specialized Hebrew prompts:
- **Registration Recovery**: Helps users complete signup
- **Dormant Reactivation**: Re-engages inactive users

---

## 📈 Analytics

Dashboard provides:
- Total calls made
- Success rate by campaign type
- Average CX scores
- Disposition breakdown
- Real-time call monitoring

---

## 💰 Cost Estimate

**For 1,000 calls/month (3 min average):**
- Voximplant: ~$9
- Gemini Audio API: ~$159
- Hosting: ~$10
- **Total: ~$178/month**

---

## 🛠️ Development

### Run Backend Tests
```bash
cd backend
pytest
```

### Run Frontend in Dev Mode
```bash
cd frontend
npm run dev
```

### Build for Production
```bash
# Backend
cd backend
# Deploy to Railway, Render, or DigitalOcean

# Frontend
cd frontend
npm run build
# Deploy to Vercel or Netlify
```

---

## 📞 Webhook Endpoints

Backend exposes:
- `POST /webhook/voximplant` - Receives call events from VoxEngine
- `POST /api/calls/trigger` - Triggers new outbound call
- `WS /ws/ui` - WebSocket for real-time UI updates

---

## 🐛 Troubleshooting

### Common Issues:

**"Voximplant credentials not configured"**
- Make sure `.env` file exists with correct credentials

**"Database not initialized"**
- Run the backend once to auto-create SQLite database

**"Call not connecting"**
- Check Voximplant scenario IDs are correct
- Verify phone numbers are in E.164 format (+972...)
- Check Gemini API key is valid

**"Hebrew not working"**
- Verify `languageCode: 'he-IL'` in VoxEngine scenario
- Check system prompt is in Hebrew

---

## 📚 Documentation

- [Voximplant Docs](https://voximplant.com/docs/)
- [Gemini Live API](https://ai.google.dev/gemini-api/docs/live)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [React Docs](https://react.dev/)

---

## 🤝 Contributing

This is an internal LAYA project. For questions or issues, contact the development team.

---

## 📄 License

Proprietary - LAYA Project

---

## 🎙️ VAPI Integration with Gemini Live

### Custom Voice Provider Setup

For using Google Gemini Live native audio with VAPI, we've created a custom TTS webhook server:

**Files:**
- `backend/gemini_tts_server.py` - Flask webhook server for TTS
- `backend/GEMINI_TTS_SETUP.md` - Complete setup guide
- `backend/Dockerfile.tts` - Docker deployment configuration
- `scripts/setup_vapi_assistant.py` - VAPI assistant configuration script

**Quick Setup:**
```bash
# 1. Deploy TTS server (see GEMINI_TTS_SETUP.md for details)
cd backend
pip install -r requirements-tts.txt
python gemini_tts_server.py

# 2. Configure VAPI assistant
cd ../scripts
python3 setup_vapi_assistant.py
```

**Features:**
- ✅ Google Gemini 2.5 Flash model
- ✅ Custom voice provider integration
- ✅ Hebrew transcription support
- ✅ Production-ready deployment options (Railway, GCP, Render)

See [backend/GEMINI_TTS_SETUP.md](backend/GEMINI_TTS_SETUP.md) for complete deployment instructions.

---

## 🎯 Next Steps

1. ✅ Complete backend implementation
2. ✅ Build React dashboard
3. ✅ VAPI integration with custom TTS server
4. ⏳ Deploy TTS webhook to production
5. ⏳ Test Hebrew conversations
6. ⏳ Refine AI prompts
7. ⏳ Deploy to production
8. ⏳ Run pilot with 100 calls

---

**Built with ❤️ for LAYA by Claude Code**
