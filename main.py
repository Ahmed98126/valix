"""FastAPI application entry point."""

from fastapi import FastAPI, HTTPException, Depends, Query, Request, Form, UploadFile, File, BackgroundTasks, Body
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse as FastAPIJSONResponse
from fastapi.encoders import jsonable_encoder

# Custom JSONResponse class that ensures UTF-8 encoding
class JSONResponse(FastAPIJSONResponse):
    media_type = "application/json; charset=utf-8"
    
    def render(self, content):
        return super().render(jsonable_encoder(content))
from fastapi.staticfiles import StaticFiles
from jinja2 import TemplateNotFound
from starlette.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional

from app.db import get_session
from app.models import Invoice, InvoiceValidation, Unit, Lease, User, Tenant, UnitTimeline
from app.upload_status import UploadStatus
from app.password_reset import PasswordResetToken
from app.email_service import send_password_reset_email
from app.schemas import (
    InvoiceResponse, 
    InvoiceValidationResponse, 
    InvoiceWithValidationResponse,
    ValidationRequest
)
from app.validation import validate_invoice, generate_unit_timeline
from app.auth import (
    get_current_user, authenticate_user, create_user, 
    get_current_tenant, get_tenant_id, create_tenant
)
from app.tenant_helpers import filter_by_tenant, get_user_tenant
from app.column_mapping import get_column_mapping, map_columns
from app.error_handling import get_user_friendly_error, create_error_response
from app.config import UPLOAD_DIR, MAX_UPLOAD_SIZE, SECRET_KEY, BASE_URL
from app.routes import router as api_router

# PDF processing imports (optional - only needed if Azure is configured)
try:
    from app.pdf_processor import PDFProcessor
    from app.pdf_normalizer import PDFNormalizer
    PDF_PROCESSING_AVAILABLE = True
except ImportError:
    PDF_PROCESSING_AVAILABLE = False
    logger.warning("PDF processing not available - install azure-ai-documentintelligence to enable PDF uploads")
import pandas as pd
import uuid
from pathlib import Path
from datetime import datetime, date
from decimal import Decimal
import traceback
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Valix - Invoice Validation",
    description="AI-assisted invoice validation for commercial property portfolios",
    version="0.3.0",
)
app.include_router(api_router)

# Add session middleware for authentication
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Templates for HTML responses
templates = Jinja2Templates(directory="templates")

# Add custom Jinja2 filters for date formatting
def format_date_dd_mm_yyyy(date_obj):
    """Format date as DD/MM/YYYY."""
    if date_obj is None:
        return 'N/A'
    if isinstance(date_obj, date):
        return date_obj.strftime('%d/%m/%Y')
    if isinstance(date_obj, datetime):
        return date_obj.strftime('%d/%m/%Y')
    return str(date_obj)

def format_datetime_dd_mm_yyyy(datetime_obj):
    """Format datetime as DD/MM/YYYY HH:MM:SS."""
    if datetime_obj is None:
        return 'N/A'
    if isinstance(datetime_obj, datetime):
        return datetime_obj.strftime('%d/%m/%Y %H:%M:%S')
    return str(datetime_obj)

# Register filters with Jinja2
templates.env.filters['ddmmyyyy'] = format_date_dd_mm_yyyy
templates.env.filters['ddmmyyyy_time'] = format_datetime_dd_mm_yyyy

# Static files - ensure directories exist
static_dir = Path("static")
static_dir.mkdir(exist_ok=True)
(static_dir / "css").mkdir(exist_ok=True)
(static_dir / "js").mkdir(exist_ok=True)

try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception as e:
    print(f"Warning: Could not mount static files: {e}")


# Favicon route (prevents 404 errors)
@app.get("/favicon.ico")
async def favicon():
    """Return empty favicon to prevent 404 errors."""
    from fastapi.responses import Response
    return Response(content="", media_type="image/x-icon")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on application startup."""
    try:
        from app.db import init_db
        init_db()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.warning(f"⚠️ Warning: Could not initialize database: {e}")
        logger.warning("This is OK if tables already exist or database is not yet configured")


# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with appropriate responses."""
    # Handle authentication errors - redirect to login for HTML requests
    if exc.status_code == 401:  # Unauthorized
        if "application/json" not in request.headers.get("accept", ""):
            # Check if it's a session expiry
            error_msg = "Please sign in to access this page"
            if "expired" in exc.detail.lower():
                error_msg = "Your session has expired. Please sign in again."
            # For HTML requests, redirect to login with return URL
            redirect_url = f"/login?redirect={request.url.path}&error={error_msg.replace(' ', '%20')}"
            return RedirectResponse(url=redirect_url, status_code=303)
        # For API requests, return JSON
        return JSONResponse(
            status_code=401,
            content={"detail": exc.detail or "Not authenticated", "error_type": "unauthorized"}
        )
    
    # Handle forbidden errors - redirect to login or show error
    if exc.status_code == 403:  # Forbidden
        if "application/json" not in request.headers.get("accept", ""):
            # Check if user is logged in
            if not request.session.get("user_id"):
                redirect_url = f"/login?redirect={request.url.path}&error=Please%20sign%20in%20to%20access%20this%20page"
                return RedirectResponse(url=redirect_url, status_code=303)
            # User is logged in but doesn't have permission
            error_msg = exc.detail or "You don't have permission to access this resource."
            try:
                return templates.TemplateResponse("error.html", {
                    "request": request,
                    "error": error_msg,
                    "status_code": 403
                }, status_code=403)
            except:
                return HTMLResponse(
                    content=f"<h1>Access Denied</h1><p>{error_msg}</p>",
                    status_code=403
                )
        return JSONResponse(
            status_code=403,
            content={"detail": exc.detail or "Forbidden", "error_type": "forbidden"}
        )
    
    # Handle other HTTP exceptions
    if "application/json" in request.headers.get("accept", ""):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "error_type": "http_exception"}
        )
    else:
        try:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error": exc.detail or "An error occurred",
                "status_code": exc.status_code
            }, status_code=exc.status_code)
        except:
            return HTMLResponse(
                content=f"<h1>Error {exc.status_code}</h1><p>{exc.detail or 'An error occurred'}</p>",
                status_code=exc.status_code
            )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle FastAPI validation errors (e.g., missing form fields) with user-friendly HTML responses."""
    # Log validation error for debugging
    logger.warning(
        f"Validation error: {exc.errors()}",
        extra={
            "url": str(request.url),
            "method": request.method,
            "path": request.url.path,
            "errors": exc.errors()
        }
    )
    
    # For HTML requests, show user-friendly error page
    if "application/json" not in request.headers.get("accept", ""):
        # Check if it's a login/signup page
        if request.url.path in ["/login", "/signup"]:
            try:
                # Get tenants for login page
                from app.db import SessionLocal
                session = SessionLocal()
                try:
                    tenants = session.query(Tenant).filter(Tenant.is_active == True).order_by(Tenant.name).all()
                except:
                    tenants = []
                finally:
                    session.close()
                
                template_name = "login_new.html" if request.url.path == "/login" else "signup_new.html"
                return templates.TemplateResponse(template_name, {
                    "request": request,
                    "error": "Please fill in all required fields (email and password).",
                    "tenants": tenants if request.url.path == "/login" else []
                }, status_code=400)
            except Exception as e:
                logger.error(f"Error rendering validation error page: {e}", exc_info=True)
        
        # For other pages, show generic error page
        try:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error": "Please fill in all required fields.",
                "status_code": 422
            }, status_code=422)
        except:
            return HTMLResponse(
                content="<h1>Validation Error</h1><p>Please fill in all required fields.</p>",
                status_code=422
            )
    
    # For API requests, return JSON
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions with improved logging."""
    # Skip HTTPException as it's handled above
    if isinstance(exc, HTTPException):
        raise exc
    
    # Log full error details with context
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {exc}",
        exc_info=True,
        extra={
            "url": str(request.url),
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client": request.client.host if request.client else None,
        }
    )
    
    # Get user-friendly error message
    from app.error_handling import get_user_friendly_error
    error_message = get_user_friendly_error("unknown_error")
    
    # Return appropriate response based on request type
    if "application/json" in request.headers.get("accept", ""):
        return JSONResponse(
            status_code=500,
            content={"detail": error_message, "error_type": "internal_server_error"}
        )
    else:
        # For HTML requests, return a user-friendly error page
        try:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error": error_message,
                "status_code": 500
            }, status_code=500)
        except:
            # Fallback if error template doesn't exist
            return HTMLResponse(
                content=f"<h1>Internal Server Error</h1><p>{error_message}</p>",
                status_code=500
            )


# ============================================================================
# Authentication Routes
# ============================================================================

@app.get("/")
def root(request: Request):
    """Root endpoint - shows landing page or redirects to dashboard if logged in."""
    if request.session.get("user_id"):
        return RedirectResponse(url="/dashboard", status_code=303)
    return templates.TemplateResponse("landing.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, session: Session = Depends(get_session)):
    """Login page."""
    # Redirect if already logged in
    if request.session.get("user_id"):
        # Check if there's a redirect URL
        redirect_path = request.query_params.get("redirect")
        if redirect_path and redirect_path.startswith("/"):
            return RedirectResponse(url=redirect_path, status_code=303)
        return RedirectResponse(url="/dashboard", status_code=303)
    
    error = request.query_params.get("error")
    success = request.query_params.get("success")
    redirect_path = request.query_params.get("redirect")
    
    # Don't show organization dropdown on login - organization is auto-detected from user's email
    # Organization dropdown should only be on signup page
    
    # Use login_new.html (new design)
    return templates.TemplateResponse("login_new.html", {
        "request": request,
        "error": error,
        "success": success,
        "redirect_path": redirect_path,  # Pass redirect path to template
        "tenants": []  # Empty list - no organization dropdown on login
    })


@app.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    tenant_slug: Optional[str] = Form(None),
    redirect_path: Optional[str] = Form(None),  # Get redirect from form
    session: Session = Depends(get_session)
):
    """Handle login."""
    # Organization is auto-detected from user's email - no need for dropdown
    # Find user by email (organization is already associated with user account)
    # Note: If same email exists in multiple organizations, we'll find the first one
    # In practice, each email should belong to one organization
    
    # Authenticate user - authenticate_user will find the user by email
    # If tenant_id is None, it will find the user regardless of tenant (backward compatibility)
    user = authenticate_user(session, email, password, tenant_id=None)
    if not user:
        return templates.TemplateResponse("login_new.html", {
            "request": request,
            "error": "Invalid email or password",
            "redirect_path": redirect_path,
            "tenants": []
        }, status_code=401)
    
    # Check if email is verified
    if not user.email_verified:
        
        # Create a new verification token if one doesn't exist or is expired
        from app.email_verification import EmailVerificationToken
        existing_token = session.query(EmailVerificationToken).filter(
            EmailVerificationToken.user_id == user.id,
            EmailVerificationToken.used == False
        ).first()
        
        # If no valid token exists, create a new one
        if not existing_token or not existing_token.is_valid():
            verification_token = EmailVerificationToken.create_token(user.id, expires_in_hours=48)
            session.add(verification_token)
            session.commit()
            
            # Send verification email
            try:
                from app.email_service import send_email_verification_email
                base_url = BASE_URL or str(request.base_url).rstrip('/')
                verification_url = f"{base_url}/verify-email"
                send_email_verification_email(
                    to_email=user.email,
                    verification_token=verification_token.token,
                    verification_url=verification_url,
                    user_name=user.full_name
                )
            except Exception as email_error:
                logger.warning(f"Failed to resend verification email: {email_error}")
        
        return templates.TemplateResponse("login_new.html", {
            "request": request,
            "error": f"Please verify your email address before signing in. A verification email has been sent to {user.email}. Check your inbox and click the verification link.",
            "redirect_path": redirect_path,
            "tenants": []
        }, status_code=403)
    
    # Set session
    request.session["user_id"] = user.id
    request.session["user_email"] = user.email
    request.session["user_name"] = user.full_name or user.email
    request.session["last_activity"] = datetime.utcnow().isoformat()  # Track session activity
    
    # Set tenant in session (organization is auto-detected from user's account)
    if user.tenant_id:
        request.session["tenant_id"] = user.tenant_id
    
    # Redirect to original destination or dashboard
    if redirect_path and redirect_path.startswith("/"):
        return RedirectResponse(url=redirect_path, status_code=303)
    return RedirectResponse(url="/dashboard", status_code=303)


@app.get("/logout")
def logout(request: Request):
    """Handle logout."""
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)


@app.get("/forgot-password", response_class=HTMLResponse)
def forgot_password_page(request: Request):
    """Forgot password page."""
    if request.session.get("user_id"):
        return RedirectResponse(url="/dashboard", status_code=303)
    
    error = request.query_params.get("error")
    success = request.query_params.get("success")
    
    return templates.TemplateResponse("forgot_password.html", {
        "request": request,
        "error": error,
        "success": success
    })


@app.post("/forgot-password")
async def forgot_password(
    request: Request,
    email: str = Form(...),
    session: Session = Depends(get_session)
):
    """Handle password reset request."""
    try:
        # Find user by email (check all tenants)
        user = session.query(User).filter(User.email == email).first()
        
        # Always show success message (security best practice - don't reveal if email exists)
        success_message = "If an account with that email exists, we've sent a password reset link."
        
        if user and user.is_active:
            # Create password reset token
            reset_token = PasswordResetToken.create_token(user.id, expires_in_hours=24)
            session.add(reset_token)
            session.commit()
            
            # Get base URL — prefer BASE_URL env var (reliable behind Azure proxy)
            # falling back to request.base_url for local development
            base_url = BASE_URL or str(request.base_url).rstrip('/')
            reset_url = f"{base_url}/reset-password"
            
            # Send email
            send_password_reset_email(
                to_email=user.email,
                reset_token=reset_token.token,
                reset_url=reset_url,
                user_name=user.full_name
            )
        
        return RedirectResponse(
            url=f"/forgot-password?success={success_message.replace(' ', '%20')}",
            status_code=303
        )
        
    except Exception as e:
        logger.error(f"Error in forgot_password: {e}", exc_info=True)
        return RedirectResponse(
            url="/forgot-password?error=An%20error%20occurred.%20Please%20try%20again.",
            status_code=303
        )


