# Troubleshooting Guide

This document provides solutions to common issues encountered when running the Invoice Validator application.

## Template Rendering Issues

### TypeError: cannot use 'tuple' as a dict key (unhashable type: 'dict')

This error occurs when there's a version mismatch between FastAPI, Starlette, and Jinja2. The error typically appears when trying to render HTML templates.

**Solution:**

Use these specific versions in your virtual environment:

```bash
pip install fastapi==0.95.1 starlette==0.26.1 jinja2==3.0.3 pydantic<2.0.0
```

These versions are known to work well together. The issue is caused by incompatibilities between newer versions of these libraries.

## Database Issues

### SQLite Database Not Found

If you see an error about the database file not being found:

**Solution:**

Initialize the database by running:

```bash
python -m app.db
```

This creates the SQLite database file with all required tables.

### Database Migration Errors

If you encounter errors related to database schema:

**Solution:**

1. Delete the existing database file:
   ```bash
   rm app.db
   ```

2. Reinitialize the database:
   ```bash
   python -m app.db
   ```

## Azure Document Intelligence Issues

### Connection Errors

If you're having trouble connecting to Azure Document Intelligence:

**Solution:**

1. Verify your credentials in the `.env` file:
   ```
   AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=your_endpoint
   AZURE_DOCUMENT_INTELLIGENCE_API_KEY=your_api_key
   ```

2. Test the connection using:
   ```bash
   python test_azure_connection.py
   ```

3. Ensure you're using the correct API version and endpoint format.

## Server Issues

### Port Already in Use

If you see an error like: `[Errno 10048] only one usage of each socket address (protocol/network address/port) is normally permitted`

**Solution:**

1. Find and stop the process using the port:
   ```bash
   # Windows
   netstat -ano | findstr :8000
   taskkill /PID <PID> /F

   # Linux/Mac
   lsof -i :8000
   kill -9 <PID>
   ```

2. Or use a different port:
   ```bash
   uvicorn main:app --reload --port 8001
   ```

### Server Starts But UI Pages Return 500 Errors

If the API endpoints (like `/docs`) work but UI pages return 500 errors:

**Solution:**

This is likely a template rendering issue. Follow the solution for "TypeError: cannot use 'tuple' as a dict key" above.

## PDF Processing Issues

### OCR Extraction Fails

If PDF extraction is failing:

**Solution:**

1. Verify your Azure Document Intelligence credentials
2. Check that the PDF is readable and not password-protected
3. Use the test scripts in the `scripts` directory to debug:
   ```bash
   python scripts/test_pdf_extraction.py path/to/your/file.pdf
   ```

## Authentication Issues

### Cannot Log In

If you're having trouble logging in:

**Solution:**

1. Verify that you've created a user account
2. Check if email verification is required
3. Reset your password using the "Forgot Password" link
4. If you're an admin, you can reset a user's password in the database directly

## Installation Issues

### Package Installation Fails

If you encounter errors when installing dependencies:

**Solution:**

1. Update pip:
   ```bash
   python -m pip install --upgrade pip
   ```

2. Install packages one by one to identify problematic dependencies
3. If on Windows, some packages might require Microsoft Visual C++ Build Tools

## Need Further Help?

If you continue to experience issues:

1. Check the application logs for more detailed error messages
2. Search for the specific error message online
3. Create an issue in the project repository with details about the problem