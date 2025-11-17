# LAYA Calling Agent - Frontend

React dashboard for managing AI calling campaigns.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Create environment file
cp .env.example .env
# Edit .env if needed (default points to localhost:8000)

# Run development server
npm run dev
```

The app will be available at `http://localhost:5173`

## 📁 Project Structure

```
frontend/src/
├── components/
│   ├── layout/         # Navbar, Layout
│   ├── leads/          # Lead components
│   ├── calls/          # Call components
│   └── analytics/      # Analytics components
├── pages/              # Main pages
├── services/           # API clients
├── hooks/              # Custom React hooks
└── App.jsx             # Main app component
```

## 🎨 Features

- ✅ **Lead Management**: Add, edit, delete leads
- ✅ **One-Click Calling**: Trigger calls with a button click
- ✅ **Real-time Updates**: WebSocket connection for live call status
- ✅ **Dashboard**: See analytics and active calls
- ✅ **Responsive Design**: Works on desktop and mobile

## 🔧 Development

```bash
# Run dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## 📡 API Integration

The frontend connects to the Python backend at `http://localhost:8000` by default.

### API Endpoints Used:
- `GET /api/leads` - Get all leads
- `POST /api/leads` - Create lead
- `POST /api/calls/trigger` - Trigger call
- `GET /api/analytics/summary` - Get analytics
- `WS /ws/ui` - WebSocket for real-time updates

## 🎨 Styling

- **TailwindCSS** for utility-first styling
- **Custom components** with consistent design
- **RTL Support** for Hebrew interface

## 📦 Build & Deploy

```bash
# Build for production
npm run build

# The dist/ folder can be deployed to:
# - Vercel (recommended)
# - Netlify
# - AWS S3 + CloudFront
# - Any static hosting service
```

### Deploy to Vercel:

```bash
npm install -g vercel
vercel
```

## 🐛 Troubleshooting

### Backend not connecting
- Make sure backend is running on port 8000
- Check `.env` file has correct `VITE_API_URL`
- Check CORS is configured in backend

### WebSocket not connecting
- Verify `VITE_WS_URL` in `.env`
- Check browser console for errors
- Make sure backend WebSocket endpoint is running

---

**Built with React + Vite + TailwindCSS** 🚀
