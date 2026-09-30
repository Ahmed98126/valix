"""Column mapping utilities for per-tenant Excel/CSV column configurations."""

import json
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.models import Tenant


# Default column mappings (fallback if tenant doesn't have custom config)
DEFAULT_INVOICE_MAPPING = {
    "invoice_number": ["invoice_number", "invoice number", "invoice #", "invoice_no", "invoice no", "inv_number", "inv number", "invoice_num", "invoice num"],
    "supplier_name": ["supplier_name", "supplier name", "supplier", "vendor", "vendor_name", "vendor name", "company", "company_name", "company name"],
    "supplier_account_number": ["supplier_account_number", "supplier account number", "account_number", "account number", "account", "account_no", "account no", "customer_account", "customer account", "account_id", "account id"],
    "unit_id": ["unit_id", "unit id", "unit", "property_id", "property id", "property", "property_code", "property code", "unit_code", "unit code"],
    "billing_period_start": ["billing_period_start", "billing period start", "period_start", "period start", "start_date", "start date", "bill_start", "bill start", "from_date", "from date"],
    "billing_period_end": ["billing_period_end", "billing period end", "period_end", "period end", "end_date", "end date", "bill_end", "bill end", "to_date", "to date"],
    "gross_amount": ["gross_amount", "gross amount", "amount", "total", "total_amount", "total amount", "invoice_amount", "invoice amount", "value"],
    "utility_type": ["utility_type", "utility type", "type", "utility", "service_type", "service type", "utility_category", "utility category"],
    "invoice_date": ["invoice_date", "invoice date", "date", "invoice_dt", "invoice dt", "issue_date", "issue date"],
    "net_amount": ["net_amount", "net amount", "net", "subtotal", "sub_total", "sub total"],
    "vat_amount": ["vat_amount", "vat amount", "vat", "tax", "tax_amount", "tax amount"],
    "currency": ["currency", "curr", "ccy"]
}

DEFAULT_UNIT_MAPPING = {
    "unit_id": ["unit_id", "unit id", "unit", "property_id", "property id", "property"],
    "building_name": ["building_name", "building name", "building", "property_name", "property name"],
    "address_line_1": ["address_line_1", "address line 1", "address1", "address_line1", "street_address", "street address", "address line 1"],
    "address_line_2": ["address_line_2", "address line 2", "address2", "address_line2"],
    "city": ["city"],
    "postcode": ["postcode", "post_code", "post code", "zip", "zipcode", "zip_code"]
}

DEFAULT_LEASE_MAPPING = {
    "unit_id": ["unit_id", "unit id", "unit", "property_id", "property id", "property"],
    "tenant_name": ["tenant_name", "tenant name", "tenant", "lessee", "occupant", "company_name", "company name"],
    "lease_start": ["lease_start", "lease start", "start_date", "start date", "lease_start_date", "lease start"],
    "lease_end": ["lease_end", "lease end", "end_date", "end date", "lease_end_date", "expiry_date", "expiry date", "lease end"]
}


def get_column_mapping(
    session: Session,
    tenant_id: Optional[int],
    mapping_type: str = "invoice"
) -> Dict[str, List[str]]:
    """
    Get column mapping configuration for a tenant.
    
    Args:
        session: Database session
        tenant_id: Tenant ID (None for default)
        mapping_type: Type of mapping ('invoice', 'unit', 'lease')
    
    Returns:
        Dictionary mapping target columns to list of possible source column names
    """
    # Get default mapping based on type
    default_mapping = {
        "invoice": DEFAULT_INVOICE_MAPPING,
        "unit": DEFAULT_UNIT_MAPPING,
        "lease": DEFAULT_LEASE_MAPPING
    }.get(mapping_type, DEFAULT_INVOICE_MAPPING)
    
    # If no tenant_id, return default
    if not tenant_id:
        return default_mapping
    
    # Get tenant config
    tenant = session.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant or not tenant.column_mapping_config:
        return default_mapping
    
    # Parse tenant config
    try:
        config = json.loads(tenant.column_mapping_config)
        
        # Get mapping for this type, or use default
        tenant_mapping = config.get(mapping_type, {})
        
        # Merge with default (tenant config overrides defaults)
        merged_mapping = default_mapping.copy()
        for target_col, source_cols in tenant_mapping.items():
            if isinstance(source_cols, list):
                merged_mapping[target_col] = source_cols
            elif isinstance(source_cols, str):
                merged_mapping[target_col] = [source_cols]
        
        return merged_mapping
    except (json.JSONDecodeError, KeyError, TypeError):
        # If config is invalid, return default
        return default_mapping


def map_columns(
    df_columns: List[str],
    column_mapping: Dict[str, List[str]]
) -> Dict[str, str]:
    """
    Map DataFrame columns to target columns based on mapping configuration.
    
    Args:
        df_columns: List of column names from the DataFrame
        column_mapping: Mapping configuration (target -> list of possible source names)
    
    Returns:
        Dictionary mapping target columns to actual DataFrame column names
    """
    mapped_cols = {}
    
    for target_col, possible_names in column_mapping.items():
        for col in df_columns:
            col_normalized = str(col).lower().strip()
            if col_normalized in [name.lower().strip() for name in possible_names]:
                mapped_cols[target_col] = col
                break
    
    return mapped_cols


def save_column_mapping(
    session: Session,
    tenant_id: int,
    mapping_type: str,
    mapping: Dict[str, List[str]]
) -> bool:
    """
    Save column mapping configuration for a tenant.
    
    Args:
        session: Database session
        tenant_id: Tenant ID
        mapping_type: Type of mapping ('invoice', 'unit', 'lease')
        mapping: Mapping configuration to save
    
    Returns:
        True if successful
    """
    tenant = session.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        return False
    
    # Get existing config or create new
    try:
        if tenant.column_mapping_config:
            config = json.loads(tenant.column_mapping_config)
        else:
            config = {}
    except json.JSONDecodeError:
        config = {}
    
    # Update config for this mapping type
    config[mapping_type] = mapping
    
    # Save back to tenant
    tenant.column_mapping_config = json.dumps(config)
    session.commit()
    
    return True


