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

# Ensure SQLAlchemy uses psycopg2 (not psycopg3) for PostgreSQL connections
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

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

# Base URL for building absolute links in emails (password reset, email verification).
# Set this to the public-facing URL of the app, e.g. https://valixs.com
# Without this, links are built from request.base_url which is unreliable behind Azure's proxy.
BASE_URL = os.getenv("BASE_URL", "").rstrip("/")

# Email settings (Resend)
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")
RESEND_FROM_NAME = os.getenv("RESEND_FROM_NAME", "Valix")

# Azure Document Intelligence settings (for PDF invoice processing)
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT", "")
AZURE_DOCUMENT_INTELLIGENCE_API_KEY = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_API_KEY", "")
