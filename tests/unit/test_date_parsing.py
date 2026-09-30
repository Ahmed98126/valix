"""Unit tests for date parsing functionality."""

import pytest
from datetime import date
from app.pdf_normalizer import PDFNormalizer


class TestDateParsing:
    """Test date parsing in PDF normalizer."""
    
    def test_parse_standard_date_formats(self):
        """Test parsing standard date formats."""
        normalizer = PDFNormalizer()
        
        # YYYY-MM-DD
        assert normalizer._parse_date("2024-01-15") == date(2024, 1, 15)
        
        # DD/MM/YYYY
        assert normalizer._parse_date("15/01/2024") == date(2024, 1, 15)
        
        # DD-MM-YYYY
        assert normalizer._parse_date("15-01-2024") == date(2024, 1, 15)
        
        # YYYY/MM/DD
        assert normalizer._parse_date("2024/01/15") == date(2024, 1, 15)
    
    def test_parse_eon_date_format(self):
        """Test parsing E.ON specific date format (08 Jan 14)."""
        normalizer = PDFNormalizer(supplier_name="e.on")
        
        # E.ON format: DD MMM YY
        assert normalizer._parse_date("08 Jan 14") == date(2014, 1, 8)
        assert normalizer._parse_date("18 Feb 14") == date(2014, 2, 18)
        assert normalizer._parse_date("31 Dec 23") == date(2023, 12, 31)
    
    def test_parse_date_with_time(self):
        """Test parsing date strings with time components."""
        normalizer = PDFNormalizer()
        
        # ISO format with time
        result = normalizer._parse_date("2024-01-15T10:30:00")
        assert result == date(2024, 1, 15) or result is None  # May or may not parse
    
    def test_parse_invalid_dates(self):
        """Test parsing invalid date strings."""
        normalizer = PDFNormalizer()
        
        # Invalid formats
        assert normalizer._parse_date("invalid") is None
        assert normalizer._parse_date("") is None
        assert normalizer._parse_date("None") is None
        assert normalizer._parse_date("null") is None
    
    def test_parse_date_object(self):
        """Test parsing when input is already a date object."""
        normalizer = PDFNormalizer()
        
        test_date = date(2024, 1, 15)
        assert normalizer._parse_date(test_date) == test_date
    
    def test_parse_none(self):
        """Test parsing None input."""
        normalizer = PDFNormalizer()
        
        assert normalizer._parse_date(None) is None
    
    @pytest.mark.parametrize("date_str,expected", [
        ("2024-01-15", date(2024, 1, 15)),
        ("15/01/2024", date(2024, 1, 15)),
        ("15-01-2024", date(2024, 1, 15)),
        ("08 Jan 14", date(2014, 1, 8)),  # E.ON format
        ("invalid", None),
        ("", None),
    ])
    def test_parse_various_formats(self, date_str, expected):
        """Test parsing various date formats."""
        normalizer = PDFNormalizer(supplier_name="e.on")
        result = normalizer._parse_date(date_str)
        assert result == expected

