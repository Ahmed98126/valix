"""Authentication utilities for the invoice validator."""

from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Optional, Tuple

from app.db import get_session
from app.models import User, Tenant
from app.config import SESSION_TIMEOUT_HOURS


def get_current_user(
    request: Request,
    session: Session = Depends(get_session)
) -> User:
    """Get the current authenticated user from session."""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # Check session expiry
    last_activity = request.session.get("last_activity")
    if last_activity:
        try:
            last_activity_time = datetime.fromisoformat(last_activity)
            if datetime.utcnow() - last_activity_time > timedelta(hours=SESSION_TIMEOUT_HOURS):
                # Session expired - clear it
                request.session.clear()
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Session expired"
                )
        except (ValueError, TypeError):
            # Invalid timestamp, treat as expired
            request.session.clear()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired"
            )
    
    # Update last activity timestamp
    request.session["last_activity"] = datetime.utcnow().isoformat()
    
    user = session.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        # Clear session if user not found or inactive
        request.session.clear()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return user


def get_current_tenant(
    request: Request,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Optional[Tenant]:
    """Get the current tenant from session or user."""
    # Super admin can access any tenant via session
    if user.is_super_admin:
        tenant_id = request.session.get("tenant_id")
        if tenant_id:
            return session.query(Tenant).filter(Tenant.id == tenant_id).first()
        # If no tenant selected, return None (super admin can see all)
        return None
    
    # Regular users are tied to their tenant
    if user.tenant_id:
        return session.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    
    return None


def get_tenant_id(user: User, request: Request) -> Optional[int]:
    """Get tenant_id for query filtering."""
    # Super admin can access any tenant
    if user.is_super_admin:
        tenant_id = request.session.get("tenant_id")
        if tenant_id:
            return tenant_id
        # If no tenant selected, return None (will need special handling)
        return None
    
    # Regular users are tied to their tenant
    return user.tenant_id


def authenticate_user(session: Session, email: str, password: str, tenant_id: Optional[int] = None) -> Optional[User]:
    """Authenticate a user by email and password.
    
    Args:
        session: Database session
        email: User email
        password: User password
        tenant_id: Optional tenant ID for multi-tenant login
    
    Returns:
        User if authenticated, None otherwise
    """
    # For multi-tenant, check email + tenant_id combination
    if tenant_id:
        user = session.query(User).filter(
            User.email == email,
            User.tenant_id == tenant_id
        ).first()
    else:
        # Try to find user (for backward compatibility or super admin)
        user = session.query(User).filter(User.email == email).first()
    
    if not user:
        return None
    if not user.check_password(password):
        return None
    if not user.is_active:
        return None
    
    # Update last login
    user.last_login = datetime.utcnow()
    session.commit()
    
    return user


def create_user(
    session: Session, 
    email: str, 
    password: str, 
    full_name: Optional[str] = None,
    tenant_id: Optional[int] = None,
    is_super_admin: bool = False
) -> User:
    """Create a new user account.
    
    Args:
        session: Database session
        email: User email
        password: User password
        full_name: Optional full name
        tenant_id: Optional tenant ID (required unless super admin)
        is_super_admin: Whether user is super admin
    
    Returns:
        Created User
    """
    # Check if user already exists (within tenant for regular users, globally for super admin)
    if is_super_admin:
        existing = session.query(User).filter(User.email == email).first()
    else:
        if not tenant_id:
            raise ValueError("tenant_id is required for non-admin users")
        existing = session.query(User).filter(
            User.email == email,
            User.tenant_id == tenant_id
        ).first()
    
    if existing:
        raise ValueError("User with this email already exists")
    
    user = User(
        email=email,
        full_name=full_name,
        tenant_id=tenant_id if not is_super_admin else None,
        is_super_admin=is_super_admin,
        is_active=True
    )
    user.set_password(password)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def create_tenant(session: Session, name: str, slug: Optional[str] = None) -> Tenant:
    """Create a new tenant.
    
    Args:
        session: Database session
        name: Tenant name
        slug: Optional slug (auto-generated from name if not provided)
    
    Returns:
        Created Tenant
    """
    if not slug:
        # Generate slug from name
        slug = name.lower().replace(" ", "-").replace("_", "-")
        # Remove special characters
        slug = "".join(c for c in slug if c.isalnum() or c == "-")
    
    # Check if slug already exists
    existing = session.query(Tenant).filter(Tenant.slug == slug).first()
    if existing:
        raise ValueError(f"Tenant with slug '{slug}' already exists")
    
    tenant = Tenant(
        name=name,
        slug=slug,
        is_active=True
    )
    session.add(tenant)
    session.commit()
    session.refresh(tenant)
    return tenant

