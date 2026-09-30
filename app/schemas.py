"""Pydantic schemas for API request/response validation."""

from pydantic import BaseModel
from datetime import date, datetime
from decimal import Decimal
from typing import Optional


class InvoiceResponse(BaseModel):
    """Invoice response schema."""
    id: int
    invoice_number: str
    supplier_account_number: str  # Required field
    supplier_name: str
    unit_id: str
    address: Optional[str]  # Full address from invoice
    billing_period_start: date
    billing_period_end: date
    invoice_date: Optional[date]
    gross_amount: Decimal
    net_amount: Optional[Decimal]
    vat_amount: Optional[Decimal]
    utility_type: str
    currency: str
    source_batch: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class InvoiceValidationResponse(BaseModel):
    """Invoice validation response schema."""
    id: int
    invoice_id: int
    invoice_days: Optional[int]
    total_vacancy_overlap_days: int
    validation_status: str
    duplicate_batch: Optional[str]
    is_duplicate: str
    payment_status: Optional[str]
    daily_rate: Optional[Decimal]
    determination: str
    validated_at: datetime
    validation_notes: Optional[str]
    
    class Config:
        from_attributes = True


class InvoiceWithValidationResponse(BaseModel):
    """Invoice with its validation results."""
    invoice: InvoiceResponse
    validation: Optional[InvoiceValidationResponse]
    
    class Config:
        from_attributes = True


class ValidationRequest(BaseModel):
    """Request to validate invoices."""
    batch_number: Optional[str] = None  # If None, validates all invoices

