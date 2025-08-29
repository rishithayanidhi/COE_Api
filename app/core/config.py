# app/core/config.py
import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

# Database configuration
DB_CONFIG = {
    "DB_HOST": os.getenv("DB_HOST", "localhost"),
    "DB_PORT": int(os.getenv("DB_PORT", 5432)),
    "DB_NAME": os.getenv("DB_NAME", "resource_hub"),
    "DB_USER": os.getenv("DB_USER", "postgres"),
    "DB_PASSWORD": os.getenv("DB_PASSWORD", "postgres"),
}

# FastAPI server config
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", 8000))
DEBUG = os.getenv("DEBUG", "True") == "True"

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
