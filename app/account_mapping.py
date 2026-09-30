"""Account mapping management module.

This module handles the mapping between supplier account numbers and units,
allowing for automatic matching of invoices to units based on account numbers.
"""

import pandas as pd
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models import InvoiceUnitMapping, Unit
from app.db import SessionLocal

logger = logging.getLogger(__name__)

def normalize_account_number(account_number: Optional[str]) -> Optional[str]:
    """
    Normalize account number by removing spaces and dashes.
    This ensures consistent formatting for matching.
    """
    if not account_number:
        return None
    return account_number.replace(" ", "").replace("-", "")


def get_unit_for_account(
    account_number: str,
    supplier_name: Optional[str] = None,
    tenant_id: int = None,
    session: Optional[Session] = None
) -> Optional[str]:
    """
    Find unit ID for a given account number.
    
    Args:
        account_number: The supplier account number to look up
        supplier_name: Optional supplier name for fallback matching
        tenant_id: Tenant ID for multi-tenant support
        session: Optional database session (creates one if not provided)
    
    Returns:
        Unit ID if found, None otherwise
    """
    if not account_number:
        return None
    
    # Normalize account number for consistent matching
    clean_account = normalize_account_number(account_number)
    
    # Use provided session or create a new one
    close_session = False
    if session is None:
        session = SessionLocal()
        close_session = True
    
    try:
        # Try matching with normalized account number
        mapping = session.query(InvoiceUnitMapping).filter(
            InvoiceUnitMapping.tenant_id == tenant_id,
            InvoiceUnitMapping.supplier_account_number.replace(" ", "").replace("-", "") == clean_account,
            InvoiceUnitMapping.is_active == True
        ).first()
        
        # If still not found and supplier name provided, try matching by supplier
        if not mapping and supplier_name:
            mapping = session.query(InvoiceUnitMapping).filter(
                InvoiceUnitMapping.tenant_id == tenant_id,
                InvoiceUnitMapping.supplier_name == supplier_name,
                InvoiceUnitMapping.is_active == True
            ).first()
        
        if mapping:
            return mapping.unit_id
        
        return None
    
    finally:
        # Close session if we created it
        if close_session:
            session.close()


def create_account_mapping(
    supplier_account_number: str,
    unit_id: str,
    tenant_id: int,
    supplier_name: Optional[str] = None,
    notes: Optional[str] = None,
    created_by_user_id: Optional[int] = None,
    session: Optional[Session] = None
) -> InvoiceUnitMapping:
    """
    Create new account-to-unit mapping.
    
    Args:
        supplier_account_number: The account number from invoice
        unit_id: The unit ID to map to
        tenant_id: Tenant ID for multi-tenant support
        supplier_name: Optional supplier name
        notes: Optional notes about the mapping
        created_by_user_id: Optional user ID who created this mapping
        session: Optional database session (creates one if not provided)
    
    Returns:
        Created InvoiceUnitMapping object
    """
    # Use provided session or create a new one
    close_session = False
    if session is None:
        session = SessionLocal()
        close_session = True
    
    try:
        # Check if unit exists
        unit = session.query(Unit).filter(
            Unit.tenant_id == tenant_id,
            Unit.unit_id == unit_id
        ).first()
        
        if not unit:
            raise ValueError(f"Unit with ID '{unit_id}' not found for tenant {tenant_id}")
        
        # Normalize account number for consistent storage and matching
        normalized_account = normalize_account_number(supplier_account_number)
        
        # Check if mapping already exists (using normalized account)
        existing = session.query(InvoiceUnitMapping).filter(
            InvoiceUnitMapping.tenant_id == tenant_id,
            # Compare normalized versions
            InvoiceUnitMapping.supplier_account_number.replace(" ", "").replace("-", "") == normalized_account
        ).first()
        
        if existing:
            # Update existing mapping
            existing.unit_id = unit_id
            existing.supplier_name = supplier_name
            existing.notes = notes
            existing.is_active = True
            
            if created_by_user_id:
                existing.created_by_user_id = created_by_user_id
            
            session.commit()
            logger.info(f"Updated mapping: {supplier_account_number} → {unit_id}")
            return existing
        else:
            # Create new mapping with normalized account number
            mapping = InvoiceUnitMapping(
                tenant_id=tenant_id,
                supplier_account_number=normalized_account,  # Store normalized version
                unit_id=unit_id,
                supplier_name=supplier_name,
                notes=notes,
                is_active=True,
                created_by_user_id=created_by_user_id
            )
            
            session.add(mapping)
            session.commit()
            logger.info(f"Created mapping: {supplier_account_number} → {unit_id}")
            return mapping
    
    finally:
        # Close session if we created it
        if close_session:
            session.close()