@app.get("/reset-password", response_class=HTMLResponse)
def reset_password_page(request: Request, token: Optional[str] = Query(None), session: Session = Depends(get_session)):
    """Password reset page."""
    if request.session.get("user_id"):
        return RedirectResponse(url="/dashboard", status_code=303)
    
    if not token:
        return RedirectResponse(
            url="/forgot-password?error=Invalid%20or%20missing%20reset%20token.",
            status_code=303
        )
    
    # Verify token
    reset_token = session.query(PasswordResetToken).filter(
        PasswordResetToken.token == token
    ).first()
    
    if not reset_token or not reset_token.is_valid():
        return RedirectResponse(
            url="/forgot-password?error=Invalid%20or%20expired%20reset%20token.%20Please%20request%20a%20new%20one.",
            status_code=303
        )
    
    return templates.TemplateResponse("reset_password.html", {
        "request": request,
        "token": token
    })


@app.post("/reset-password")
async def reset_password(
    request: Request,
    token: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    session: Session = Depends(get_session)
):
    """Handle password reset."""
    try:
        # Validate passwords match
        if password != password_confirm:
            return templates.TemplateResponse("reset_password.html", {
                "request": request,
                "token": token,
                "error": "Passwords do not match."
            }, status_code=400)
        
        # Validate password length
        if len(password) < 8:
            return templates.TemplateResponse("reset_password.html", {
                "request": request,
                "token": token,
                "error": "Password must be at least 8 characters long."
            }, status_code=400)
        
        # Verify token
        reset_token = session.query(PasswordResetToken).filter(
            PasswordResetToken.token == token
        ).first()
        
        if not reset_token or not reset_token.is_valid():
            return RedirectResponse(
                url="/forgot-password?error=Invalid%20or%20expired%20reset%20token.%20Please%20request%20a%20new%20one.",
                status_code=303
            )
        
        # Get user
        user = session.query(User).filter(User.id == reset_token.user_id).first()
        if not user:
            return RedirectResponse(
                url="/forgot-password?error=User%20not%20found.",
                status_code=303
            )
        
        # Update password
        user.set_password(password)
        
        # Mark token as used
        reset_token.mark_as_used()
        
        session.commit()
        
        # Redirect to login with success message
        return RedirectResponse(
            url="/login?success=Password%20reset%20successfully.%20Please%20sign%20in%20with%20your%20new%20password.",
            status_code=303
        )
        
    except Exception as e:
        logger.error(f"Error in reset_password: {e}", exc_info=True)
        return templates.TemplateResponse("reset_password.html", {
            "request": request,
            "token": token,
            "error": "An error occurred. Please try again."
        }, status_code=500)


@app.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request, session: Session = Depends(get_session)):
    """Signup page."""
    if request.session.get("user_id"):
        return RedirectResponse(url="/dashboard", status_code=303)
    
    error = request.query_params.get("error")
    success = request.query_params.get("success")
    
    # Get list of tenants for selection (with error handling)
    try:
        tenants = session.query(Tenant).filter(Tenant.is_active == True).order_by(Tenant.name).all()
    except Exception as e:
        logger.error(f"Error loading tenants: {e}")
        tenants = []  # Empty list if database error
    
    return templates.TemplateResponse("signup_new.html", {
        "request": request,
        "error": error,
        "success": success,
        "tenants": tenants
    })


@app.get("/signup-success", response_class=HTMLResponse)
def signup_success_page(request: Request):
    """Signup success confirmation page."""
    email = request.query_params.get("email", "")
    name = request.query_params.get("name", "")
    org = request.query_params.get("org", "")
    verify = request.query_params.get("verify", "false") == "true"
    
    return templates.TemplateResponse("signup_success.html", {
        "request": request,
        "email": email,
        "name": name,
        "organization": org,
        "verify": verify
    })


@app.get("/verify-email", response_class=HTMLResponse)
def verify_email_page(
    request: Request,
    token: Optional[str] = Query(None),
    session: Session = Depends(get_session)
):
    """Email verification page."""
    if not token:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "Invalid or missing verification token. Please check your email for the correct verification link.",
            "status_code": 400
        }, status_code=400)
    
    # Verify token
    from app.email_verification import EmailVerificationToken
    verification_token = session.query(EmailVerificationToken).filter(
        EmailVerificationToken.token == token
    ).first()
    
    if not verification_token or not verification_token.is_valid():
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "Invalid or expired verification link. Please request a new verification email.",
            "status_code": 400
        }, status_code=400)
    
    # Get user
    user = session.query(User).filter(User.id == verification_token.user_id).first()
    if not user:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "User not found.",
            "status_code": 404
        }, status_code=404)
    
    # Mark email as verified
    user.email_verified = True
    
    # Mark token as used
    verification_token.mark_as_used()
    
    session.commit()
    
    # Redirect to login with success message (don't auto-login for better security)
    return RedirectResponse(
        url=f"/login?success=Email%20verified%20successfully!%20Please%20sign%20in%20to%20continue.",
        status_code=303
    )


@app.post("/signup")
async def signup(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    full_name: Optional[str] = Form(None),
    tenant_slug: Optional[str] = Form(None),
    new_tenant_name: Optional[str] = Form(None),
    session: Session = Depends(get_session)
):
    """Handle user registration."""
    try:
        # Validate password confirmation
        if password != password_confirm:
            # Get tenants list for dropdown
            try:
                tenants = session.query(Tenant).filter(Tenant.is_active == True).order_by(Tenant.name).all()
            except:
                tenants = []
            return templates.TemplateResponse("signup_new.html", {
                "request": request,
                "error": "Passwords do not match. Please make sure both password fields are identical.",
                "tenants": tenants
            }, status_code=400)
        tenant_id = None
        
        # If new tenant name provided, create new tenant (check this first)
        if new_tenant_name and new_tenant_name.strip():
            try:
                # Use provided slug if given, otherwise auto-generate
                tenant_slug_value = tenant_slug.strip() if tenant_slug and tenant_slug.strip() else None
                tenant = create_tenant(session, new_tenant_name.strip(), slug=tenant_slug_value)
                tenant_id = tenant.id
            except ValueError as e:
                # Get tenants list for dropdown
                try:
                    tenants = session.query(Tenant).filter(Tenant.is_active == True).order_by(Tenant.name).all()
                except:
                    tenants = []
                return templates.TemplateResponse("signup_new.html", {
                    "request": request,
                    "error": str(e),
                    "tenants": tenants
                }, status_code=400)
        # Otherwise, if tenant_slug provided (for existing tenant selection - not used in current form)
        elif tenant_slug and tenant_slug.strip():
            tenant = session.query(Tenant).filter(Tenant.slug == tenant_slug.strip()).first()
            if tenant:
                tenant_id = tenant.id
            else:
                # Get tenants list for dropdown
                try:
                    tenants = session.query(Tenant).filter(Tenant.is_active == True).order_by(Tenant.name).all()
                except:
                    tenants = []
                return templates.TemplateResponse("signup_new.html", {
                    "request": request,
                    "error": "Selected organization not found",
                    "tenants": tenants
                }, status_code=400)
        # If no tenant name provided, this is an error (required field)
        else:
            # Get tenants list for dropdown
            try:
                tenants = session.query(Tenant).filter(Tenant.is_active == True).order_by(Tenant.name).all()
            except:
                tenants = []
            return templates.TemplateResponse("signup_new.html", {
                "request": request,
                "error": "Organization name is required",
                "tenants": tenants
            }, status_code=400)
        
        user = create_user(session, email, password, full_name, tenant_id=tenant_id)
        # User starts with email_verified=False (default in model)
        
        # Get tenant name for emails
        tenant_name = None
        if tenant_id:
            tenant = session.query(Tenant).filter(Tenant.id == tenant_id).first()
            if tenant:
                tenant_name = tenant.name
        
        # Create email verification token
        from app.email_verification import EmailVerificationToken
        verification_token = EmailVerificationToken.create_token(user.id, expires_in_hours=48)
        session.add(verification_token)
        session.commit()
        
        # Send email verification email (non-blocking - don't fail signup if email fails)
        try:
            from app.email_service import send_email_verification_email
            base_url = BASE_URL or str(request.base_url).rstrip('/')
            verification_url = f"{base_url}/verify-email"
            send_email_verification_email(
                to_email=user.email,
                verification_token=verification_token.token,
                verification_url=verification_url,
                user_name=user.full_name
            )
        except Exception as email_error:
            # Log but don't fail signup if email fails
            logger.warning(f"Failed to send verification email: {email_error}")
        
        # Don't log user in automatically - require email verification first
        # Redirect to a "check your email" page
        return RedirectResponse(
            url=f"/signup-success?email={email}&verify=true",
            status_code=303
        )
    except ValueError as e:
        # Get tenants list for dropdown
        try:
            tenants = session.query(Tenant).filter(Tenant.is_active == True).order_by(Tenant.name).all()
        except:
            tenants = []
        
        # Provide user-friendly error messages for duplicate accounts
        error_message = str(e)
        if "already exists" in error_message.lower():
            if "email" in error_message.lower() or "user" in error_message.lower():
                error_message = "An account with this email already exists. Please sign in instead or use a different email address."
            elif "tenant" in error_message.lower() or "organization" in error_message.lower():
                error_message = "An organization with this name already exists. Please choose a different organization name."
            else:
                error_message = "This account already exists. Please sign in or try again with different details."
        
        return templates.TemplateResponse("signup_new.html", {
            "request": request,
            "error": error_message,
            "tenants": tenants
        }, status_code=400)
    except Exception as e:
        # Catch all other exceptions (database errors, etc.)
        logger.error(f"Unexpected error during signup: {e}", exc_info=True)
        
        # Get tenants list for dropdown
        try:
            tenants = session.query(Tenant).filter(Tenant.is_active == True).order_by(Tenant.name).all()
        except:
            tenants = []
        
        # Provide user-friendly error message
        error_message = "An unexpected error occurred during signup. Please try again or contact support if the problem persists."
        
        # If it's a database error about missing table, provide more specific message
        error_str = str(e).lower()
        if "no such table" in error_str or "relation" in error_str and "does not exist" in error_str:
            error_message = "Database setup error. Please contact support. Error: Missing email verification table."
        
        return templates.TemplateResponse("signup_new.html", {
            "request": request,
            "error": error_message,
            "tenants": tenants
        }, status_code=500)


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "healthy"}


