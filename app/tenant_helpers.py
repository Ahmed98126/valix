"""Helper functions for tenant filtering and management."""

from typing import Optional
from fastapi import Request
from sqlalchemy.orm import Query, Session
from sqlalchemy import and_

from app.models import User, Tenant


def get_tenant_filter(user: User, request: Request) -> Optional[int]:
    """Get tenant_id for query filtering.
    
    Returns:
        tenant_id if user should be filtered, None if super admin viewing all
    """
    # Super admin can access any tenant via session
    if user.is_super_admin:
        tenant_id = request.session.get("tenant_id")
        return tenant_id  # None means viewing all tenants
    
    # Regular users are tied to their tenant
    return user.tenant_id


def filter_by_tenant(query: Query, model_class, user: User, request: Request) -> Query:
    """Add tenant filtering to a query.
    
    Args:
        query: SQLAlchemy query
        model_class: Model class (must have tenant_id attribute)
        user: Current user
        request: FastAPI request
    
    Returns:
        Query with tenant filtering applied
    """
    tenant_id = get_tenant_filter(user, request)
    
    # If tenant_id is None and user is super admin, don't filter (show all)
    if tenant_id is None and user.is_super_admin:
        return query
    
    # If tenant_id is None and user is not super admin, this is an error
    if tenant_id is None:
        # Return empty query (no results)
        return query.filter(False)
    
    # Filter by tenant_id
    return query.filter(model_class.tenant_id == tenant_id)


def get_user_tenant(session: Session, user: User) -> Optional[Tenant]:
    """Get the tenant for a user."""
    if user.is_super_admin:
        return None  # Super admin doesn't have a tenant
    
    if user.tenant_id:
        return session.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    
    return None


