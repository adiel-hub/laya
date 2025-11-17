"""
LAYA AI Calling Agent - FastAPI Backend
Main application file
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from database.db import init_db
from config.settings import settings

# Import routers
from api import leads, calls, analytics, websocket
from webhooks import voximplant


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events - startup and shutdown
    """
    # Startup
    print("🚀 Starting LAYA AI Calling Agent Backend...")
    print(f"📦 App: {settings.APP_NAME} v{settings.APP_VERSION}")

    # Initialize database
    init_db()

    # Inject WebSocket manager into webhook handler
    ws_manager = websocket.get_manager()
    voximplant.set_websocket_manager(ws_manager)

    print("✅ Backend ready!")
    print(f"🌐 Backend URL: {settings.BACKEND_URL}")
    print(f"🔗 CORS Origins: {settings.CORS_ORIGINS}")

    yield

    # Shutdown
    print("👋 Shutting down LAYA AI Calling Agent Backend...")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered calling agent for LAYA digital wallet - re-engaging dropped registrations and reactivating dormant users",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(leads.router)
app.include_router(calls.router)
app.include_router(analytics.router)
app.include_router(voximplant.router)
app.include_router(websocket.router)


@app.get("/")
def root():
    """
    Root endpoint - API information
    """
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "leads": "/api/leads",
            "calls": "/api/calls",
            "analytics": "/api/analytics",
            "webhook": "/webhook/voximplant",
            "websocket": "/ws/ui"
        }
    }


@app.get("/health")
def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