# ============================================================================
# Protected Web UI Routes
# ============================================================================

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(
    request: Request,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Dashboard page with full statistics - requires authentication."""
    # Get tenant_id for filtering
    tenant_id = get_tenant_id(user, request)
    
    # Get statistics (with tenant filtering)
    invoice_query = session.query(Invoice)
    if tenant_id:
        invoice_query = invoice_query.filter(Invoice.tenant_id == tenant_id)
    total_invoices = invoice_query.count()
    
    # Calculate total amount
    total_amount_query = session.query(func.sum(Invoice.gross_amount))
    if tenant_id:
        total_amount_query = total_amount_query.filter(Invoice.tenant_id == tenant_id)
    total_amount = total_amount_query.scalar() or 0
    
    validation_query = session.query(InvoiceValidation)
    if tenant_id:
        validation_query = validation_query.filter(InvoiceValidation.tenant_id == tenant_id)
    validated_invoices = validation_query.count()
    
    # Status breakdown (with tenant filtering)
    status_query = session.query(
        InvoiceValidation.validation_status,
        func.count(InvoiceValidation.id).label('count')
    )
    if tenant_id:
        status_query = status_query.filter(InvoiceValidation.tenant_id == tenant_id)
    status_counts = status_query.group_by(InvoiceValidation.validation_status).all()
    
    valid_count = sum(count for status, count in status_counts if status == 'Valid')
    invalid_count = sum(count for status, count in status_counts if status == 'Invalid')
    review_count = sum(count for status, count in status_counts if status == 'Needs Review')
    
    # Recent invoices (with tenant filtering)
    recent_query = session.query(Invoice)
    if tenant_id:
        recent_query = recent_query.filter(Invoice.tenant_id == tenant_id)
    recent_invoices = recent_query.order_by(Invoice.created_at.desc()).limit(5).all()
    
    recent_with_validation = []
    for invoice in recent_invoices:
        validation = session.query(InvoiceValidation).filter(
            InvoiceValidation.invoice_id == invoice.id
        ).first()
        recent_with_validation.append({
            "invoice": invoice,
            "validation": validation
        })
    
    # Determination breakdown for chart (with tenant filtering)
    determination_query = session.query(
        InvoiceValidation.determination,
        func.count(InvoiceValidation.id).label('count')
    )
    if tenant_id:
        determination_query = determination_query.filter(InvoiceValidation.tenant_id == tenant_id)
    determination_counts = determination_query.group_by(InvoiceValidation.determination).all()
    
    # Calculate percentage changes based on previous period (last 30 days vs previous 30 days)
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    current_period_start = now - timedelta(days=30)
    previous_period_start = current_period_start - timedelta(days=30)
    previous_period_end = current_period_start
    
    # Current period stats
    current_query = session.query(Invoice).filter(Invoice.created_at >= current_period_start)
    if tenant_id:
        current_query = current_query.filter(Invoice.tenant_id == tenant_id)
    current_total = current_query.count()
    
    # Previous period stats
    prev_query = session.query(Invoice).filter(
        Invoice.created_at >= previous_period_start,
        Invoice.created_at < previous_period_end
    )
    if tenant_id:
        prev_query = prev_query.filter(Invoice.tenant_id == tenant_id)
    prev_total = prev_query.count()
    
    # Calculate percentage changes
    def calc_change(current, previous):
        # Don't show percentage if there's no meaningful comparison
        if previous == 0:
            # If going from 0 to something, don't show a percentage (it's misleading)
            # Return None to hide the badge
            return None
        if current == 0 and previous == 0:
            return None  # No change, no data
        if current == previous:
            return None  # No change, hide badge
        
        change = ((current - previous) / previous) * 100
        # Only show if change is significant (at least 1%)
        if abs(change) < 1:
            return None
        
        sign = "+" if change >= 0 else ""
        return f"{sign}{change:.0f}%"
    
    total_change = calc_change(current_total, prev_total)
    
    # Valid invoices change (using validated_at for validation timestamps)
    current_valid = session.query(InvoiceValidation).filter(
        InvoiceValidation.validation_status == 'Valid',
        InvoiceValidation.validated_at >= current_period_start
    )
    if tenant_id:
        current_valid = current_valid.filter(InvoiceValidation.tenant_id == tenant_id)
    current_valid_count = current_valid.count()
    
    prev_valid = session.query(InvoiceValidation).filter(
        InvoiceValidation.validation_status == 'Valid',
        InvoiceValidation.validated_at >= previous_period_start,
        InvoiceValidation.validated_at < previous_period_end
    )
    if tenant_id:
        prev_valid = prev_valid.filter(InvoiceValidation.tenant_id == tenant_id)
    prev_valid_count = prev_valid.count()
    
    valid_change = calc_change(current_valid_count, prev_valid_count)
    
    # Invalid invoices change
    current_invalid = session.query(InvoiceValidation).filter(
        InvoiceValidation.validation_status == 'Invalid',
        InvoiceValidation.validated_at >= current_period_start
    )
    if tenant_id:
        current_invalid = current_invalid.filter(InvoiceValidation.tenant_id == tenant_id)
    current_invalid_count = current_invalid.count()
    
    prev_invalid = session.query(InvoiceValidation).filter(
        InvoiceValidation.validation_status == 'Invalid',
        InvoiceValidation.validated_at >= previous_period_start,
        InvoiceValidation.validated_at < previous_period_end
    )
    if tenant_id:
        prev_invalid = prev_invalid.filter(InvoiceValidation.tenant_id == tenant_id)
    prev_invalid_count = prev_invalid.count()
    
    invalid_change = calc_change(current_invalid_count, prev_invalid_count)
    
    # Needs Review change
    current_review = session.query(InvoiceValidation).filter(
        InvoiceValidation.validation_status == 'Needs Review',
        InvoiceValidation.validated_at >= current_period_start
    )
    if tenant_id:
        current_review = current_review.filter(InvoiceValidation.tenant_id == tenant_id)
    current_review_count = current_review.count()
    
    prev_review = session.query(InvoiceValidation).filter(
        InvoiceValidation.validation_status == 'Needs Review',
        InvoiceValidation.validated_at >= previous_period_start,
        InvoiceValidation.validated_at < previous_period_end
    )
    if tenant_id:
        prev_review = prev_review.filter(InvoiceValidation.tenant_id == tenant_id)
    prev_review_count = prev_review.count()
    
    review_change = calc_change(current_review_count, prev_review_count)
    
    # Get tenant info
    tenant = get_user_tenant(session, user)
    current_tenant = get_current_tenant(request, user, session)
    
    # Check for signup success message
    signup_success = request.query_params.get("signup_success") == "true"
    signup_email = request.query_params.get("email", "")
    
    return templates.TemplateResponse("dashboard_new.html", {
        "request": request,
        "user": user,
        "tenant": current_tenant or tenant,
        "signup_success": signup_success,
        "signup_email": signup_email,
        "stats": {
            "total": total_invoices,
            "total_amount": float(total_amount),
            "validated": validated_invoices,
            "valid": valid_count,
            "invalid": invalid_count,
            "review": review_count,
            "total_change": total_change,
            "valid_change": valid_change,
            "invalid_change": invalid_change,
            "review_change": review_change
        },
        "recent_invoices": recent_with_validation,
        "determination_data": [{"name": d, "value": c} for d, c in determination_counts]
    })


@app.get("/upload", response_class=HTMLResponse)
def upload_page(
    request: Request,
    user: User = Depends(get_current_user)
):
    """File upload page - requires authentication."""
    return templates.TemplateResponse("upload.html", {
        "request": request,
        "user": user
    })


@app.get("/import-units", response_class=HTMLResponse)
def import_units_page(
    request: Request,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Units import page - requires authentication."""
    # Get tenant_id for filtering
    tenant_id = get_tenant_id(user, request)
    if not tenant_id and not user.is_super_admin:
        raise HTTPException(status_code=403, detail="User must be associated with a tenant")
    
    # Count existing units
    units_query = session.query(Unit)
    if tenant_id:
        units_query = units_query.filter(Unit.tenant_id == tenant_id)
    units_count = units_query.count()
    
    return templates.TemplateResponse("import_units.html", {
        "request": request,
        "user": user,
        "units_count": units_count
    })


@app.get("/import-leases", response_class=HTMLResponse)
def import_leases_page(
    request: Request,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Leases import page - requires authentication."""
    # Get tenant_id for filtering
    tenant_id = get_tenant_id(user, request)
    if not tenant_id and not user.is_super_admin:
        raise HTTPException(status_code=403, detail="User must be associated with a tenant")
    
    # Count existing leases
    leases_query = session.query(Lease)
    if tenant_id:
        leases_query = leases_query.filter(Lease.tenant_id == tenant_id)
    leases_count = leases_query.count()
    
    return templates.TemplateResponse("import_leases.html", {
        "request": request,
        "user": user,
        "leases_count": leases_count
    })


@app.get("/settings", response_class=HTMLResponse)
def settings_page(
    request: Request,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Settings page - configure column mappings and data sources."""
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "user": user
    })


@app.get("/data-management", response_class=HTMLResponse)
def data_management_page(
    request: Request,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Data management page - view/edit units and leases."""
    # Get tenant_id for filtering
    tenant_id = get_tenant_id(user, request)
    if not tenant_id and not user.is_super_admin:
        raise HTTPException(status_code=403, detail="User must be associated with a tenant")
    
    # Get units (with pagination)
    units_query = session.query(Unit)
    if tenant_id:
        units_query = units_query.filter(Unit.tenant_id == tenant_id)
    units_count = units_query.count()
    
    # Pagination for units
    units_page = int(request.query_params.get("units_page", 1))
    units_per_page = 20
    units_offset = (units_page - 1) * units_per_page
    units_total_pages = (units_count + units_per_page - 1) // units_per_page
    units = units_query.order_by(Unit.unit_id).offset(units_offset).limit(units_per_page).all()
    
    # Get leases (with pagination)
    leases_query = session.query(Lease)
    if tenant_id:
        leases_query = leases_query.filter(Lease.tenant_id == tenant_id)
    leases_count = leases_query.count()
    
    # Pagination for leases
    leases_page = int(request.query_params.get("leases_page", 1))
    leases_per_page = 20
    leases_offset = (leases_page - 1) * leases_per_page
    leases_total_pages = (leases_count + leases_per_page - 1) // leases_per_page
    leases = leases_query.order_by(Lease.lease_start.desc()).offset(leases_offset).limit(leases_per_page).all()
    
    from datetime import date
    today = date.today()
    
    return templates.TemplateResponse("data_management.html", {
        "request": request,
        "user": user,
        "units": units,
        "units_count": units_count,
        "units_pagination": {
            "page": units_page,
            "per_page": units_per_page,
            "total": units_count,
            "total_pages": units_total_pages,
            "has_prev": units_page > 1,
            "has_next": units_page < units_total_pages
        },
        "leases": leases,
        "leases_count": leases_count,
        "leases_pagination": {
            "page": leases_page,
            "per_page": leases_per_page,
            "total": leases_count,
            "total_pages": leases_total_pages,
            "has_prev": leases_page > 1,
            "has_next": leases_page < leases_total_pages
        },
        "today": today
    })


@app.post("/api/upload")
async def upload_file(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Handle file upload and trigger validation (supports Excel, CSV, and PDF)."""
    # Check file type
    file_ext = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
    
    # Generate batch ID
    batch_id = f"BATCH_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    
    # Save file
    file_path = UPLOAD_DIR / f"{batch_id}_{file.filename}"
    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail=f"File too large. Maximum size is {MAX_UPLOAD_SIZE / 1024 / 1024:.0f}MB")
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Handle PDF files
    if file_ext == 'pdf':
        if not PDF_PROCESSING_AVAILABLE:
            raise HTTPException(
                status_code=400,
                detail="PDF processing is not available. Please install azure-ai-documentintelligence and configure Azure Document Intelligence."
            )
        
        # Process PDF in background
        background_tasks.add_task(process_pdf_invoice, str(file_path), batch_id, user.id)
        
        return JSONResponse({
            "status": "success",
            "message": "PDF invoice uploaded. Processing with AI extraction...",
            "batch_id": batch_id,
            "file_type": "pdf"
        })
    
    # Handle Excel/CSV files (existing flow)
    elif file_ext in ('xlsx', 'xls', 'csv'):
        # Quick validation: try to read the file and check columns
        try:
            if file_ext == 'csv':
                preview_df = pd.read_csv(file_path, nrows=1, encoding='utf-8', errors='ignore')
            else:
                preview_df = pd.read_excel(file_path, nrows=1, engine='openpyxl')
            
            # Convert column names to strings (handle datetime objects, etc.)
            columns_found = [str(col) if col is not None else f"Unnamed_{i}" for i, col in enumerate(preview_df.columns)]
            print(f"File columns detected: {columns_found}")
            
        except Exception as e:
            return JSONResponse({
                "status": "error",
                "message": f"Error reading file: {str(e)}. Please check the file format.",
                "error": str(e)
            }, status_code=400)
        
        # Process file in background (don't pass session - create new one in background task)
        background_tasks.add_task(process_uploaded_file, str(file_path), batch_id, user.id)
        
        return JSONResponse({
            "status": "success",
            "message": "File uploaded successfully. Processing in background...",
            "batch_id": batch_id,
            "columns_detected": columns_found[:10]  # First 10 columns for debugging (already strings)
        })
    
    else:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload Excel (.xlsx, .xls), CSV, or PDF files."
        )


