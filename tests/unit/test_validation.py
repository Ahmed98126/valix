"""Unit tests for validation logic."""

import pytest
from datetime import date
from decimal import Decimal
from app.validation import (
    calculate_invoice_days,
    calculate_daily_rate,
    check_date_overlap
)


class TestValidationLogic:
    """Test validation logic functions."""
    
    def test_calculate_invoice_days(self):
        """Test invoice days calculation."""
        from app.models import Invoice
        
        invoice = Invoice(
            billing_period_start=date(2024, 1, 1),
            billing_period_end=date(2024, 1, 31)
        )
        
        days = calculate_invoice_days(invoice)
        assert days == 31  # 31 days inclusive
    
    def test_calculate_daily_rate(self):
        """Test daily rate calculation."""
        from app.models import Invoice
        
        invoice = Invoice(
            billing_period_start=date(2024, 1, 1),
            billing_period_end=date(2024, 1, 31),
            gross_amount=Decimal("310.00")
        )
        
        rate = calculate_daily_rate(invoice)
        assert rate == Decimal("10.00")  # 310 / 31
    
    def test_check_date_overlap_full_overlap(self):
        """Test date overlap calculation - full overlap."""
        overlap = check_date_overlap(
            date(2024, 1, 1), date(2024, 1, 31),  # Invoice period
            date(2024, 1, 1), date(2024, 1, 31)   # Vacancy period
        )
        assert overlap == 31
    
    def test_check_date_overlap_partial_overlap(self):
        """Test date overlap calculation - partial overlap."""
        overlap = check_date_overlap(
            date(2024, 1, 1), date(2024, 1, 31),  # Invoice period
            date(2024, 1, 15), date(2024, 2, 15)  # Vacancy period
        )
        assert overlap == 17  # Days 15-31 = 17 days
    
    def test_check_date_overlap_no_overlap(self):
        """Test date overlap calculation - no overlap."""
        overlap = check_date_overlap(
            date(2024, 1, 1), date(2024, 1, 31),  # Invoice period
            date(2024, 2, 1), date(2024, 2, 28)   # Vacancy period
        )
        assert overlap == 0
    
    def test_check_date_overlap_ongoing_vacancy(self):
        """Test date overlap with ongoing vacancy (end_date = None)."""
        overlap = check_date_overlap(
            date(2024, 1, 1), date(2024, 1, 31),  # Invoice period
            date(2024, 1, 15), None               # Ongoing vacancy
        )
        assert overlap == 17  # Days 15-31 = 17 days
    
    def test_check_date_overlap_with_vacancy_periods(self):
        """Test date overlap calculation with vacancy periods."""
        # Test with single vacancy period
        overlap = check_date_overlap(
            date(2024, 1, 1), date(2024, 1, 31),  # Invoice period
            date(2024, 1, 1), date(2024, 1, 31)   # Vacancy period
        )
        assert overlap == 31  # Full overlap
    
    def test_check_date_overlap_multiple_periods(self):
        """Test date overlap with multiple periods (simulated)."""
        # Test first period
        overlap1 = check_date_overlap(
            date(2024, 1, 1), date(2024, 1, 31),  # Invoice period
            date(2024, 1, 1), date(2024, 1, 15)   # First vacancy period
        )
        assert overlap1 == 15
        
        # Test second period
        overlap2 = check_date_overlap(
            date(2024, 1, 1), date(2024, 1, 31),  # Invoice period
            date(2024, 1, 16), date(2024, 1, 31)  # Second vacancy period
        )
        assert overlap2 == 16
        
        # Total overlap would be 15 + 16 = 31
        assert overlap1 + overlap2 == 31
    
    @pytest.mark.parametrize("daily_rate,expected_determination", [
        (Decimal("3.00"), "OK TO PAY"),
        (Decimal("5.00"), "OK TO PAY, SUBMIT METER READING"),
        (Decimal("10.00"), "DO NOT PAY, SUBMIT METER READING"),
        (Decimal("15.00"), "DO NOT PAY, SUBMIT METER READING")
    ])
    def test_determination_by_daily_rate(self, daily_rate, expected_determination):
        """Test determination generation based on daily rate."""
        from app.models import Invoice
        from app.validation import generate_determination
        from datetime import date
        from decimal import Decimal
        
        invoice = Invoice(
            invoice_number="TEST-001",
            supplier_account_number="1234567890",
            supplier_name="British Gas",
            unit_id="SHOP-001",
            billing_period_start=date(2024, 1, 1),
            billing_period_end=date(2024, 1, 31),
            gross_amount=Decimal("300.00"),
            utility_type="Electricity"
        )
        
        determination = generate_determination(
            invoice=invoice,
            validation_status="Valid",
            payment_status="Unpaid",
            daily_rate=daily_rate,
            unit_id="SHOP-001"
        )
        
        assert expected_determination in determination
    
    def test_landlord_supply_determination(self):
        """Test landlord supply determination (unit ending in '00')."""
        from app.models import Invoice
        from app.validation import generate_determination
        from datetime import date
        from decimal import Decimal
        
        invoice = Invoice(
            invoice_number="TEST-001",
            supplier_account_number="1234567890",
            supplier_name="British Gas",
            unit_id="SHOP-100",  # Ends in '00'
            billing_period_start=date(2024, 1, 1),
            billing_period_end=date(2024, 1, 31),
            gross_amount=Decimal("300.00"),
            utility_type="Electricity"
        )
        
        determination = generate_determination(
            invoice=invoice,
            validation_status="Valid",
            payment_status="Unpaid",
            daily_rate=Decimal("5.00"),
            unit_id="SHOP-100"
        )
        
        assert "Landlord Supply" in determination
        assert "OK TO PAY" in determination

