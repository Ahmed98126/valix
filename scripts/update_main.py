"""Update main.py to include new routes."""

import re

def update_main_file():
    """Update main.py to include new routes."""
    # Read the main.py file
    with open("main.py", "r") as f:
        content = f.read()
    
    # Add import for routes
    import_pattern = "from app.config import UPLOAD_DIR, MAX_UPLOAD_SIZE, SECRET_KEY"
    routes_import = "from app.routes import router as api_router"
    
    if routes_import not in content:
        content = content.replace(
            import_pattern,
            f"{import_pattern}\n{routes_import}"
        )
    
    # Add include_router line
    app_pattern = "app = FastAPI()"
    include_router = 'app.include_router(api_router)'
    
    if include_router not in content:
        content = content.replace(
            app_pattern,
            f"{app_pattern}\n{include_router}"
        )
    
    # Write the updated content back to main.py
    with open("main.py", "w") as f:
        f.write(content)
    
    print("Updated main.py to include new routes")

if __name__ == "__main__":
    update_main_file()