@app.post("/api/import/units")
async def import_units(
    request: Request,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Import units from Excel/CSV file."""
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(status_code=400, detail="Only Excel (.xlsx, .xls) and CSV files are supported")
    
    # Get tenant_id
    tenant_id = get_tenant_id(user, request)
    if not tenant_id and not user.is_super_admin:
        raise HTTPException(status_code=403, detail="User must be associated with a tenant")
    
    # Save file temporarily
    temp_file = UPLOAD_DIR / f"units_import_{uuid.uuid4().hex[:8]}_{file.filename}"
    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail=f"File too large. Maximum size is {MAX_UPLOAD_SIZE / 1024 / 1024:.0f}MB")
    
    with open(temp_file, "wb") as f:
        f.write(content)
    
    try:
        # Read file
        if file.filename.endswith('.csv'):
            df = pd.read_csv(temp_file, encoding='utf-8', errors='ignore')
        else:
            df = pd.read_excel(temp_file, engine='openpyxl')
        
        # Get column mapping from tenant config (or use default)
        unit_mapping = get_column_mapping(session, tenant_id, mapping_type="unit")
        
        # Map columns using helper function
        mapped_cols = map_columns(list(df.columns), unit_mapping)
        
        # Check required columns
        required = ['unit_id', 'building_name', 'address_line_1', 'city', 'postcode']
        missing = [col for col in required if col not in mapped_cols]
        if missing:
            raise create_error_response(
                "missing_columns",
                status_code=400,
                missing=', '.join(missing),
                available=', '.join(df.columns[:10])  # First 10 columns
            )
        
        # Process rows
        units_created = 0
        units_updated = 0
        
        for idx, row in df.iterrows():
            try:
                unit_id = str(row[mapped_cols['unit_id']]).strip()
                if pd.isna(unit_id) or unit_id == '':
                    continue
                
                # Check if unit exists
                existing = session.query(Unit).filter(
                    Unit.unit_id == unit_id,
                    Unit.tenant_id == tenant_id
                ).first()
                
                unit_data = {
                    'unit_id': unit_id,
                    'building_name': str(row[mapped_cols['building_name']]) if mapped_cols.get('building_name') and not pd.isna(row[mapped_cols['building_name']]) else None,
                    'address_line_1': str(row[mapped_cols['address_line_1']]) if mapped_cols.get('address_line_1') and not pd.isna(row[mapped_cols['address_line_1']]) else None,
                    'address_line_2': str(row[mapped_cols['address_line_2']]) if mapped_cols.get('address_line_2') and not pd.isna(row[mapped_cols['address_line_2']]) else None,
                    'city': str(row[mapped_cols['city']]) if mapped_cols.get('city') and not pd.isna(row[mapped_cols['city']]) else None,
                    'postcode': str(row[mapped_cols['postcode']]) if mapped_cols.get('postcode') and not pd.isna(row[mapped_cols['postcode']]) else None,
                    'tenant_id': tenant_id
                }
                
                if existing:
                    # Update existing
                    for key, value in unit_data.items():
                        if key != 'tenant_id':  # Don't update tenant_id
                            setattr(existing, key, value)
                    units_updated += 1
                else:
                    # Create new
                    unit = Unit(**unit_data)
                    session.add(unit)
                    units_created += 1
            except Exception as e:
                continue  # Skip invalid rows
        
        session.commit()
        
        # Clean up temp file
        temp_file.unlink()
        
        return JSONResponse({
            "status": "success",
            "units_created": units_created,
            "units_updated": units_updated,
            "message": f"Successfully imported {units_created} new unit(s) and updated {units_updated} existing unit(s)."
        })
        
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        if temp_file.exists():
            temp_file.unlink()
        raise HTTPException(status_code=400, detail=f"Error importing units: {str(e)}")


@app.post("/api/import/leases")
async def import_leases(
    request: Request,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Import leases from Excel/CSV file."""
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(status_code=400, detail="Only Excel (.xlsx, .xls) and CSV files are supported")
    
    # Get tenant_id
    tenant_id = get_tenant_id(user, request)
    if not tenant_id and not user.is_super_admin:
        raise HTTPException(status_code=403, detail="User must be associated with a tenant")
    
    # Save file temporarily
    temp_file = UPLOAD_DIR / f"leases_import_{uuid.uuid4().hex[:8]}_{file.filename}"
    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail=f"File too large. Maximum size is {MAX_UPLOAD_SIZE / 1024 / 1024:.0f}MB")
    
    with open(temp_file, "wb") as f:
        f.write(content)
    
    try:
        # Read file
        if file.filename.endswith('.csv'):
            df = pd.read_csv(temp_file, encoding='utf-8', errors='ignore')
        else:
            df = pd.read_excel(temp_file, engine='openpyxl')
        
        # Get column mapping from tenant config (or use default)
        lease_mapping = get_column_mapping(session, tenant_id, mapping_type="lease")
        
        # Map columns using helper function
        mapped_cols = map_columns(list(df.columns), lease_mapping)
        
        # Check required columns
        required = ['unit_id', 'tenant_name', 'lease_start']
        missing = [col for col in required if col not in mapped_cols]
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(missing)}. Found columns: {', '.join(df.columns)}"
            )
        
        # Get valid unit_ids for this tenant
        valid_unit_ids = {u.unit_id for u in session.query(Unit.unit_id).filter(Unit.tenant_id == tenant_id).all()}
        
        # Process rows
        leases_created = 0
        invalid_unit_ids = []
        
        def parse_date(date_val):
            """Parse date from various formats."""
            if pd.isna(date_val):
                return None
            if isinstance(date_val, date):
                return date_val
            if isinstance(date_val, datetime):
                return date_val.date()
            date_str = str(date_val).strip()
            if not date_str or date_str.lower() in ['none', 'null', 'ongoing', '']:
                return None
            # Try common date formats
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d']:
                try:
                    return datetime.strptime(date_str.split()[0], fmt).date()
                except:
                    continue
            return None
        
        for idx, row in df.iterrows():
            try:
                unit_id = str(row[mapped_cols['unit_id']]).strip()
                if pd.isna(unit_id) or unit_id == '':
                    continue
                
                # Validate unit_id exists
                if unit_id not in valid_unit_ids:
                    invalid_unit_ids.append(unit_id)
                    continue
                
                tenant_name = str(row[mapped_cols['tenant_name']]) if mapped_cols.get('tenant_name') and not pd.isna(row[mapped_cols['tenant_name']]) else None
                lease_start = parse_date(row[mapped_cols['lease_start']])
                lease_end = parse_date(row[mapped_cols.get('lease_end')]) if mapped_cols.get('lease_end') else None
                
                if not lease_start:
                    continue  # Skip if no start date
                
                # Create lease
                lease = Lease(
                    tenant_id=tenant_id,
                    unit_id=unit_id,
                    tenant_name=tenant_name,
                    lease_start=lease_start,
                    lease_end=lease_end
                )
                session.add(lease)
                leases_created += 1
            except Exception as e:
                continue  # Skip invalid rows
        
        session.commit()
        
        # Regenerate unit timelines for this tenant
        try:
            generate_unit_timeline(session, tenant_id=tenant_id)
            timeline_regenerated = True
        except Exception as e:
            timeline_regenerated = False
        
        # Clean up temp file
        temp_file.unlink()
        
        return JSONResponse({
            "status": "success",
            "leases_created": leases_created,
            "invalid_unit_ids": list(set(invalid_unit_ids))[:10],  # First 10 unique invalid IDs
            "timeline_regenerated": timeline_regenerated,
            "message": f"Successfully imported {leases_created} lease(s)."
        })
        
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        if temp_file.exists():
            temp_file.unlink()
        raise HTTPException(status_code=400, detail=f"Error importing leases: {str(e)}")


def process_uploaded_file(file_path: str, batch_id: str, user_id: int):
    """Process uploaded file and load invoices into database."""
    # Create new session for background task
    from app.db import get_session
    import logging
    
    # Set up logging to file
    log_file = Path("uploads") / f"upload_{batch_id}.log"
    log_file.parent.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    logger.info(f"Starting upload processing for batch {batch_id}")
    
    # Create a new session for background task - MUST be closed manually
    from app.db import SessionLocal
    session = SessionLocal()
    
    try:
        # Get user and tenant_id
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User {user_id} not found")
            return
        
        tenant_id = user.tenant_id
        if not tenant_id and not user.is_super_admin:
            logger.error(f"User {user_id} has no tenant_id")
            return
        
        # Create upload status record
        upload_status = UploadStatus(
            tenant_id=tenant_id,
            batch_id=batch_id,
            file_name=Path(file_path).name,
            status='processing',
            user_id=user_id
        )
        session.add(upload_status)
        session.commit()
        logger.info("[OK] Upload status record created")
    except Exception as e:
        logger.error(f"Error creating upload status: {e}")
        session.rollback()
    
    try:
        # Read Excel or CSV
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path, encoding='utf-8', errors='ignore')
        else:
            # Try to find the header row (skip rows that don't look like headers)
            # Common patterns: header might be in row 0, 5, or 6
            df = None
            header_row = None
            
            for skip_rows in [0, 5, 6]:
                try:
                    test_df = pd.read_excel(file_path, skiprows=skip_rows, engine='openpyxl')
                    # Check if this looks like a header row (has invoice number column)
                    cols_lower = [str(c).lower().strip() for c in test_df.columns]
                    if any('invoice' in c or 'inv' in c for c in cols_lower):
                        df = test_df
                        header_row = skip_rows
                        print(f"Found header at row {skip_rows}")
                        break
                except Exception as e:
                    print(f"Tried skip_rows={skip_rows}, error: {e}")
                    continue
            
            if df is None:
                # Fallback: read from first sheet, first row
                print("Using default header row (0)")
                df = pd.read_excel(file_path, engine='openpyxl')
        
        # Clean column names: strip whitespace, handle NaN
        df.columns = [str(col).strip() if pd.notna(col) else f"Unnamed_{i}" for i, col in enumerate(df.columns)]
        
        # Get column mapping from tenant config (or use default)
        column_mapping = get_column_mapping(session, tenant_id, mapping_type="invoice")
        
        # Map columns using helper function
        mapping_found = map_columns(list(df.columns), column_mapping)
        
        # Create mapped DataFrame
        mapped_df = pd.DataFrame()
        for target_col, source_col in mapping_found.items():
            if source_col in df.columns:
                mapped_df[target_col] = df[source_col]
        
        # Debug: log what we found
        logger.info("[INFO] Column mapping found:")
        for target, source in mapping_found.items():
            logger.info(f"  {target} <- {source}")
        print(f"Column mapping found:")
        for target, source in mapping_found.items():
            print(f"  {target} <- {source}")
        
        # Validate required columns
        required = ['invoice_number', 'supplier_account_number', 'supplier_name', 'unit_id', 'billing_period_start', 'billing_period_end', 'gross_amount', 'utility_type']
        missing = [col for col in required if col not in mapped_df.columns]
        if missing:
            error_msg = f"Error: Missing required columns: {missing}\nAvailable columns: {list(df.columns)}"
            logger.error(error_msg)
            print(error_msg)
            # Update upload status with error
            upload_status = session.query(UploadStatus).filter_by(batch_id=batch_id).first()
            if upload_status:
                upload_status.status = 'error'
                upload_status.errors = error_msg
                upload_status.completed_at = datetime.utcnow()
                session.commit()
            return
        
        # Parse dates and amounts
        from scripts.load_invoices import parse_date, parse_decimal
        
        invoices_created = 0
        errors = []
        
        # Remove rows where all required fields are empty
        mapped_df = mapped_df.dropna(subset=['invoice_number', 'supplier_account_number', 'supplier_name', 'unit_id'], how='all')
        
        # Track invoices in current batch to prevent duplicates within the same file
        current_batch_invoices = {}  # {(invoice_number, gross_amount): row_index}
        
        for idx, row in mapped_df.iterrows():
            try:
                # Skip if invoice number is missing or empty
                if pd.isna(row.get('invoice_number')) or str(row.get('invoice_number')).strip() == '':
                    continue
                
                # Parse dates - handle NaN values
                billing_start_str = str(row['billing_period_start']) if pd.notna(row.get('billing_period_start')) else ''
                billing_end_str = str(row['billing_period_end']) if pd.notna(row.get('billing_period_end')) else ''
                invoice_date_str = str(row.get('invoice_date', '')) if pd.notna(row.get('invoice_date')) else ''
                
                billing_start = parse_date(billing_start_str)
                billing_end = parse_date(billing_end_str)
                invoice_date = parse_date(invoice_date_str) if invoice_date_str else None
                
                # Parse amounts - handle NaN and empty values
                gross_amount_str = str(row['gross_amount']) if pd.notna(row.get('gross_amount')) else ''
                net_amount_str = str(row.get('net_amount', '')) if pd.notna(row.get('net_amount')) else ''
                vat_amount_str = str(row.get('vat_amount', '')) if pd.notna(row.get('vat_amount')) else ''
                
                gross_amount = parse_decimal(gross_amount_str)
                net_amount = parse_decimal(net_amount_str) if net_amount_str else None
                vat_amount = parse_decimal(vat_amount_str) if vat_amount_str else None
                
                if gross_amount is None:
                    errors.append(f"Row {idx+1}: Invalid gross_amount: {gross_amount_str}")
                    continue
                
                # Validate supplier_account_number (required and must be different from invoice number)
                supplier_account_number = str(row.get('supplier_account_number', '')).strip() if pd.notna(row.get('supplier_account_number')) else ''
                invoice_number = str(row['invoice_number']).strip()
                
                if not supplier_account_number or supplier_account_number == '':
                    errors.append(f"Row {idx+1}: Missing required field 'supplier_account_number'. Account number is mandatory for all invoices.")
                    continue
                
                if supplier_account_number == invoice_number:
                    errors.append(f"Row {idx+1}: supplier_account_number cannot be the same as invoice_number. Account number must be unique.")
                    continue
                
                # Check for duplicate BEFORE creating invoice
                invoice_key = (invoice_number, gross_amount)
                
                # First check: duplicate within current batch (same file)
                if invoice_key in current_batch_invoices:
                    original_row = current_batch_invoices[invoice_key]
                    errors.append({
                        "type": "duplicate_in_file",
                        "row": idx + 1,
                        "invoice_number": invoice_number,
                        "amount": float(gross_amount),
                        "original_row": original_row
                    })
                    logger.warning(f"Duplicate invoice skipped (within batch): {invoice_number} (Amount: {gross_amount})")
                    continue
                
                # Second check: duplicate in database (historical invoices, within same tenant)
                duplicate_query = session.query(Invoice).filter(
                    Invoice.invoice_number == invoice_number,
                    Invoice.gross_amount == gross_amount
                )
                if tenant_id:
                    duplicate_query = duplicate_query.filter(Invoice.tenant_id == tenant_id)
                existing_duplicate = duplicate_query.first()
                
                if existing_duplicate:
                    # Skip duplicate - don't add it
                    duplicate_batch = existing_duplicate.source_batch or "unknown batch"
                    errors.append({
                        "type": "duplicate_historical",
                        "row": idx + 1,
                        "invoice_number": invoice_number,
                        "amount": float(gross_amount),
                        "existing_batch": duplicate_batch
                    })
                    logger.warning(f"Duplicate invoice skipped (historical): {invoice_number} (Amount: {gross_amount})")
                    continue
                
                # Track this invoice in current batch
                current_batch_invoices[invoice_key] = idx + 1  # Store row number (1-indexed)
                
                # Create invoice
                invoice = Invoice(
                    tenant_id=tenant_id,
                    invoice_number=invoice_number,
                    supplier_account_number=supplier_account_number,  # Required field (validated above)
                    supplier_name=str(row['supplier_name']).strip() if pd.notna(row.get('supplier_name')) else 'Unknown',
                    unit_id=str(row['unit_id']).strip() if pd.notna(row.get('unit_id')) else 'UNKNOWN',
                    address=str(row['address']).strip() if pd.notna(row.get('address')) else None,
                    billing_period_start=billing_start,
                    billing_period_end=billing_end,
                    invoice_date=invoice_date,
                    gross_amount=gross_amount,
                    net_amount=net_amount,
                    vat_amount=vat_amount,
                    utility_type=str(row['utility_type']).strip() if pd.notna(row.get('utility_type')) else 'Unknown',
                    currency=str(row.get('currency', 'GBP')).strip() if pd.notna(row.get('currency')) else 'GBP',
                    source_batch=batch_id
                )
                
                session.add(invoice)
                invoices_created += 1
            except Exception as e:
                error_msg = f"Row {idx+1}: {str(e)}"
                errors.append(error_msg)
                print(error_msg)
                import traceback
                traceback.print_exc()
                continue
        
        # Update upload status
        upload_status.status = 'completed' if invoices_created > 0 else 'error'
        upload_status.invoices_created = invoices_created
        upload_status.total_rows = len(mapped_df)
        upload_status.completed_at = datetime.utcnow()
        if errors:
            import json
            # Convert error dicts to strings for storage, but keep structure for API
            error_strings = []
            for err in errors[:50]:
                if isinstance(err, dict):
                    if err["type"] == "duplicate_historical":
                        error_strings.append(f"Row {err['row']}: Invoice #{err['invoice_number']} (Amount: £{err['amount']:.2f}) already exists in batch {err['existing_batch']}")
                    elif err["type"] == "duplicate_in_file":
                        error_strings.append(f"Row {err['row']}: Invoice #{err['invoice_number']} (Amount: £{err['amount']:.2f}) duplicates row {err['original_row']}")
                else:
                    error_strings.append(str(err))
            upload_status.errors = json.dumps(errors[:50])  # Store structured errors
        
        if invoices_created > 0:
            session.commit()
            logger.info(f"[OK] Loaded {invoices_created} invoices from {file_path}")
            print(f"Loaded {invoices_created} invoices from {file_path}")
            
            # Count duplicates separately
            duplicate_errors = [e for e in errors if isinstance(e, dict) and e.get("type", "").startswith("duplicate")]
            other_errors = [e for e in errors if not (isinstance(e, dict) and e.get("type", "").startswith("duplicate"))]
            
            if duplicate_errors:
                logger.warning(f"[WARN] {len(duplicate_errors)} duplicate invoice(s) skipped")
                print(f"⚠ {len(duplicate_errors)} duplicate invoice(s) were skipped (not uploaded)")
                if len(duplicate_errors) <= 5:
                    for err in duplicate_errors:
                        print(f"  - {err}")
                else:
                    for err in duplicate_errors[:3]:
                        print(f"  - {err}")
                    print(f"  ... and {len(duplicate_errors) - 3} more duplicates")
            
            if other_errors:
                logger.warning(f"[WARN] {len(other_errors)} other errors encountered")
                print(f"⚠ {len(other_errors)} other errors encountered (first 5):")
                for err in other_errors[:5]:
                    logger.warning(f"  - {err}")
                    print(f"  - {err}")
        else:
            session.commit()  # Commit status even if no invoices
            logger.error(f"[ERROR] No invoices loaded. Errors:")
            print(f"✗ No invoices loaded. Errors:")
            for err in errors[:10]:
                logger.error(f"  - {err}")
                print(f"  - {err}")
            return
        
        # Auto-validate after loading
        if invoices_created > 0:
            from app.validation import generate_unit_timeline
            generate_unit_timeline(session, tenant_id=tenant_id)
            
            # Validate invoices (with tenant filtering)
            invoice_query = session.query(Invoice).filter(Invoice.source_batch == batch_id)
            if tenant_id:
                invoice_query = invoice_query.filter(Invoice.tenant_id == tenant_id)
            invoices = invoice_query.all()
            for invoice in invoices:
                try:
                    existing = session.query(InvoiceValidation).filter(
                        InvoiceValidation.invoice_id == invoice.id
                    ).first()
                    
                    if existing:
                        validation = validate_invoice(session, invoice)
                        validation.id = existing.id
                        session.merge(validation)
                    else:
                        validation = validate_invoice(session, invoice)
                        session.add(validation)
                except Exception as e:
                    print(f"Error validating invoice {invoice.id}: {e}")
            
            session.commit()
            print(f"Validated {invoices_created} invoices")
        
    except Exception as e:
        error_msg = f"Error processing file {file_path}: {e}"
        print(error_msg)
        traceback.print_exc()
        
        # Update upload status with error
        try:
            upload_status = session.query(UploadStatus).filter_by(batch_id=batch_id).first()
            if upload_status:
                upload_status.status = 'error'
                upload_status.errors = str(e)
                upload_status.completed_at = datetime.utcnow()
                session.commit()
        except Exception as update_error:
            print(f"Error updating upload status: {update_error}")
    finally:
        # CRITICAL: Always close the session to prevent connection leaks
        try:
            session.close()
        except Exception as close_error:
            logger.error(f"Error closing session: {close_error}")