def delete_account_mapping(
    mapping_id: int,
    tenant_id: int,
    session: Optional[Session] = None
) -> bool:
    """
    Delete account mapping (soft delete by setting is_active=False).
    
    Args:
        mapping_id: ID of the mapping to delete
        tenant_id: Tenant ID for security check
        session: Optional database session
    
    Returns:
        True if successful, False otherwise
    """
    # Use provided session or create a new one
    close_session = False
    if session is None:
        session = SessionLocal()
        close_session = True
    
    try:
        # Find mapping
        mapping = session.query(InvoiceUnitMapping).filter(
            InvoiceUnitMapping.id == mapping_id,
            InvoiceUnitMapping.tenant_id == tenant_id
        ).first()
        
        if not mapping:
            logger.warning(f"Mapping {mapping_id} not found for tenant {tenant_id}")
            return False
        
        # Soft delete by setting is_active=False
        mapping.is_active = False
        session.commit()
        logger.info(f"Deleted mapping: {mapping.supplier_account_number} → {mapping.unit_id}")
        return True
    
    finally:
        # Close session if we created it
        if close_session:
            session.close()


def import_account_mappings(
    file_path: str,
    tenant_id: int,
    created_by_user_id: Optional[int] = None,
    session: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Import account mappings from Excel file.
    
    Expected columns:
    - supplier_name
    - supplier_account_number
    - unit_id
    - notes (optional)
    
    Args:
        file_path: Path to Excel file
        tenant_id: Tenant ID for multi-tenant support
        created_by_user_id: Optional user ID who created these mappings
        session: Optional database session
    
    Returns:
        Dictionary with import results
    """
    # Use provided session or create a new one
    close_session = False
    if session is None:
        session = SessionLocal()
        close_session = True
    
    try:
        # Read Excel file
        df = pd.read_excel(file_path)
        
        # Check required columns
        required_columns = ["supplier_account_number", "unit_id"]
        for col in required_columns:
            if col not in df.columns:
                return {
                    "success": False,
                    "message": f"Missing required column: {col}",
                    "created": 0,
                    "updated": 0,
                    "failed": 0
                }
        
        # Process rows
        created = 0
        updated = 0
        failed = 0
        errors = []
        
        for _, row in df.iterrows():
            try:
                # Get values
                account_number = str(row["supplier_account_number"])
                unit_id = str(row["unit_id"])
                supplier_name = row.get("supplier_name") if "supplier_name" in df.columns else None
                notes = row.get("notes") if "notes" in df.columns else None
                
                # Skip rows with empty account number or unit ID
                if pd.isna(account_number) or pd.isna(unit_id) or not account_number or not unit_id:
                    failed += 1
                    errors.append(f"Row {_ + 2}: Empty account number or unit ID")
                    continue
                
                # Check if unit exists
                unit = session.query(Unit).filter(
                    Unit.tenant_id == tenant_id,
                    Unit.unit_id == unit_id
                ).first()
                
                if not unit:
                    failed += 1
                    errors.append(f"Row {_ + 2}: Unit '{unit_id}' not found")
                    continue
                
                # Check if mapping exists
                existing = session.query(InvoiceUnitMapping).filter(
                    InvoiceUnitMapping.tenant_id == tenant_id,
                    InvoiceUnitMapping.supplier_account_number == account_number
                ).first()
                
                if existing:
                    # Update existing
                    existing.unit_id = unit_id
                    existing.supplier_name = supplier_name
                    existing.notes = notes
                    existing.is_active = True
                
                    if created_by_user_id:
                        existing.created_by_user_id = created_by_user_id
                    
                    updated += 1
                else:
                    # Create new
                    mapping = InvoiceUnitMapping(
                        tenant_id=tenant_id,
                        supplier_account_number=account_number,
                        unit_id=unit_id,
                        supplier_name=supplier_name,
                        notes=notes,
                        is_active=True,
                        created_by_user_id=created_by_user_id
                    )
                    session.add(mapping)
                    created += 1
            
            except Exception as e:
                failed += 1
                errors.append(f"Row {_ + 2}: {str(e)}")
        
        # Commit changes
        session.commit()
        
        return {
            "success": True,
            "message": f"Imported {created + updated} mappings ({created} created, {updated} updated, {failed} failed)",
            "created": created,
            "updated": updated,
            "failed": failed,
            "errors": errors
        }
    
    except Exception as e:
        logger.error(f"Error importing account mappings: {str(e)}")
        return {
            "success": False,
            "message": f"Error importing account mappings: {str(e)}",
            "created": 0,
            "updated": 0,
            "failed": 0
        }
    
    finally:
        # Close session if we created it
        if close_session:
            session.close()


def export_account_mappings(
    tenant_id: int,
    output_path: str,
    session: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Export account mappings to Excel file.
    
    Args:
        tenant_id: Tenant ID for multi-tenant support
        output_path: Path to save Excel file
        session: Optional database session
    
    Returns:
        Dictionary with export results
    """
    # Use provided session or create a new one
    close_session = False
    if session is None:
        session = SessionLocal()
        close_session = True
    
    try:
        # Get all active mappings for this tenant
        mappings = session.query(InvoiceUnitMapping).filter(
            InvoiceUnitMapping.tenant_id == tenant_id,
            InvoiceUnitMapping.is_active == True
        ).all()
        
        # Convert to DataFrame
        data = []
        for mapping in mappings:
            data.append({
                "supplier_name": mapping.supplier_name,
                "supplier_account_number": mapping.supplier_account_number,
                "unit_id": mapping.unit_id,
                "notes": mapping.notes
            })
        
        df = pd.DataFrame(data)
        
        # Save to Excel
        df.to_excel(output_path, index=False)
        
        return {
            "success": True,
            "message": f"Exported {len(mappings)} mappings to {output_path}",
            "count": len(mappings)
        }
    
    except Exception as e:
        logger.error(f"Error exporting account mappings: {str(e)}")
        return {
            "success": False,
            "message": f"Error exporting account mappings: {str(e)}",
            "count": 0
        }
    
    finally:
        # Close session if we created it
        if close_session:
            session.close()


def get_account_mappings(
    tenant_id: int,
    session: Optional[Session] = None
) -> List[InvoiceUnitMapping]:
    """
    Get all active account mappings for a tenant.
    
    Args:
        tenant_id: Tenant ID for multi-tenant support
        session: Optional database session
    
    Returns:
        List of InvoiceUnitMapping objects
    """
    # Use provided session or create a new one
    close_session = False
    if session is None:
        session = SessionLocal()
        close_session = True
    
    try:
        # Get all active mappings for this tenant
        mappings = session.query(InvoiceUnitMapping).filter(
            InvoiceUnitMapping.tenant_id == tenant_id,
            InvoiceUnitMapping.is_active == True
        ).all()
        
        return mappings
    
    finally:
        # Close session if we created it
        if close_session:
            session.close()


def create_mapping_template(output_path: str) -> Dict[str, Any]:
    """
    Create Excel template for account mappings.
    
    Args:
        output_path: Path to save Excel file
    
    Returns:
        Dictionary with result
    """
    try:
        # Create DataFrame with sample data
        df = pd.DataFrame({
            "supplier_name": ["British Gas", "E.ON", "Water Company"],
            "supplier_account_number": ["1234567890", "0987654321", "WATER001"],
            "unit_id": ["SHOP-001", "OFFICE-101", "UNIT-A5"],
            "notes": ["Main electricity account", "Office building", "Water supply"]
        })
        
        # Save to Excel
        df.to_excel(output_path, index=False)
        
        return {
            "success": True,
            "message": f"Created mapping template at {output_path}",
            "path": output_path
        }
    
    except Exception as e:
        logger.error(f"Error creating mapping template: {str(e)}")
        return {
            "success": False,
            "message": f"Error creating mapping template: {str(e)}",
            "path": None
        }