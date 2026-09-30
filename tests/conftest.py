"""Pytest configuration and shared fixtures."""

import pytest
import os
import sys
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import Base, get_session
from app.models import User, Tenant, Invoice, InvoiceValidation, Unit, Lease
from main import app

# Test database strategy:
# - Unit tests: SQLite in-memory (fast, no external dependencies)
# - Integration tests: Use TEST_DATABASE_URL env var (Supabase test database) or SQLite fallback
# 
# For Supabase integration tests, set TEST_DATABASE_URL to your test Supabase connection string
# Example: TEST_DATABASE_URL=postgresql://user:pass@host:5432/test_db
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", 
    "sqlite:///:memory:"  # Default: in-memory SQLite for fast unit tests
)


@pytest.fixture(scope="session")
def test_engine():
    """
    Create test database engine.
    
    Strategy:
    - If TEST_DATABASE_URL is set (Supabase/PostgreSQL): Use it for integration tests
    - Otherwise: Use SQLite in-memory for fast unit tests
    """
    # Determine connection args based on database type
    if "sqlite" in TEST_DATABASE_URL:
        connect_args = {"check_same_thread": False}
    else:
        # PostgreSQL/Supabase connection args
        connect_args = {
            "connect_timeout": 10,
        }
    
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args=connect_args,
        pool_pre_ping=True if "postgresql" in TEST_DATABASE_URL else False
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    yield engine
    
    # Clean up: drop all tables
    Base.metadata.drop_all(bind=engine)
    
    # Note: For Supabase test database, tables are dropped but database remains
    # For SQLite in-memory, everything is automatically cleaned up


@pytest.fixture(scope="function")
def db_session(test_engine) -> Generator[Session, None, None]:
    """Create a fresh database session for each test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session) -> TestClient:
    """Create a test client with database session override."""
    def override_get_session():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_session] = override_get_session
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def test_tenant(db_session: Session) -> Tenant:
    """Create a test tenant."""
    tenant = Tenant(
        name="Test Company",
        slug="test-company"
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant


@pytest.fixture
def test_user(db_session: Session, test_tenant: Tenant) -> User:
    """Create a test user."""
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
    
    user = User(
        email="test@example.com",
        hashed_password=pwd_context.hash("password"),
        full_name="Test User",
        tenant_id=test_tenant.id,
        email_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def authenticated_client(client: TestClient, test_user: User) -> TestClient:
    """Create an authenticated test client."""
    # Login to get session
    response = client.post("/login", data={
        "email": test_user.email,
        "password": "password"
    })
    assert response.status_code in [200, 302]  # Redirect or success
    return client


@pytest.fixture
def sample_invoice_data():
    """Sample invoice data for testing."""
    return {
        "invoice_number": "TEST-INV-001",
        "supplier_account_number": "1234567890",
        "supplier_name": "British Gas",
        "unit_id": "SHOP-001",
        "billing_period_start": "2024-01-01",
        "billing_period_end": "2024-01-31",
        "gross_amount": "300.00",
        "utility_type": "Electricity"
    }


@pytest.fixture
def sample_pdf_extraction_data():
    """Sample Azure Document Intelligence extraction data."""
    return {
        "fields": {
            "InvoiceId": {"value": "ABC123ABC", "confidence": 0.95},
            "CustomerAccountNumber": {"value": "0123 4567 89", "confidence": 0.92},
            "VendorName": {"value": "e.on", "confidence": 0.90},
            "InvoiceTotal": {"value": "48.59", "confidence": 0.95},
            "InvoiceDate": {"value": "2014-02-18", "confidence": 0.88},
            "DueDate": {"value": "2014-03-18", "confidence": 0.85}
        },
        "content": """FFS/D2/S3
Date of bill
Tax invoice number
Page 1 of 2
e.on
18 February 2014
ABC123ABC
VAT registration number
Want to talk?
000 0000 00
Call us on
0345 055 0065
Monday to Friday 8.00am to 6.00pm
FXRB
Business name
Email us on
K
Street
business@eonenergy.com
City
Your account number
0123 4567 89
Post Code
Electricity bill
For electricity supplied to Street, City, Count, Post Code
Important information about
We have estimated your reading
your plan
Latest electricity reading 23303 estimated on 18 February 2014.
Please pay £48.59""",
        "tables": []
    }


@pytest.fixture
def test_unit(db_session: Session, test_tenant: Tenant) -> Unit:
    """Create a test unit."""
    unit = Unit(
        tenant_id=test_tenant.id,
        unit_id="SHOP-001",
        building_name="Test Building",
        address_line_1="123 Test Street",
        city="London",
        postcode="SW1A 1AA"
    )
    db_session.add(unit)
    db_session.commit()
    db_session.refresh(unit)
    return unit


@pytest.fixture
def test_lease(db_session: Session, test_unit: Unit) -> Lease:
    """Create a test lease."""
    from datetime import date
    lease = Lease(
        tenant_id=test_unit.tenant_id,
        unit_id=test_unit.unit_id,
        tenant_name="Test Tenant",
        lease_start=date(2024, 1, 1),
        lease_end=date(2024, 12, 31)
    )
    db_session.add(lease)
    db_session.commit()
    db_session.refresh(lease)
    return lease