def process_pdf_invoice(file_path: str, batch_id: str, user_id: int):
    """Process PDF invoice using Azure Document Intelligence and normalize to Invoice schema."""
    # Create new session for background task
    from app.db import get_session
    import logging
    
    # Set up logging to file
    log_file = Path("uploads") / f"upload_{batch_id}.log"
    log_file.parent.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    logger.info(f"Starting PDF invoice processing for batch {batch_id}")
    
    # Create a new session for background task - MUST be closed manually
    from app.db import SessionLocal
    session = SessionLocal()
    
    try:
        # Get user and tenant_id
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User {user_id} not found")
            return
        
        tenant_id = user.tenant_id
        if not tenant_id and not user.is_super_admin:
            logger.error(f"User {user_id} has no tenant_id")
            return
        
        # Create upload status record
        upload_status = UploadStatus(
            tenant_id=tenant_id,
            batch_id=batch_id,
            file_name=Path(file_path).name,
            status='processing',
            user_id=user_id
        )
        session.add(upload_status)
        session.commit()
        logger.info("[OK] Upload status record created")
    except Exception as e:
        logger.error(f"Error creating upload status: {e}")
        session.rollback()
        session.close()
        return
    
    try:
        # Step 1: Extract data from PDF using Azure Document Intelligence
        logger.info(f"Extracting invoice data from PDF: {Path(file_path).name}")
        
        try:
            if not PDF_PROCESSING_AVAILABLE:
                raise Exception("PDF processing not available - Azure package not installed or not configured")
            
            processor = PDFProcessor()
            extracted_data = processor.extract_invoice(file_path)
            logger.info("[OK] PDF extraction completed")
        except Exception as e:
            error_msg = f"Failed to extract PDF invoice: {str(e)}"
            logger.error(f"[ERROR] {error_msg}")
            upload_status.status = 'error'
            upload_status.errors = f'{{"error": "{error_msg}"}}'
            upload_status.completed_at = datetime.utcnow()
            session.commit()
            return
        
        # Step 2: Normalize extracted data to Invoice schema
        logger.info("Normalizing extracted data to Invoice schema")
        
        try:
            # Try to detect supplier name from extracted data
            supplier_name = None
            if "fields" in extracted_data:
                supplier_field = extracted_data["fields"].get("VendorName") or extracted_data["fields"].get("SupplierName")
                if supplier_field:
                    if isinstance(supplier_field, dict):
                        supplier_name = supplier_field.get("value") or supplier_field.get("content")
                    else:
                        supplier_name = supplier_field
            
            normalizer = PDFNormalizer(supplier_name=supplier_name)
            normalized_invoices = normalizer.normalize(extracted_data)
            
            if not normalized_invoices:
                raise Exception("No valid invoice data extracted from PDF")
            
            logger.info(f"[OK] Normalized {len(normalized_invoices)} invoice(s) from PDF")
        except Exception as e:
            error_msg = f"Failed to normalize invoice data: {str(e)}"
            logger.error(f"[ERROR] {error_msg}")
            upload_status.status = 'error'
            upload_status.errors = f'{{"error": "{error_msg}"}}'
            upload_status.completed_at = datetime.utcnow()
            session.commit()
            return
        
        # Step 3: Save normalized invoices to database
        invoices_created = 0
        errors = []
        
        for invoice_data in normalized_invoices:
            try:
                # Validate required fields
                if not invoice_data.get("invoice_number"):
                    errors.append("Missing invoice_number")
                    continue
                
                supplier_account_number = invoice_data.get("supplier_account_number")
                if not supplier_account_number or supplier_account_number == "UNKNOWN" or supplier_account_number == invoice_data.get("invoice_number"):
                    errors.append(f"Invoice {invoice_data.get('invoice_number', 'unknown')}: Missing or invalid supplier_account_number. Account number is mandatory and must be different from invoice number.")
                    continue
                
                if not invoice_data.get("billing_period_start") or not invoice_data.get("billing_period_end"):
                    errors.append(f"Invoice {invoice_data.get('invoice_number', 'unknown')}: Missing billing period dates")
                    continue
                
                if not invoice_data.get("gross_amount"):
                    errors.append(f"Invoice {invoice_data.get('invoice_number', 'unknown')}: Missing gross_amount")
                    continue
                
                # Check for duplicates (within same tenant)
                existing = session.query(Invoice).filter(
                    Invoice.tenant_id == tenant_id,
                    Invoice.invoice_number == invoice_data["invoice_number"],
                    Invoice.gross_amount == Decimal(str(invoice_data["gross_amount"]))
                ).first()
                
                if existing:
                    errors.append({
                        "type": "duplicate_historical",
                        "row": invoices_created + 1,
                        "invoice_number": invoice_data["invoice_number"],
                        "amount": float(invoice_data["gross_amount"]),
                        "existing_batch": existing.source_batch or "unknown"
                    })
                    logger.warning(f"Duplicate invoice skipped: {invoice_data['invoice_number']}")
                    continue
                
                # Use InvoiceUnitMapper for flexible, priority-based mapping
                from app.invoice_unit_mapper import InvoiceUnitMapper
                
                extracted_unit_id = str(invoice_data.get("unit_id", "UNKNOWN"))
                invoice_address = str(invoice_data.get("address")).strip() if invoice_data.get("address") else None
                
                # Create a temporary invoice object for matching
                temp_invoice = Invoice(
                    tenant_id=tenant_id,
                    invoice_number=str(invoice_data["invoice_number"]),
                    supplier_account_number=str(invoice_data.get("supplier_account_number", "UNKNOWN")),
                    supplier_name=str(invoice_data.get("supplier_name", "Unknown Supplier")),
                    unit_id=extracted_unit_id,
                    address=invoice_address,
                    billing_period_start=invoice_data["billing_period_start"],
                    billing_period_end=invoice_data["billing_period_end"],
                    invoice_date=invoice_data.get("invoice_date"),
                    gross_amount=Decimal(str(invoice_data["gross_amount"])),
                    net_amount=Decimal(str(invoice_data["net_amount"])) if invoice_data.get("net_amount") else None,
                    vat_amount=Decimal(str(invoice_data["vat_amount"])) if invoice_data.get("vat_amount") else None,
                    utility_type=str(invoice_data.get("utility_type", "Electricity")),
                    currency=str(invoice_data.get("currency", "GBP")),
                    source_batch=batch_id
                )
                
                # Use mapper service to find best match
                mapper = InvoiceUnitMapper(session, tenant_id)
                matched_unit_id, mapping_method, mapping_details = mapper.map_invoice_to_unit(
                    temp_invoice,
                    extracted_unit_id=extracted_unit_id,
                    auto_apply_threshold=0.7
                )
                
                final_unit_id = matched_unit_id if matched_unit_id else "UNKNOWN"
                
                # Log mapping result
                if mapping_method == "exact_match":
                    logger.info(f"Invoice {invoice_data['invoice_number']}: Exact unit_id match: {final_unit_id}")
                elif mapping_method == "account_mapping":
                    logger.info(f"Invoice {invoice_data['invoice_number']}: Account number mapping → {final_unit_id}")
                elif mapping_method == "address_match":
                    logger.info(
                        f"Invoice {invoice_data['invoice_number']}: Address match → {final_unit_id} "
                        f"(confidence: {mapping_details['confidence']:.0%})"
                    )
                elif mapping_method == "manual_required":
                    logger.warning(
                        f"Invoice {invoice_data['invoice_number']}: Manual mapping required. "
                        f"Reason: {mapping_details.get('reason', 'No match found')}"
                    )
                    if mapping_details.get("suggestions"):
                        suggestions = ", ".join([f"{s['unit_id']} ({s['similarity_score']:.0%})" for s in mapping_details["suggestions"]])
                        logger.info(f"  Suggestions: {suggestions}")
                
                # Create Invoice record
                invoice = Invoice(
                    tenant_id=tenant_id,
                    invoice_number=str(invoice_data["invoice_number"]),
                    supplier_account_number=str(invoice_data.get("supplier_account_number", "UNKNOWN")),  # Required field
                    supplier_name=str(invoice_data.get("supplier_name", "Unknown Supplier")),
                    unit_id=final_unit_id,
                    address=str(invoice_data.get("address")).strip() if invoice_data.get("address") else None,
                    billing_period_start=invoice_data["billing_period_start"],
                    billing_period_end=invoice_data["billing_period_end"],
                    invoice_date=invoice_data.get("invoice_date"),
                    gross_amount=Decimal(str(invoice_data["gross_amount"])),
                    net_amount=Decimal(str(invoice_data["net_amount"])) if invoice_data.get("net_amount") else None,
                    vat_amount=Decimal(str(invoice_data["vat_amount"])) if invoice_data.get("vat_amount") else None,
                    utility_type=str(invoice_data.get("utility_type", "Electricity")),
                    currency=str(invoice_data.get("currency", "GBP")),
                    source_batch=batch_id
                )
                
                session.add(invoice)
                invoices_created += 1
                logger.info(f"Created invoice: {invoice.invoice_number}")
                
            except Exception as e:
                error_msg = f"Error creating invoice: {str(e)}"
                errors.append(error_msg)
                logger.error(f"[ERROR] {error_msg}")
                import traceback
                traceback.print_exc()
                continue
        
        # Update upload status
        upload_status.status = 'completed' if invoices_created > 0 else 'error'
        upload_status.invoices_created = invoices_created
        upload_status.total_rows = len(normalized_invoices)
        upload_status.completed_at = datetime.utcnow()
        
        if errors:
            import json
            error_strings = []
            for err in errors[:50]:
                if isinstance(err, dict):
                    if err["type"] == "duplicate_historical":
                        error_strings.append(f"Invoice #{err['invoice_number']} (Amount: £{err['amount']:.2f}) already exists in batch {err['existing_batch']}")
                else:
                    error_strings.append(str(err))
            upload_status.errors = json.dumps(errors[:50])
        
        if invoices_created > 0:
            session.commit()
            logger.info(f"[OK] Loaded {invoices_created} invoice(s) from PDF")
            print(f"Loaded {invoices_created} invoice(s) from PDF")
            
            # Batch match invoices to units (if needed)
            from app.batch_unit_matcher import batch_match_invoices_to_units
            invoice_query = session.query(Invoice).filter(Invoice.source_batch == batch_id)
            if tenant_id:
                invoice_query = invoice_query.filter(Invoice.tenant_id == tenant_id)
            invoices = invoice_query.all()
            
            if invoices:
                # Batch match invoices to units
                match_result = batch_match_invoices_to_units(
                    session, invoices, tenant_id,
                    auto_apply_threshold=0.85,
                    rule_priority=True
                )
                logger.info(f"Batch matching: {match_result.auto_matched} auto-matched, "
                           f"{match_result.rule_matched} rule-matched, "
                           f"{match_result.exact_match} exact match, "
                           f"{match_result.needs_review} need review")
            
            # Auto-validate after loading and matching
            from app.validation import generate_unit_timeline
            generate_unit_timeline(session, tenant_id=tenant_id)
            
            # Validate invoices
            invoices = invoice_query.all()
            
            for invoice in invoices:
                try:
                    existing = session.query(InvoiceValidation).filter(
                        InvoiceValidation.invoice_id == invoice.id
                    ).first()
                    
                    if existing:
                        validation = validate_invoice(session, invoice)
                        validation.id = existing.id
                        session.merge(validation)
                    else:
                        validation = validate_invoice(session, invoice)
                        session.add(validation)
                except Exception as e:
                    logger.error(f"Error validating invoice {invoice.id}: {e}")
            
            session.commit()
            logger.info(f"[OK] Validated {invoices_created} invoice(s)")
            print(f"Validated {invoices_created} invoice(s)")
        else:
            session.commit()
            logger.error(f"[ERROR] No invoices loaded from PDF. Errors: {errors}")
            print(f"✗ No invoices loaded from PDF. Errors:")
            for err in errors[:10]:
                print(f"  - {err}")
    
    except Exception as e:
        logger.error(f"[ERROR] Unexpected error processing PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        upload_status.status = 'error'
        upload_status.errors = f'{{"error": "{str(e)}"}}'
        upload_status.completed_at = datetime.utcnow()
        session.commit()
    
    finally:
        session.close()


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/api/invoices", response_model=List[InvoiceWithValidationResponse])
def list_invoices(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    batch_number: Optional[str] = None,
    validation_status: Optional[str] = None,
    determination: Optional[str] = None,
    search: Optional[str] = Query(None, alias="q"),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """List invoices with their validation results."""
    query = session.query(Invoice)
    
    # Apply tenant filtering
    query = filter_by_tenant(query, Invoice, user, request)
    
    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Invoice.invoice_number.ilike(search_term),
                Invoice.supplier_name.ilike(search_term),
                Invoice.unit_id.ilike(search_term)
            )
        )
    
    # Apply filters - only join once if both status and determination filters are present
    if batch_number:
        query = query.filter(Invoice.source_batch == batch_number)
    
    if validation_status or determination:
        query = query.join(InvoiceValidation, isouter=False)
        
        if validation_status:
            query = query.filter(
                InvoiceValidation.validation_status == validation_status
            )
        if determination:
            query = query.filter(
                InvoiceValidation.determination == determination
            )
    
    # Order by created_at descending
    query = query.order_by(Invoice.created_at.desc())
    
    # Apply pagination
    invoices = query.offset(skip).limit(limit).all()
    
    result = []
    for invoice in invoices:
        validation = session.query(InvoiceValidation).filter(
            InvoiceValidation.invoice_id == invoice.id
        ).first()
        
        # Convert to response models
        try:
            invoice_data = InvoiceResponse.model_validate(invoice)
        except:
            invoice_data = InvoiceResponse.from_orm(invoice)
        
        validation_data = None
        if validation:
            try:
                validation_data = InvoiceValidationResponse.model_validate(validation)
            except:
                validation_data = InvoiceValidationResponse.from_orm(validation)
        
        result.append(InvoiceWithValidationResponse(
            invoice=invoice_data,
            validation=validation_data
        ))
    
    return result


