"""
Application configuration settings
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application settings loaded from environment variables"""

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./database.db")

    # Voximplant
    VOXIMPLANT_ACCOUNT_ID: str = os.getenv("VOXIMPLANT_ACCOUNT_ID", "")
    VOXIMPLANT_API_KEY: str = os.getenv("VOXIMPLANT_API_KEY", "")
    VOXIMPLANT_SCENARIO_ID_REGISTRATION: str = os.getenv("VOXIMPLANT_SCENARIO_ID_REGISTRATION", "")
    VOXIMPLANT_SCENARIO_ID_DORMANT: str = os.getenv("VOXIMPLANT_SCENARIO_ID_DORMANT", "")

    # Gemini (for reference, actual key used in VoxEngine)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # Backend
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")

    # CORS
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

    # Application
    APP_NAME: str = "LAYA Calling Agent"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"


# Create settings instance
settings = Settings()
