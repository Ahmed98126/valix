"""
Minimal FastAPI server to test Jinja2 templates.
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uvicorn

app = FastAPI()

# Set up templates
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Simple root endpoint."""
    return templates.TemplateResponse("test.html", {"request": request, "message": "Hello from Jinja2!"})

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8004)