@app.get("/api/invoices/unmapped")
async def get_unmapped_invoices(
    request: Request,
    batch_id: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get invoices that need unit mapping."""
    tenant_id = get_tenant_id(user, request)
    
    from app.invoice_mapper import get_unmapped_invoices
    unmapped = get_unmapped_invoices(session, tenant_id, batch_id=batch_id)
    
    return {"unmapped_invoices": unmapped, "count": len(unmapped)}


@app.post("/api/invoices/batch-map")
async def batch_map_invoices_endpoint(
    request: Request,
    mapping_request: dict = Body(...),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Batch process multiple invoices for unit mapping."""
    tenant_id = get_tenant_id(user, request)
    
    invoice_ids = mapping_request.get("invoice_ids", [])
    auto_apply = mapping_request.get("auto_apply", True)
    auto_match_threshold = mapping_request.get("auto_match_threshold", 0.85)
    
    if not invoice_ids:
        raise HTTPException(status_code=400, detail="invoice_ids is required")
    
    from app.invoice_mapper import batch_map_invoices
    result = batch_map_invoices(
        session, invoice_ids, tenant_id,
        auto_apply=auto_apply,
        auto_match_threshold=auto_match_threshold
    )
    
    return result


@app.get("/api/invoices/{invoice_id}/unit-matches")
async def get_invoice_unit_matches(
    invoice_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get potential unit matches for an invoice based on address similarity."""
    tenant_id = get_tenant_id(user, request)
    
    invoice = session.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.tenant_id == tenant_id
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    from app.unit_matcher import find_matching_units
    matches = find_matching_units(session, invoice, tenant_id, threshold=0.3)
    
    return {"matches": matches}


@app.patch("/api/invoices/{invoice_id}/unit")
async def update_invoice_unit(
    invoice_id: int,
    request: Request,
    unit_data: dict = Body(...),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Update invoice unit_id, save as mapping rule, and re-validate."""
    tenant_id = get_tenant_id(user, request)
    
    invoice = session.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.tenant_id == tenant_id
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    new_unit_id = unit_data.get("unit_id")
    if not new_unit_id:
        raise HTTPException(status_code=400, detail="unit_id is required")
    
    # Verify unit exists
    from app.unit_matcher import check_unit_exists
    if not check_unit_exists(session, new_unit_id, tenant_id):
        raise HTTPException(status_code=400, detail=f"Unit '{new_unit_id}' not found")
    
    # Save old unit_id for mapping rule
    old_unit_id = invoice.unit_id
    
    # Update invoice unit_id
    invoice.unit_id = new_unit_id
    session.commit()
    
    # Save as mapping rule for future invoices (if not exact match)
    if old_unit_id and old_unit_id != new_unit_id and old_unit_id not in ["UNKNOWN", "None", "N/A", ""]:
        from app.unit_mapping_config import save_unit_mapping_rule
        save_unit_mapping_rule(session, tenant_id, old_unit_id, new_unit_id, confidence=1.0)
        logger.info(f"Saved mapping rule: {old_unit_id} -> {new_unit_id} (from invoice {invoice.invoice_number})")
    
    # Re-validate invoice
    from app.validation import validate_invoice, generate_unit_timeline
    generate_unit_timeline(session, unit_id=new_unit_id, tenant_id=tenant_id)
    
    validation = validate_invoice(session, invoice)
    
    # Update or create validation record
    existing = session.query(InvoiceValidation).filter(
        InvoiceValidation.invoice_id == invoice.id
    ).first()
    
    if existing:
        validation.id = existing.id
        session.merge(validation)
    else:
        session.add(validation)
    
    session.commit()
    
    return {
        "success": True,
        "message": f"Invoice unit_id updated to {new_unit_id}",
        "validation_status": validation.validation_status,
        "determination": validation.determination,
        "mapping_rule_saved": old_unit_id != new_unit_id if old_unit_id else False
    }


@app.get("/api/invoices/needing-review")
async def get_invoices_needing_review(
    request: Request,
    limit: int = Query(100, ge=1, le=1000),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get invoices that need unit mapping review."""
    tenant_id = get_tenant_id(user, request)
    
    from app.batch_unit_matcher import get_invoices_needing_review
    invoices = get_invoices_needing_review(session, tenant_id, limit=limit)
    
    return {
        "count": len(invoices),
        "invoices": invoices
    }


@app.get("/api/invoices/{invoice_id}", response_model=InvoiceWithValidationResponse)
def get_invoice(
    invoice_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get a single invoice with its validation results."""
    query = session.query(Invoice).filter(Invoice.id == invoice_id)
    query = filter_by_tenant(query, Invoice, user, request)
    invoice = query.first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    validation = session.query(InvoiceValidation).filter(
        InvoiceValidation.invoice_id == invoice.id
    ).first()
    
    # Convert to response models
    try:
        invoice_data = InvoiceResponse.model_validate(invoice)
    except:
        invoice_data = InvoiceResponse.from_orm(invoice)
    
    validation_data = None
    if validation:
        try:
            validation_data = InvoiceValidationResponse.model_validate(validation)
        except:
            validation_data = InvoiceValidationResponse.from_orm(validation)
    
    return InvoiceWithValidationResponse(
        invoice=invoice_data,
        validation=validation_data
    )


@app.delete("/api/invoices/bulk")
def bulk_delete_invoices(
    request: Request,
    invoice_ids: List[int] = Body(...),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Delete multiple invoices and their validation results.
    
    This endpoint allows users to delete multiple invoices at once.
    All invoices and their associated validation data will be permanently removed.
    """
    if not invoice_ids:
        raise HTTPException(status_code=400, detail="No invoice IDs provided")
    
    try:
        deleted_count = 0
        failed_count = 0
        deleted_invoice_numbers = []
        
        # Get tenant_id for filtering
        tenant_id = get_tenant_id(user, request)
        
        for invoice_id in invoice_ids:
            try:
                # Find invoice with tenant filtering
                query = session.query(Invoice).filter(Invoice.id == invoice_id)
                if tenant_id:
                    query = query.filter(Invoice.tenant_id == tenant_id)
                invoice = query.first()
                
                if not invoice:
                    failed_count += 1
                    continue
                
                # Delete associated InvoiceValidation first (foreign key constraint)
                # Use delete() with filter to ensure it's deleted even if not loaded
                session.query(InvoiceValidation).filter(
                    InvoiceValidation.invoice_id == invoice_id
                ).delete(synchronize_session=False)
                
                # Delete the invoice
                deleted_invoice_numbers.append(invoice.invoice_number)
                session.delete(invoice)
                deleted_count += 1
                
            except Exception as e:
                logger.error(f"Error deleting invoice {invoice_id}: {e}")
                failed_count += 1
                continue
        
        # Commit all deletions
        session.commit()
        
        logger.info(f"Bulk delete: {deleted_count} invoices deleted by user {user.email} (tenant_id: {tenant_id})")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "deleted_count": deleted_count,
                "failed_count": failed_count,
                "message": f"Successfully deleted {deleted_count} invoice(s)." + (f" {failed_count} failed." if failed_count > 0 else "")
            }
        )
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error in bulk delete: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=str(e) if str(e) else "An error occurred while deleting invoices. Please try again."
        )


@app.delete("/api/invoices/{invoice_id}")
def delete_invoice(
    invoice_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Delete an invoice and its validation results.
    
    This endpoint allows users to delete invoices they uploaded by mistake.
    The invoice and its associated validation data will be permanently removed.
    """
    try:
        # Find invoice with tenant filtering (ensures user can only delete their own invoices)
        query = session.query(Invoice).filter(Invoice.id == invoice_id)
        query = filter_by_tenant(query, Invoice, user, request)
        invoice = query.first()
        
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        # Delete associated InvoiceValidation first (foreign key constraint)
        # Use delete() with filter to ensure it's deleted even if not loaded
        session.query(InvoiceValidation).filter(
            InvoiceValidation.invoice_id == invoice_id
        ).delete(synchronize_session=False)
        
        # Flush to ensure validation deletion is processed before invoice deletion
        session.flush()
        
        # Delete the invoice
        session.delete(invoice)
        session.commit()
        
        logger.info(f"Invoice {invoice_id} deleted by user {user.email} (tenant_id: {get_tenant_id(user, request)})")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Invoice {invoice.invoice_number} has been deleted successfully."
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Error deleting invoice {invoice_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=str(e) if str(e) else "An error occurred while deleting the invoice. Please try again."
        )


@app.post("/api/validate")
def validate_invoices(
    request: ValidationRequest,
    http_request: Request,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Trigger validation for invoices."""
    try:
        # Generate unit timeline (with tenant filtering)
        tenant_id = get_tenant_id(user, http_request)
        generate_unit_timeline(session, tenant_id=tenant_id)
        
        # Get invoices to validate
        query = session.query(Invoice)
        query = filter_by_tenant(query, Invoice, user, http_request)
        if request.batch_number:
            query = query.filter(Invoice.source_batch == request.batch_number)
        
        invoices = query.all()
        
        validated_count = 0
        errors = []
        
        for invoice in invoices:
            try:
                # Check if validation exists
                existing = session.query(InvoiceValidation).filter(
                    InvoiceValidation.invoice_id == invoice.id
                ).first()
                
                if existing:
                    validation = validate_invoice(session, invoice)
                    validation.id = existing.id
                    session.merge(validation)
                else:
                    validation = validate_invoice(session, invoice)
                    session.add(validation)
                
                validated_count += 1
            except Exception as e:
                errors.append(f"Invoice #{invoice.invoice_number}: {str(e)}")
        
        session.commit()
        
        return {
            "status": "success",
            "validated_count": validated_count,
            "total_invoices": len(invoices),
            "errors": errors if errors else None
        }
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/upload/status/{batch_id}")
def get_upload_status(
    batch_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get upload status and errors for a batch."""
    tenant_id = get_tenant_id(user, request)
    query = session.query(UploadStatus).filter_by(batch_id=batch_id)
    if tenant_id:
        query = query.filter(UploadStatus.tenant_id == tenant_id)
    upload_status = query.first()
    
    if not upload_status:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    errors = None
    if upload_status.errors:
        try:
            import json
            errors = json.loads(upload_status.errors)
            # Ensure it's a list
            if not isinstance(errors, list):
                errors = [errors]
            
            # Sanitize any special characters in error messages
            if isinstance(errors, list):
                for i, error in enumerate(errors):
                    if isinstance(error, str):
                        # Replace any problematic characters
                        errors[i] = error.replace("✓", "").replace("✗", "X")
                    elif isinstance(error, dict):
                        for key, value in error.items():
                            if isinstance(value, str):
                                error[key] = value.replace("✓", "").replace("✗", "X")
        except:
            # Sanitize the error string
            if isinstance(upload_status.errors, str):
                errors = [upload_status.errors.replace("✓", "").replace("✗", "X")]
            else:
                errors = [str(upload_status.errors)]
    
    return {
        "batch_id": upload_status.batch_id,
        "file_name": upload_status.file_name,
        "status": upload_status.status,
        "total_rows": upload_status.total_rows,
        "invoices_created": upload_status.invoices_created,
        "errors": errors,
        "started_at": upload_status.started_at.isoformat() if upload_status.started_at else None,
        "completed_at": upload_status.completed_at.isoformat() if upload_status.completed_at else None
    }


@app.get("/api/export/invoices")
def export_invoices_csv(
    request: Request,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    status_filter: Optional[str] = Query(None, alias="status"),
    determination_filter: Optional[str] = Query(None, alias="determination"),
    batch_filter: Optional[str] = Query(None, alias="batch")
):
    """Export invoices to CSV."""
    from fastapi.responses import Response
    import csv
    from io import StringIO
    
    # Build query (same as invoices page)
    invoices_query = session.query(Invoice)
    
    # Apply tenant filtering
    invoices_query = filter_by_tenant(invoices_query, Invoice, user, request)
    
    # Apply filters - only join once if both status and determination filters are present
    if status_filter or determination_filter:
        invoices_query = invoices_query.join(InvoiceValidation, isouter=False)
        
        if status_filter:
            invoices_query = invoices_query.filter(
                InvoiceValidation.validation_status == status_filter
            )
        if determination_filter:
            invoices_query = invoices_query.filter(
                InvoiceValidation.determination == determination_filter
            )
    
    if batch_filter:
        invoices_query = invoices_query.filter(Invoice.source_batch == batch_filter)
    
    invoices = invoices_query.order_by(Invoice.created_at.desc()).all()
    
    # Create CSV
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Invoice Number', 'Supplier', 'Unit ID', 'Billing Period Start', 'Billing Period End',
        'Invoice Date', 'Gross Amount', 'Net Amount', 'VAT Amount', 'Utility Type', 'Currency',
        'Validation Status', 'Determination', 'Daily Rate', 'Vacancy Overlap Days', 'Is Duplicate', 'Batch'
    ])
    
    # Write rows
    for invoice in invoices:
        validation = session.query(InvoiceValidation).filter(
            InvoiceValidation.invoice_id == invoice.id
        ).first()
        
        writer.writerow([
            invoice.invoice_number,
            invoice.supplier_name,
            invoice.unit_id,
            invoice.billing_period_start,
            invoice.billing_period_end,
            invoice.invoice_date or '',
            invoice.gross_amount,
            invoice.net_amount or '',
            invoice.vat_amount or '',
            invoice.utility_type,
            invoice.currency,
            validation.validation_status if validation else '',
            validation.determination if validation else '',
            validation.daily_rate if validation and validation.daily_rate else '',
            validation.total_vacancy_overlap_days if validation else '',
            validation.is_duplicate if validation else '',
            invoice.source_batch or ''
        ])
    
    # Return CSV file
    filename = f"invoices_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ============================================================================
# Units API Endpoints
# ============================================================================

@app.post("/api/units")
def create_unit(
    request: Request,
    unit_data: dict = Body(...),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Create a new unit."""
    tenant_id = get_tenant_id(user, request)
    
    # Check if unit_id already exists
    existing_unit = session.query(Unit).filter(
        Unit.unit_id == unit_data.get("unit_id"),
        Unit.tenant_id == tenant_id
    ).first()
    
    if existing_unit:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": f"Unit with ID '{unit_data.get('unit_id')}' already exists"}
        )
    
    try:
        new_unit = Unit(
            tenant_id=tenant_id,
            unit_id=unit_data.get("unit_id"),
            building_name=unit_data.get("building_name"),
            address_line_1=unit_data.get("address_line_1"),
            address_line_2=unit_data.get("address_line_2"),
            city=unit_data.get("city"),
            postcode=unit_data.get("postcode"),
            created_at=datetime.utcnow(),
            created_by_user_id=user.id
        )
        session.add(new_unit)
        session.commit()
        
        return {"success": True, "unit_id": new_unit.id}
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating unit: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": "Failed to create unit", "detail": str(e)}
        )

@app.get("/api/units/{unit_id}")
def get_unit(
    unit_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get a single unit by ID."""
    tenant_id = get_tenant_id(user, request)
    if not tenant_id and not user.is_super_admin:
        raise HTTPException(status_code=403, detail="User must be associated with a tenant")
    
    unit = session.query(Unit).filter(Unit.id == unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    # Check tenant access
    if tenant_id and unit.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "id": unit.id,
        "unit_id": unit.unit_id,
        "building_name": unit.building_name,
        "address_line_1": unit.address_line_1,
        "address_line_2": unit.address_line_2,
        "city": unit.city,
        "postcode": unit.postcode
    }


@app.put("/api/units/{unit_id}")
def update_unit(
    unit_id: int,
    request: Request,
    unit_data: dict = Body(...),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Update a unit."""
    tenant_id = get_tenant_id(user, request)
    if not tenant_id and not user.is_super_admin:
        raise HTTPException(status_code=403, detail="User must be associated with a tenant")
    
    unit = session.query(Unit).filter(Unit.id == unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    # Check tenant access
    if tenant_id and unit.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Update fields
    if "unit_id" in unit_data:
        unit.unit_id = unit_data["unit_id"]
    if "building_name" in unit_data:
        unit.building_name = unit_data["building_name"]
    if "address_line_1" in unit_data:
        unit.address_line_1 = unit_data["address_line_1"]
    if "address_line_2" in unit_data:
        unit.address_line_2 = unit_data["address_line_2"]
    if "city" in unit_data:
        unit.city = unit_data["city"]
    if "postcode" in unit_data:
        unit.postcode = unit_data["postcode"]
    
    session.commit()
    
    return {"success": True, "message": "Unit updated successfully"}


@app.delete("/api/units/bulk")
def bulk_delete_units(
    request: Request,
    unit_ids: List[int] = Body(...),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Delete multiple units and their associated leases."""
    if not unit_ids:
        raise HTTPException(status_code=400, detail="No unit IDs provided")
    
    tenant_id = get_tenant_id(user, request)
    if not tenant_id and not user.is_super_admin:
        raise HTTPException(status_code=403, detail="User must be associated with a tenant")
    
    try:
        deleted_count = 0
        failed_count = 0
        deleted_unit_ids = []
        tenant_ids_to_regenerate = set()
        
        for unit_id in unit_ids:
            try:
                unit = session.query(Unit).filter(Unit.id == unit_id).first()
                if not unit:
                    failed_count += 1
                    continue
                
                # Check tenant access
                if tenant_id and unit.tenant_id != tenant_id:
                    failed_count += 1
                    continue
                
                # Delete associated leases
                session.query(Lease).filter(Lease.unit_id == unit.unit_id, Lease.tenant_id == unit.tenant_id).delete()
                
                # Delete unit timeline entries
                session.query(UnitTimeline).filter(UnitTimeline.unit_id == unit.unit_id, UnitTimeline.tenant_id == unit.tenant_id).delete()
                
                # Track tenant_id for timeline regeneration
                tenant_ids_to_regenerate.add(unit.tenant_id)
                
                # Delete the unit
                deleted_unit_ids.append(unit.unit_id)
                session.delete(unit)
                deleted_count += 1
                
            except Exception as e:
                logger.error(f"Error deleting unit {unit_id}: {e}")
                failed_count += 1
                continue
        
        # Commit all deletions
        session.commit()
        
        # Regenerate timelines for affected tenants
        for tid in tenant_ids_to_regenerate:
            try:
                generate_unit_timeline(session, tenant_id=tid)
            except:
                pass
        
        logger.info(f"Bulk delete: {deleted_count} units deleted by user {user.email} (tenant_id: {tenant_id})")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "deleted_count": deleted_count,
                "failed_count": failed_count,
                "message": f"Successfully deleted {deleted_count} unit(s)." + (f" {failed_count} failed." if failed_count > 0 else "")
            }
        )
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error in bulk delete units: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=str(e) if str(e) else "An error occurred while deleting units. Please try again."
        )


@app.delete("/api/units/{unit_id}")
def delete_unit(
    unit_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Delete a unit and all associated leases."""
    tenant_id = get_tenant_id(user, request)
    if not tenant_id and not user.is_super_admin:
        raise HTTPException(status_code=403, detail="User must be associated with a tenant")
    
    unit = session.query(Unit).filter(Unit.id == unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    # Check tenant access
    if tenant_id and unit.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Delete associated leases
    session.query(Lease).filter(Lease.unit_id == unit.unit_id, Lease.tenant_id == unit.tenant_id).delete()
    
    # Delete unit timeline entries
    session.query(UnitTimeline).filter(UnitTimeline.unit_id == unit.unit_id, UnitTimeline.tenant_id == unit.tenant_id).delete()
    
    # Delete the unit
    session.delete(unit)
    session.commit()
    
    # Regenerate timelines for remaining units
    try:
        generate_unit_timeline(session, tenant_id=unit.tenant_id)
    except:
        pass
    
    return {"success": True, "message": "Unit deleted successfully"}


# ============================================================================
# Leases API Endpoints
# ============================================================================

@app.get("/api/leases/{lease_id}")
def get_lease(
    lease_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get a single lease by ID."""
    tenant_id = get_tenant_id(user, request)
    if not tenant_id and not user.is_super_admin:
        raise HTTPException(status_code=403, detail="User must be associated with a tenant")
    
    lease = session.query(Lease).filter(Lease.id == lease_id).first()
    if not lease:
        raise HTTPException(status_code=404, detail="Lease not found")
    
    # Check tenant access
    if tenant_id and lease.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "id": lease.id,
        "unit_id": lease.unit_id,
        "tenant_name": lease.tenant_name,
        "lease_start": lease.lease_start.isoformat() if lease.lease_start else None,
        "lease_end": lease.lease_end.isoformat() if lease.lease_end else None
    }


@app.put("/api/leases/{lease_id}")
def update_lease(
    lease_id: int,
    request: Request,
    lease_data: dict = Body(...),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Update a lease."""
    tenant_id = get_tenant_id(user, request)
    if not tenant_id and not user.is_super_admin:
        raise HTTPException(status_code=403, detail="User must be associated with a tenant")
    
    lease = session.query(Lease).filter(Lease.id == lease_id).first()
    if not lease:
        raise HTTPException(status_code=404, detail="Lease not found")
    
    # Check tenant access
    if tenant_id and lease.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Validate unit_id exists
    if "unit_id" in lease_data:
        unit = session.query(Unit).filter(
            Unit.unit_id == lease_data["unit_id"],
            Unit.tenant_id == lease.tenant_id
        ).first()
        if not unit:
            raise HTTPException(status_code=400, detail=f"Unit {lease_data['unit_id']} not found")
        lease.unit_id = lease_data["unit_id"]
    
    # Update fields
    if "tenant_name" in lease_data:
        lease.tenant_name = lease_data["tenant_name"]
    if "lease_start" in lease_data:
        lease.lease_start = datetime.strptime(lease_data["lease_start"], "%Y-%m-%d").date()
    if "lease_end" in lease_data:
        if lease_data["lease_end"]:
            lease.lease_end = datetime.strptime(lease_data["lease_end"], "%Y-%m-%d").date()
        else:
            lease.lease_end = None
    
    session.commit()
    
    # Regenerate unit timelines
    try:
        generate_unit_timeline(session, tenant_id=lease.tenant_id)
    except:
        pass
    
    return {"success": True, "message": "Lease updated successfully"}


@app.delete("/api/leases/bulk")
def bulk_delete_leases(
    request: Request,
    lease_ids: List[int] = Body(...),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Delete multiple leases."""
    if not lease_ids:
        raise HTTPException(status_code=400, detail="No lease IDs provided")
    
    tenant_id = get_tenant_id(user, request)
    if not tenant_id and not user.is_super_admin:
        raise HTTPException(status_code=403, detail="User must be associated with a tenant")
    
    try:
        deleted_count = 0
        failed_count = 0
        tenant_ids_to_regenerate = set()
        
        for lease_id in lease_ids:
            try:
                lease = session.query(Lease).filter(Lease.id == lease_id).first()
                if not lease:
                    failed_count += 1
                    continue
                
                # Check tenant access
                if tenant_id and lease.tenant_id != tenant_id:
                    failed_count += 1
                    continue
                
                # Track tenant_id for timeline regeneration
                tenant_ids_to_regenerate.add(lease.tenant_id)
                
                # Delete the lease
                session.delete(lease)
                deleted_count += 1
                
            except Exception as e:
                logger.error(f"Error deleting lease {lease_id}: {e}")
                failed_count += 1
                continue
        
        # Commit all deletions
        session.commit()
        
        # Regenerate unit timelines for affected tenants
        for tid in tenant_ids_to_regenerate:
            try:
                generate_unit_timeline(session, tenant_id=tid)
            except:
                pass
        
        logger.info(f"Bulk delete: {deleted_count} leases deleted by user {user.email} (tenant_id: {tenant_id})")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "deleted_count": deleted_count,
                "failed_count": failed_count,
                "message": f"Successfully deleted {deleted_count} lease(s)." + (f" {failed_count} failed." if failed_count > 0 else "")
            }
        )
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error in bulk delete leases: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=str(e) if str(e) else "An error occurred while deleting leases. Please try again."
        )


