"""Configuration settings for the application."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")

# Database configuration
# Supports both SQLite (development) and PostgreSQL (production)

# Use PostgreSQL if DATABASE_URL env var is set, otherwise use SQLite
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{BASE_DIR / 'app.db'}"
)

# For SQLite, ensure the database directory exists
if DATABASE_URL.startswith("sqlite"):
    os.makedirs(BASE_DIR, exist_ok=True)

# Authentication
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-min-32-chars")
ALGORITHM = "HS256"
SESSION_TIMEOUT_HOURS = int(os.getenv("SESSION_TIMEOUT_HOURS", "24"))  # Default 24 hours

# File upload settings
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Email settings (SendGrid Web API)
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "noreply@valixs.com")
SENDGRID_FROM_NAME = os.getenv("SENDGRID_FROM_NAME", "Valix")

# Azure Document Intelligence settings (for PDF invoice processing)
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT", "")
AZURE_DOCUMENT_INTELLIGENCE_API_KEY = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_API_KEY", "")
