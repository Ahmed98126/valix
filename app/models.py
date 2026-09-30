"""SQLAlchemy models for the invoice validator."""

from datetime import date, datetime
from sqlalchemy import Column, Integer, String, Date, DateTime, Numeric, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, relationship
from passlib.context import CryptContext

Base = declarative_base()

# Import password reset token model (will be defined in password_reset.py)
# This import is here to ensure Base is available for password_reset.py

# Password hashing context - using pbkdf2_sha256 for better compatibility
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


class Tenant(Base):
    """Tenant/Client organization for multi-tenant support."""
    
    __tablename__ = "tenants"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True, index=True)
    slug = Column(String, nullable=False, unique=True, index=True)  # URL-friendly identifier
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Configuration
    column_mapping_config = Column(String, nullable=True)  # JSON string for column mappings
    
    def __repr__(self):
        return f"<Tenant(name='{self.name}', slug='{self.slug}')>"


class User(Base):
    """User account for authentication."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True)  # NULL for super admin
    is_active = Column(Boolean, default=True, nullable=False)
    is_super_admin = Column(Boolean, default=False, nullable=False)  # Can access all tenants
    email_verified = Column(Boolean, default=False, nullable=False)  # Email verification status
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # Unique constraint on email + tenant_id (same email can exist in different tenants)
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )
    
    def set_password(self, password: str):
        """Hash and set the password."""
        self.hashed_password = pwd_context.hash(password)
    
    def check_password(self, password: str) -> bool:
        """Check if the provided password matches."""
        return pwd_context.verify(password, self.hashed_password)
    
    def __repr__(self):
        return f"<User(email='{self.email}', tenant_id={self.tenant_id}, active={self.is_active})>"


class Unit(Base):
    """Commercial property unit (shop, office, etc.)."""
    
    __tablename__ = "units"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    unit_id = Column(String, nullable=False, index=True)  # Unique per tenant, not globally
    building_name = Column(String, nullable=True)
    address_line_1 = Column(String, nullable=True)
    address_line_2 = Column(String, nullable=True)
    city = Column(String, nullable=True)
    postcode = Column(String, nullable=True)
    
    # Unique constraint on tenant_id + unit_id (same unit_id can exist in different tenants)
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )
    
    def __repr__(self):
        return f"<Unit(tenant_id={self.tenant_id}, unit_id='{self.unit_id}', building='{self.building_name}')>"


class Lease(Base):
    """Lease period for a unit."""
    
    __tablename__ = "leases"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    unit_id = Column(String, nullable=False, index=True)  # References Unit.unit_id (within tenant)
    tenant_name = Column(String, nullable=True)
    lease_start = Column(Date, nullable=False)
    lease_end = Column(Date, nullable=True)  # None/null for ongoing leases
    
    def __repr__(self):
        return f"<Lease(tenant_id={self.tenant_id}, unit_id='{self.unit_id}', tenant='{self.tenant_name}', start={self.lease_start}, end={self.lease_end})>"


class Invoice(Base):
    """Invoice record from CSV or other sources."""
    
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    invoice_number = Column(String, nullable=False, index=True)
    supplier_account_number = Column(String, nullable=False)  # Supplier account number (e.g., E.ON account number) - REQUIRED
    supplier_name = Column(String, nullable=False)
    unit_id = Column(String, nullable=False, index=True)  # References Unit.unit_id (within tenant)
    address = Column(String, nullable=True)  # Full address from invoice (for PDF extraction)
    billing_period_start = Column(Date, nullable=False)
    billing_period_end = Column(Date, nullable=False)
    invoice_date = Column(Date, nullable=True)
    gross_amount = Column(Numeric(10, 2), nullable=False)
    net_amount = Column(Numeric(10, 2), nullable=True)
    vat_amount = Column(Numeric(10, 2), nullable=True)
    utility_type = Column(String, nullable=False)  # e.g., 'Electricity', 'Gas', 'Water'
    currency = Column(String, default="GBP", nullable=False)
    source_batch = Column(String, nullable=True)  # Batch identifier for the import
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Unique constraint on tenant_id + invoice_number + gross_amount (for duplicate detection within tenant)
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )
    
    def __repr__(self):
        return f"<Invoice(tenant_id={self.tenant_id}, invoice_number='{self.invoice_number}', unit_id='{self.unit_id}', amount={self.gross_amount})>"


class UnitTimeline(Base):
    """Timeline of occupied/vacant periods for units.
    
    This table is derived from Units + Leases and shows when each unit
    was occupied (by a lease) or vacant (gaps between leases, never-leased, etc.).
    """
    
    __tablename__ = "unit_timeline"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    unit_id = Column(String, nullable=False, index=True)  # References Unit.unit_id (within tenant)
    period_start = Column(Date, nullable=False, index=True)
    period_end = Column(Date, nullable=True, index=True)  # NULL means ongoing vacancy
    status = Column(String, nullable=False)  # 'occupied' or 'vacant'
    lease_id = Column(Integer, nullable=True)  # References Lease.id if occupied, NULL if vacant
    days_in_period = Column(Integer, nullable=True)  # Calculated days in this period
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<UnitTimeline(tenant_id={self.tenant_id}, unit_id='{self.unit_id}', {self.status}, {self.period_start} to {self.period_end})>"


class InvoiceValidation(Base):
    """Validation results for invoices.
    
    Stores the validation status, overlap calculations, and final determination
    for each invoice after running the validation engine.
    """
    
    __tablename__ = "invoice_validation"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False, unique=True, index=True)
    
    # Overlap calculations
    invoice_days = Column(Integer, nullable=True)  # Total days in invoice billing period
    total_vacancy_overlap_days = Column(Integer, default=0, nullable=False)  # Days overlapping with vacancy
    
    # Validation status
    validation_status = Column(String, nullable=False)  # 'Valid', 'Invalid', 'Needs Review'
    
    # Duplicate detection
    duplicate_batch = Column(String, nullable=True)  # Batch numbers where duplicate found
    is_duplicate = Column(String, default="No", nullable=False)  # 'Yes' or 'No'
    
    # Payment status (for future use)
    payment_status = Column(String, nullable=True)  # 'Paid', 'Unpaid', 'Part Paid'
    
    # Daily rate calculation
    daily_rate = Column(Numeric(10, 2), nullable=True)  # Gross amount / invoice days
    
    # Final determination
    determination = Column(String, nullable=False)  # e.g., 'OK TO PAY', 'DO NOT PAY', 'COT', etc.
    
    # Metadata
    validated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    validation_notes = Column(String, nullable=True)  # Additional notes or explanation
    
    def __repr__(self):
        return f"<InvoiceValidation(tenant_id={self.tenant_id}, invoice_id={self.invoice_id}, status={self.validation_status}, determination={self.determination})>"


class InvoiceUnitMapping(Base):
    """Custom mapping of supplier account numbers to units.
    
    Allows organizations to create their own mappings for invoices that
    can't be automatically matched. This is especially useful when:
    - Account numbers are consistent and map to specific units
    - Address matching is unreliable
    - Organizations have their own internal unit identifiers
    """
    
    __tablename__ = "invoice_unit_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    supplier_account_number = Column(String, nullable=False, index=True)  # The account number from invoice (normalized format)
    unit_id = Column(String, nullable=False, index=True)  # The unit_id to map to
    supplier_name = Column(String, nullable=True)  # Optional: supplier name for context
    is_active = Column(Boolean, default=True, nullable=False)  # Can disable mappings without deleting
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Who created this mapping
    notes = Column(String, nullable=True)  # Optional notes about the mapping
    
    # Unique constraint: one active mapping per tenant + account number
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )
    
    def __repr__(self):
        return f"<InvoiceUnitMapping(tenant_id={self.tenant_id}, account={self.supplier_account_number}, unit_id={self.unit_id})>"


class SupplierExtractionPattern(Base):
    """Extraction patterns for specific suppliers.
    
    Stores regex patterns and other extraction rules for specific suppliers,
    allowing for more accurate extraction of invoice data based on supplier-specific
    formats and layouts.
    
    Examples:
    - British Gas account number pattern: r'customer\s+reference\s+number[\s:]+([0-9\s-]{6,})'
    - E.ON billing period pattern: r'billing\s+period[\s:]+(\d{1,2}\s+[A-Za-z]{3}\s+\d{2})\s*[-–]\s*(\d{1,2}\s+[A-Za-z]{3}\s+\d{2})'
    """
    
    __tablename__ = "supplier_extraction_patterns"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True)  # NULL for global patterns
    supplier_name = Column(String, nullable=False, index=True)  # e.g., "British Gas", "E.ON"
    field_name = Column(String, nullable=False, index=True)  # e.g., "supplier_account_number", "billing_period_start"
    pattern_type = Column(String, nullable=False)  # e.g., "regex", "xpath", "table_cell"
    pattern_value = Column(String, nullable=False)  # The actual pattern (regex, xpath, etc.)
    priority = Column(Integer, default=0)  # Higher priority patterns are tried first
    is_active = Column(Boolean, default=True, nullable=False)  # Can disable patterns without deleting
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Who created this pattern
    notes = Column(String, nullable=True)  # Optional notes about the pattern
    
    def __repr__(self):
        return f"<SupplierExtractionPattern(supplier='{self.supplier_name}', field='{self.field_name}', type='{self.pattern_type}')>"


class ManualReviewQueue(Base):
    """Queue for invoices needing manual review.
    
    Stores PDF invoices that couldn't be automatically processed due to:
    - Low confidence in extracted data
    - Missing required fields
    - Ambiguous or conflicting data
    
    Users can review these invoices in the UI and manually correct the extracted data.
    """
    
    __tablename__ = "manual_review_queue"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    pdf_path = Column(String, nullable=False)  # Path to the PDF file
    original_filename = Column(String, nullable=True)  # Original filename for reference
    extracted_data = Column(String, nullable=True)  # JSON string of extracted data
    raw_data = Column(String, nullable=True)  # JSON string of raw Azure extraction
    confidence_scores = Column(String, nullable=True)  # JSON string of confidence scores
    status = Column(String, default="Pending", nullable=False)  # "Pending", "In Review", "Completed", "Failed"
    reviewed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Who reviewed this invoice
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    reviewed_at = Column(DateTime, nullable=True)  # When the review was completed
    notes = Column(String, nullable=True)  # Notes from the reviewer
    
    def __repr__(self):
        return f"<ManualReviewQueue(id={self.id}, tenant_id={self.tenant_id}, status='{self.status}')>"