@app.post("/api/leases")
def create_lease(
    request: Request,
    lease_data: dict = Body(...),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Create a new lease."""
    tenant_id = get_tenant_id(user, request)
    
    # Check if unit exists
    unit_id = lease_data.get("unit_id")
    unit = session.query(Unit).filter(
        Unit.unit_id == unit_id,
        Unit.tenant_id == tenant_id
    ).first()
    
    if not unit:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": f"Unit with ID '{unit_id}' not found"}
        )
    
    # Parse dates
    try:
        lease_start = datetime.strptime(lease_data.get("lease_start"), "%Y-%m-%d").date()
        lease_end = None
        if lease_data.get("lease_end"):
            lease_end = datetime.strptime(lease_data.get("lease_end"), "%Y-%m-%d").date()
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "Invalid date format. Use YYYY-MM-DD."}
        )
    
    try:
        new_lease = Lease(
            tenant_id=tenant_id,
            unit_id=unit_id,
            tenant_name=lease_data.get("tenant_name"),
            lease_start=lease_start,
            lease_end=lease_end,
            created_at=datetime.utcnow(),
            created_by_user_id=user.id
        )
        session.add(new_lease)
        session.commit()
        
        # Regenerate unit timeline
        from app.validation import generate_unit_timeline
        generate_unit_timeline(session, tenant_id=tenant_id, unit_id=unit_id)
        
        return {"success": True, "lease_id": new_lease.id}
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating lease: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": "Failed to create lease", "detail": str(e)}
        )


@app.delete("/api/leases/{lease_id}")
def delete_lease(
    lease_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Delete a lease."""
    tenant_id = get_tenant_id(user, request)
    if not tenant_id and not user.is_super_admin:
        raise HTTPException(status_code=403, detail="User must be associated with a tenant")
    
    lease = session.query(Lease).filter(Lease.id == lease_id).first()
    if not lease:
        raise HTTPException(status_code=404, detail="Lease not found")
    
    # Check tenant access
    if tenant_id and lease.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    lease_tenant_id = lease.tenant_id
    session.delete(lease)
    session.commit()
    
    # Regenerate unit timelines
    try:
        generate_unit_timeline(session, tenant_id=lease_tenant_id)
    except:
        pass
    
    return {"success": True, "message": "Lease deleted successfully"}


# ============================================================================
# Settings API Endpoints
# ============================================================================

@app.get("/api/settings/column-mappings")
def get_column_mappings(
    request: Request,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get column mapping configuration for current tenant."""
    tenant_id = get_tenant_id(user, request)
    if not tenant_id and not user.is_super_admin:
        raise HTTPException(status_code=403, detail="User must be associated with a tenant")
    
    tenant = session.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Parse config or return defaults
    from app.column_mapping import DEFAULT_INVOICE_MAPPING, DEFAULT_UNIT_MAPPING, DEFAULT_LEASE_MAPPING
    
    mappings = {
        "invoice": DEFAULT_INVOICE_MAPPING,
        "unit": DEFAULT_UNIT_MAPPING,
        "lease": DEFAULT_LEASE_MAPPING
    }
    
    if tenant.column_mapping_config:
        try:
            import json
            config = json.loads(tenant.column_mapping_config)
            for mapping_type in ["invoice", "unit", "lease"]:
                if mapping_type in config:
                    mappings[mapping_type] = config[mapping_type]
        except:
            pass
    
    return {"mappings": mappings}


@app.post("/api/settings/column-mappings")
def save_column_mappings(
    request: Request,
    mappings_data: dict = Body(...),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Save column mapping configuration for current tenant."""
    from app.column_mapping import save_column_mapping
    
    tenant_id = get_tenant_id(user, request)
    if not tenant_id and not user.is_super_admin:
        raise HTTPException(status_code=403, detail="User must be associated with a tenant")
    
    mappings = mappings_data.get("mappings", {})
    
    # Save each mapping type
    for mapping_type, mapping in mappings.items():
        if mapping_type in ["invoice", "unit", "lease"]:
            save_column_mapping(session, tenant_id, mapping_type, mapping)
    
    return {"success": True, "message": "Column mappings saved successfully"}


@app.post("/api/sync/horizon")
def sync_from_horizon_endpoint(
    request: Request,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Trigger manual sync from Horizon API."""
    from app.horizon_connector import sync_from_horizon
    
    tenant_id = get_tenant_id(user, request)
    if not tenant_id and not user.is_super_admin:
        raise HTTPException(status_code=403, detail="User must be associated with a tenant")
    
    tenant = session.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Get Horizon config from tenant (for now, placeholder)
    # TODO: Read from tenant.data_source_config
    # For now, return placeholder
    return {
        "success": False,
        "error": "Horizon configuration not set up. Please configure in Settings first."
    }


@app.get("/api/tenants")
def list_tenants(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """List all tenants (for super admin) or user's tenant."""
    if user.is_super_admin:
        tenants = session.query(Tenant).filter(Tenant.is_active == True).order_by(Tenant.name).all()
    else:
        if user.tenant_id:
            tenants = [session.query(Tenant).filter(Tenant.id == user.tenant_id).first()]
        else:
            tenants = []
    
    return [{"id": t.id, "name": t.name, "slug": t.slug} for t in tenants if t]


@app.post("/api/switch-tenant")
def switch_tenant(
    request: Request,
    data: dict = Body(...),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Switch tenant context (for super admin only)."""
    if not user.is_super_admin:
        raise HTTPException(status_code=403, detail="Only super admins can switch tenants")
    
    tenant_id = data.get("tenant_id")
    
    if tenant_id:
        tenant = session.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        request.session["tenant_id"] = tenant_id
    else:
        # Clear tenant (view all)
        request.session.pop("tenant_id", None)
    
    return {"status": "success", "tenant_id": tenant_id}


@app.get("/api/stats")
def get_stats(
    request: Request,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get validation statistics."""
    tenant_id = get_tenant_id(user, request)
    
    # Get statistics (with tenant filtering)
    invoice_query = session.query(Invoice)
    if tenant_id:
        invoice_query = invoice_query.filter(Invoice.tenant_id == tenant_id)
    total_invoices = invoice_query.count()
    
    validation_query = session.query(InvoiceValidation)
    if tenant_id:
        validation_query = validation_query.filter(InvoiceValidation.tenant_id == tenant_id)
    validated_invoices = validation_query.count()
    
    # Status breakdown (with tenant filtering)
    status_query = session.query(
        InvoiceValidation.validation_status,
        func.count(InvoiceValidation.id).label('count')
    )
    if tenant_id:
        status_query = status_query.filter(InvoiceValidation.tenant_id == tenant_id)
    status_counts = status_query.group_by(InvoiceValidation.validation_status).all()
    
    # Determination breakdown (with tenant filtering)
    determination_query = session.query(
        InvoiceValidation.determination,
        func.count(InvoiceValidation.id).label('count')
    )
    if tenant_id:
        determination_query = determination_query.filter(InvoiceValidation.tenant_id == tenant_id)
    determination_counts = determination_query.group_by(InvoiceValidation.determination).all()
    
    return {
        "total_invoices": total_invoices,
        "validated_invoices": validated_invoices,
        "unvalidated_invoices": total_invoices - validated_invoices,
        "status_breakdown": {status: count for status, count in status_counts},
        "determination_breakdown": {determination: count for determination, count in determination_counts}
    }


# ============================================================================
# Web UI Endpoints
# ============================================================================

@app.get("/invoices", response_class=HTMLResponse)
def invoices_page(
    request: Request,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    status_filter: Optional[str] = Query(None, alias="status"),
    determination_filter: Optional[str] = Query(None, alias="determination"),
    batch_filter: Optional[str] = Query(None, alias="batch"),
    search: Optional[str] = Query(None, alias="q")
):
    """Web UI page to view invoices with filters."""
    # Auto-validate any invoices that haven't been validated yet
    tenant_id = get_tenant_id(user, request)
    
    # Find invoices without validations
    unvalidated_invoices = session.query(Invoice).outerjoin(
        InvoiceValidation, Invoice.id == InvoiceValidation.invoice_id
    ).filter(
        InvoiceValidation.id == None
    )
    
    # Apply tenant filtering to unvalidated invoices
    unvalidated_invoices = filter_by_tenant(unvalidated_invoices, Invoice, user, request)
    
    # Get the count of unvalidated invoices
    unvalidated_count = unvalidated_invoices.count()
    
    # Auto-validate if there are any unvalidated invoices (up to 100 at a time to prevent timeouts)
    if unvalidated_count > 0:
        try:
            # Generate unit timeline for accurate validation
            generate_unit_timeline(session, tenant_id=tenant_id)
            
            # Validate up to 100 invoices
            invoices_to_validate = unvalidated_invoices.limit(100).all()
            validated_count = 0
            
            for invoice in invoices_to_validate:
                try:
                    validation = validate_invoice(session, invoice)
                    session.add(validation)
                    validated_count += 1
                except Exception as e:
                    logger.error(f"Error auto-validating invoice {invoice.id}: {e}")
            
            session.commit()
            logger.info(f"Auto-validated {validated_count} invoices")
            
            # If there are more unvalidated invoices, inform the user
            remaining = unvalidated_count - validated_count
            if remaining > 0:
                logger.info(f"{remaining} invoices still need validation")
        except Exception as e:
            logger.error(f"Error during batch auto-validation: {e}")
            session.rollback()
    
    # Build query for display
    invoices_query = session.query(Invoice)
    
    # Apply tenant filtering
    invoices_query = filter_by_tenant(invoices_query, Invoice, user, request)
    
    # Apply search filter
    if search:
        search_term = f"%{search}%"
        invoices_query = invoices_query.filter(
            or_(
                Invoice.invoice_number.ilike(search_term),
                Invoice.supplier_name.ilike(search_term),
                Invoice.unit_id.ilike(search_term)
            )
        )
    
    # Apply filters - only join once if both status and determination filters are present
    if status_filter or determination_filter:
        invoices_query = invoices_query.join(InvoiceValidation, isouter=False)
        
        if status_filter:
            invoices_query = invoices_query.filter(
                InvoiceValidation.validation_status == status_filter
            )
        if determination_filter:
            invoices_query = invoices_query.filter(
                InvoiceValidation.determination == determination_filter
            )
    
    if batch_filter:
        invoices_query = invoices_query.filter(Invoice.source_batch == batch_filter)
    
    # Pagination
    page = int(request.query_params.get("page", 1))
    per_page = 50
    offset = (page - 1) * per_page
    
    # Get total count for pagination
    total_count = invoices_query.count()
    total_pages = (total_count + per_page - 1) // per_page  # Ceiling division
    
    # Get invoices with validation (paginated)
    invoices = invoices_query.order_by(Invoice.created_at.desc()).offset(offset).limit(per_page).all()
    
    invoices_with_validation = []
    for invoice in invoices:
        validation = session.query(InvoiceValidation).filter(
            InvoiceValidation.invoice_id == invoice.id
        ).first()
        invoices_with_validation.append({
            "invoice": invoice,
            "validation": validation
        })
    
    # Get stats (with tenant filtering)
    tenant_id = get_tenant_id(user, request)
    
    invoice_count_query = session.query(Invoice)
    if tenant_id:
        invoice_count_query = invoice_count_query.filter(Invoice.tenant_id == tenant_id)
    total_invoices = invoice_count_query.count()
    
    validation_count_query = session.query(InvoiceValidation)
    if tenant_id:
        validation_count_query = validation_count_query.filter(InvoiceValidation.tenant_id == tenant_id)
    validated_invoices = validation_count_query.count()
    
    # Get unique batches for filter (with tenant filtering)
    batch_query = session.query(Invoice.source_batch).distinct().filter(
        Invoice.source_batch.isnot(None)
    )
    if tenant_id:
        batch_query = batch_query.filter(Invoice.tenant_id == tenant_id)
    batches = batch_query.all()
    batch_list = [b[0] for b in batches if b[0]]
    
    # Get unique determinations for filter (with tenant filtering)
    determination_query = session.query(InvoiceValidation.determination).distinct()
    if tenant_id:
        determination_query = determination_query.filter(InvoiceValidation.tenant_id == tenant_id)
    determinations = determination_query.all()
    determination_list = [d[0] for d in determinations if d[0]]
    
    return templates.TemplateResponse("invoices.html", {
        "request": request,
        "user": user,
        "invoices": invoices_with_validation,
        "stats": {
            "total": total_invoices,
            "validated": validated_invoices
        },
        "filters": {
            "status": status_filter,
            "determination": determination_filter,
            "batch": batch_filter,
            "search": search
        },
        "batch_list": batch_list,
        "determination_list": determination_list,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total_count,
            "total_pages": total_pages,
            "has_prev": page > 1,
            "has_next": page < total_pages
        }
    })


@app.get("/invoice/{invoice_id}", response_class=HTMLResponse)
def invoice_detail_page(
    invoice_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Web UI page for single invoice details."""
    query = session.query(Invoice).filter(Invoice.id == invoice_id)
    query = filter_by_tenant(query, Invoice, user, request)
    invoice = query.first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    validation = session.query(InvoiceValidation).filter(
        InvoiceValidation.invoice_id == invoice.id
    ).first()
    
    # Automatically validate the invoice if it hasn't been validated yet
    if not validation:
        try:
            # Generate unit timeline for accurate validation
            tenant_id = get_tenant_id(user, request)
            generate_unit_timeline(session, tenant_id=tenant_id)
            
            # Validate the invoice
            validation = validate_invoice(session, invoice)
            session.add(validation)
            session.commit()
            logger.info(f"Auto-validated invoice {invoice.invoice_number} (ID: {invoice.id})")
        except Exception as e:
            logger.error(f"Error auto-validating invoice {invoice.id}: {e}")
    
    return templates.TemplateResponse("invoice_detail.html", {
        "request": request,
        "invoice": invoice,
        "validation": validation
    })

