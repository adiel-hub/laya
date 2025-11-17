# 🚀 LAYA Calling Agent - Deployment Guide

Complete guide for deploying the LAYA AI Calling Agent to production.

---

## 📋 Prerequisites

- [ ] Voximplant account
- [ ] Google Gemini API key
- [ ] Server for backend (or Railway/Render account)
- [ ] Hosting for frontend (or Vercel/Netlify account)

---

## 1️⃣ Voximplant Setup

### Step 1: Create Account & Application

1. Go to [voximplant.com](https://voximplant.com) and sign up
2. Create new Application: "LAYA Calling Agent"
3. Note your **Account ID**

### Step 2: Get API Credentials

1. Navigate to **Settings → API**
2. Create new **API Key**
3. Save your:
   - Account ID
   - API Key

### Step 3: Upload VoxEngine Scenarios

#### Upload Registration Recovery Scenario:

1. Go to **Applications → LAYA Calling Agent → Scenarios**
2. Click "Create Scenario"
3. Name: `registration_recovery`
4. Copy content from `voximplant/scenarios/registration_recovery.js`
5. **Update these values:**
   ```javascript
   const GEMINI_API_KEY = "YOUR_ACTUAL_GEMINI_API_KEY";
   const WEBHOOK_URL = "https://your-production-backend.com/webhook/voximplant";
   ```
6. Save scenario
7. **Copy Scenario ID**

#### Upload Dormant Reactivation Scenario:

1. Repeat for `dormant_reactivation.js`
2. Update same configuration values
3. Save and **copy Scenario ID**

### Step 4: Create Routing Rules

1. Go to **Routing → Create Rule**
2. Create two rules:
   - `registration_recovery_rule` → Links to registration scenario
   - `dormant_reactivation_rule` → Links to dormant scenario
3. **Copy both Rule IDs**

---

## 2️⃣ Get Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the key
4. Test it works: Try a simple API call in the console

---

## 3️⃣ Backend Deployment

### Option A: Railway (Recommended - Easiest)

1. Install Railway CLI:
   ```bash
   npm install -g @railway/cli
   ```

2. Login and initialize:
   ```bash
   railway login
   cd backend
   railway init
   ```

3. Set environment variables:
   ```bash
   railway variables set VOXIMPLANT_ACCOUNT_ID="your_account_id"
   railway variables set VOXIMPLANT_API_KEY="your_api_key"
   railway variables set VOXIMPLANT_SCENARIO_ID_REGISTRATION="rule_id"
   railway variables set VOXIMPLANT_SCENARIO_ID_DORMANT="rule_id"
   railway variables set GEMINI_API_KEY="your_gemini_key"
   railway variables set DATABASE_URL="sqlite:///./database.db"
   railway variables set CORS_ORIGINS="https://your-frontend-url.vercel.app"
   ```

4. Deploy:
   ```bash
   railway up
   ```

5. Get your backend URL:
   ```bash
   railway status
   # Copy the URL (e.g., https://laya-backend-production.up.railway.app)
   ```

### Option B: Render

1. Go to [render.com](https://render.com)
2. Create new **Web Service**
3. Connect your GitHub repo
4. Set:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
5. Add environment variables (same as Railway)
6. Deploy

### Option C: DigitalOcean / AWS EC2

1. Create Ubuntu server
2. Install Python 3.10+
3. Clone repo and setup:
   ```bash
   git clone <your-repo>
   cd Laya/backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. Create `.env` file with all variables

5. Run with systemd or PM2:
   ```bash
   # Install PM2
   npm install -g pm2

   # Start backend
   pm2 start "uvicorn main:app --host 0.0.0.0 --port 8000" --name laya-backend
   pm2 save
   pm2 startup
   ```

6. Setup Nginx reverse proxy (optional but recommended)

---

## 4️⃣ Update Voximplant Webhooks

After backend is deployed:

1. Go back to **Voximplant → Scenarios**
2. Edit both scenarios
3. Update `WEBHOOK_URL` to your production backend:
   ```javascript
   const WEBHOOK_URL = "https://your-backend-url.railway.app/webhook/voximplant";
   ```
4. Save both scenarios

---

## 5️⃣ Frontend Deployment

### Option A: Vercel (Recommended)

1. Install Vercel CLI:
   ```bash
   npm install -g vercel
   ```

2. Deploy:
   ```bash
   cd frontend
   vercel
   ```

3. Set environment variables in Vercel dashboard:
   - `VITE_API_URL` = Your backend URL
   - `VITE_WS_URL` = `wss://your-backend-url/ws/ui`

4. Redeploy after setting env vars

### Option B: Netlify

1. Go to [netlify.com](https://netlify.com)
2. Connect GitHub repo
3. Set:
   - **Base directory**: `frontend`
   - **Build command**: `npm run build`
   - **Publish directory**: `frontend/dist`
4. Add environment variables
5. Deploy

### Option C: AWS S3 + CloudFront

1. Build frontend:
   ```bash
   cd frontend
   npm run build
   ```

2. Upload `dist/` folder to S3 bucket

3. Setup CloudFront distribution

4. Configure DNS

---

## 6️⃣ Update Backend CORS

After frontend is deployed, update backend CORS:

```bash
# In Railway/Render, update environment variable:
CORS_ORIGINS=https://your-frontend.vercel.app,https://your-frontend.netlify.app
```

---

## 7️⃣ Testing

### Test Backend:

1. Visit: `https://your-backend-url.com/`
   - Should return JSON with app info

2. Visit: `https://your-backend-url.com/docs`
   - Should show FastAPI Swagger UI

3. Test health endpoint:
   ```bash
   curl https://your-backend-url.com/health
   ```

### Test Frontend:

1. Visit your frontend URL
2. You should see dashboard
3. Check connection status indicator (should be green if backend is running)

### Test Full Flow:

1. Add a test lead in the UI
2. Click "התקשר" button
3. Check:
   - Call appears in active calls
   - VoxEngine logs in Voximplant
   - Backend logs
   - Call result appears after completion

---

## 8️⃣ Monitoring & Logs

### Backend Logs:

**Railway:**
```bash
railway logs
```

**Render:**
- Check logs in Render dashboard

### Voximplant Logs:

1. Go to **Voximplant → Call History**
2. Click on specific call
3. View logs and audio recording

### Frontend Monitoring:

- Check browser console for errors
- Use Vercel/Netlify dashboard for deployment logs

---

## 9️⃣ Scaling Considerations

### For 1,000 calls/month:
- ✅ Current setup is sufficient
- ✅ SQLite works fine
- ✅ Basic hosting (Railway/Vercel) is enough

### For 10,000+ calls/month:
- 🔄 Migrate to PostgreSQL
- 🔄 Upgrade to production hosting tier
- 🔄 Add caching layer (Redis)
- 🔄 Setup load balancer if needed

---

## 🔒 Security Checklist

- [ ] All API keys stored in environment variables (not in code)
- [ ] CORS configured for production domain only
- [ ] HTTPS enabled on both frontend and backend
- [ ] Voximplant webhook URL uses HTTPS
- [ ] Database backups configured (if using PostgreSQL)
- [ ] Rate limiting enabled (optional for POC)

---

## 💰 Expected Costs (1,000 calls/month)

| Service | Cost |
|---------|------|
| Voximplant | ~$110/month (includes calls + platform) |
| Gemini API | ~$160/month (audio tokens) |
| Backend Hosting (Railway) | $5-10/month |
| Frontend Hosting (Vercel) | Free |
| **TOTAL** | **~$275-280/month** |

---

## 🐛 Troubleshooting

### "Call not connecting"
- Check Voximplant scenario IDs are correct in backend `.env`
- Verify phone number is in E.164 format (+972...)
- Check Voximplant account balance

### "Webhook not received"
- Make sure backend URL is publicly accessible (not localhost)
- Check `WEBHOOK_URL` in Voximplant scenarios is correct
- Look at backend logs for incoming requests

### "WebSocket not connecting"
- Check `VITE_WS_URL` uses `wss://` (not `ws://`) for production
- Verify CORS allows WebSocket connections
- Check firewall doesn't block WebSocket

### "Database not persisting"
- For SQLite on Railway: Use volumes to persist database
- Consider upgrading to PostgreSQL for production

---

## 📞 Support

For issues with:
- **Voximplant**: Check [Voximplant Documentation](https://voximplant.com/docs/)
- **Gemini**: See [Gemini API Docs](https://ai.google.dev/gemini-api/docs/live)
- **Deployment**: Contact your hosting provider support

---

## ✅ Post-Deployment Checklist

- [ ] Backend deployed and accessible
- [ ] Frontend deployed and accessible
- [ ] Voximplant scenarios uploaded with correct webhook URLs
- [ ] All environment variables set correctly
- [ ] CORS configured for production
- [ ] Test lead added successfully
- [ ] Test call made and completed
- [ ] WebSocket real-time updates working
- [ ] Call results saved to database
- [ ] Voximplant logs showing successful calls
- [ ] Monitoring/logging setup

---

**🎉 Congratulations! Your LAYA Calling Agent is now live in production!**
