"""Unit tests for column mapping functionality."""

import pytest
from app.column_mapping import (
    get_column_mapping, 
    map_columns, 
    DEFAULT_INVOICE_MAPPING,
    DEFAULT_UNIT_MAPPING,
    DEFAULT_LEASE_MAPPING
)


class TestColumnMapping:
    """Test column mapping functionality."""
    
    def test_get_default_invoice_mapping(self, db_session, test_tenant):
        """Test getting default invoice column mapping."""
        mapping = get_column_mapping(db_session, test_tenant.id, "invoice")
        assert "invoice_number" in mapping
        assert "supplier_account_number" in mapping
        assert "supplier_name" in mapping
        assert "unit_id" in mapping
    
    def test_get_default_unit_mapping(self, db_session, test_tenant):
        """Test getting default unit column mapping."""
        mapping = get_column_mapping(db_session, test_tenant.id, "unit")
        assert "unit_id" in mapping
        assert "building_name" in mapping
        assert "address_line_1" in mapping
    
    def test_get_default_lease_mapping(self, db_session, test_tenant):
        """Test getting default lease column mapping."""
        mapping = get_column_mapping(db_session, test_tenant.id, "lease")
        assert "unit_id" in mapping
        assert "tenant_name" in mapping
        assert "lease_start" in mapping
    
    def test_map_columns_invoice(self):
        """Test mapping invoice columns."""
        df_columns = ["Invoice Number", "Account Number", "Supplier", "Unit ID", 
                     "Billing Start", "Billing End", "Amount", "Type"]
        
        mapped = map_columns(df_columns, DEFAULT_INVOICE_MAPPING)
        
        assert mapped["invoice_number"] == "Invoice Number"
        assert mapped["supplier_account_number"] == "Account Number"
        assert mapped["supplier_name"] == "Supplier"
        assert mapped["unit_id"] == "Unit ID"
    
    def test_map_columns_case_insensitive(self):
        """Test column mapping is case insensitive."""
        df_columns = ["INVOICE_NUMBER", "account_number", "Supplier Name"]
        
        mapped = map_columns(df_columns, DEFAULT_INVOICE_MAPPING)
        
        assert mapped["invoice_number"] == "INVOICE_NUMBER"
        assert mapped["supplier_account_number"] == "account_number"
        assert mapped["supplier_name"] == "Supplier Name"
    
    def test_map_columns_variations(self):
        """Test column mapping handles variations."""
        df_columns = ["Invoice #", "Account No", "Vendor", "Property ID"]
        
        mapped = map_columns(df_columns, DEFAULT_INVOICE_MAPPING)
        
        assert mapped["invoice_number"] == "Invoice #"
        assert mapped["supplier_account_number"] == "Account No"
        assert mapped["supplier_name"] == "Vendor"
        assert mapped["unit_id"] == "Property ID"
    
    def test_map_columns_supplier_account_number_variations(self):
        """Test supplier_account_number mapping variations."""
        variations = [
            "supplier_account_number",
            "supplier account number",
            "account_number",
            "account number",
            "account_no",
            "account no",
            "customer_account",
            "customer account"
        ]
        
        for col_name in variations:
            df_columns = [col_name, "invoice_number", "supplier_name"]
            mapped = map_columns(df_columns, DEFAULT_INVOICE_MAPPING)
            assert mapped["supplier_account_number"] == col_name
    
    def test_map_columns_missing_columns(self):
        """Test mapping when some columns are missing."""
        df_columns = ["Invoice Number", "Supplier"]  # Missing some required
        
        mapped = map_columns(df_columns, DEFAULT_INVOICE_MAPPING)
        
        # Should map what it can find
        assert mapped["invoice_number"] == "Invoice Number"
        assert mapped["supplier_name"] == "Supplier"
        # Missing columns won't be in mapping
        assert "unit_id" not in mapped or mapped.get("unit_id") is None
    
    def test_default_invoice_mapping_includes_account_number(self):
        """Test that default mapping includes supplier_account_number."""
        assert "supplier_account_number" in DEFAULT_INVOICE_MAPPING
        assert len(DEFAULT_INVOICE_MAPPING["supplier_account_number"]) > 0

