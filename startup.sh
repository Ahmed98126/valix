#!/bin/bash
# Azure App Service startup script for Valix

# Initialize database if needed
python -c "from app.db import init_db; init_db()" || true

# Start Gunicorn with Uvicorn workers (required for FastAPI/ASGI)
gunicorn main:app --bind 0.0.0.0:8000 --workers 2 --worker-class uvicorn.workers.UvicornWorker --timeout 120 --access-logfile - --error-logfile -

