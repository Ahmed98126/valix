# Setting Up the Local Development Server

It appears there's an issue with the Python installation on this system. Here are steps to resolve it:

## Option 1: Install Python from the Microsoft Store

1. Open the Microsoft Store
2. Search for "Python"
3. Install the latest version (3.11 or newer)
4. After installation, open a new PowerShell window and try:
   ```
   python --version
   ```

## Option 2: Install Python from the Official Website

1. Go to [python.org](https://www.python.org/downloads/)
2. Download the latest Python installer for Windows
3. Run the installer
   - Make sure to check "Add Python to PATH"
4. After installation, open a new PowerShell window and try:
   ```
   python --version
   ```

## Setting Up the Project

Once Python is installed:

1. Create a new virtual environment:
   ```
   python -m venv venv
   ```

2. Activate the virtual environment:
   ```
   .\venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Initialize the database (if not already done):
   ```
   python -m app.db
   ```

5. Run the server:
   ```
   uvicorn main:app --reload
   ```

6. Access the application at:
   - Web UI: `http://localhost:8000/`
   - API Docs: `http://localhost:8000/docs`

## Testing PDFs

Once the server is running:

1. Log in to the application
2. Navigate to the Upload page
3. Upload the PDFs from the `test_pdfs` directory
4. Check the extraction results on the Invoices page

## Alternative: Docker Setup

If you're having persistent issues with Python, consider using Docker:

1. Install Docker Desktop
2. Create a `Dockerfile` in the project root:
   ```dockerfile
   FROM python:3.11-slim
   
   WORKDIR /app
   
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   COPY . .
   
   CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

3. Build and run the Docker container:
   ```
   docker build -t invoice-validator .
   docker run -p 8000:8000 invoice-validator
   ```

4. Access the application at `http://localhost:8000/`