"""Supplier extraction pattern management.

This module provides functions to manage supplier-specific extraction patterns
for PDF invoice processing. These patterns allow for more accurate extraction
of invoice data based on supplier-specific formats and layouts.
"""

import json
import logging
import re
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple, Union
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.models import SupplierExtractionPattern
from app.db import SessionLocal

logger = logging.getLogger(__name__)


def get_supplier_patterns(
    supplier_name: str,
    field_name: Optional[str] = None,
    tenant_id: Optional[int] = None,
    include_inactive: bool = False,
    session: Optional[Session] = None
) -> List[SupplierExtractionPattern]:
    """
    Get extraction patterns for a specific supplier.
    
    Args:
        supplier_name: Name of the supplier (e.g., "British Gas", "E.ON")
        field_name: Optional field name to filter by (e.g., "supplier_account_number")
        tenant_id: Optional tenant ID for tenant-specific patterns
        include_inactive: Whether to include inactive patterns
        session: Optional database session
    
    Returns:
        List of SupplierExtractionPattern objects
    """
    # Use provided session or create a new one
    close_session = False
    if session is None:
        session = SessionLocal()
        close_session = True
    
    try:
        # Normalize supplier name for case-insensitive comparison
        supplier_name_lower = supplier_name.lower()
        
        # Build query
        query = session.query(SupplierExtractionPattern).filter(
            or_(
                # Exact match (case-insensitive)
                SupplierExtractionPattern.supplier_name.ilike(supplier_name),
                # Partial match for variations (e.g., "British Gas" matches "British Gas Trading Ltd")
                SupplierExtractionPattern.supplier_name.ilike(f"%{supplier_name}%"),
                # Match supplier name in supplier_name field
                supplier_name_lower.ilike(f"%{SupplierExtractionPattern.supplier_name}%")
            )
        )
        
        # Filter by field name if provided
        if field_name:
            query = query.filter(SupplierExtractionPattern.field_name == field_name)
        
        # Filter by tenant ID or global patterns (tenant_id IS NULL)
        if tenant_id:
            query = query.filter(
                or_(
                    SupplierExtractionPattern.tenant_id == tenant_id,  # Tenant-specific patterns
                    SupplierExtractionPattern.tenant_id.is_(None)  # Global patterns
                )
            )
        else:
            # If no tenant_id provided, only return global patterns
            query = query.filter(SupplierExtractionPattern.tenant_id.is_(None))
        
        # Filter by active status
        if not include_inactive:
            query = query.filter(SupplierExtractionPattern.is_active == True)
        
        # Order by priority (highest first), then by tenant_id (tenant-specific before global)
        patterns = query.order_by(
            SupplierExtractionPattern.priority.desc(),
            SupplierExtractionPattern.tenant_id.desc().nullslast()  # tenant-specific first
        ).all()
        
        return patterns
    
    finally:
        # Close session if we created it
        if close_session:
            session.close()


def create_supplier_pattern(
    supplier_name: str,
    field_name: str,
    pattern_type: str,
    pattern_value: str,
    tenant_id: Optional[int] = None,
    priority: int = 0,
    notes: Optional[str] = None,
    created_by_user_id: Optional[int] = None,
    session: Optional[Session] = None
) -> SupplierExtractionPattern:
    """
    Create a new supplier extraction pattern.
    
    Args:
        supplier_name: Name of the supplier (e.g., "British Gas", "E.ON")
        field_name: Field to extract (e.g., "supplier_account_number")
        pattern_type: Type of pattern (e.g., "regex", "xpath", "table_cell")
        pattern_value: The actual pattern (regex, xpath, etc.)
        tenant_id: Optional tenant ID for tenant-specific patterns
        priority: Priority of the pattern (higher = tried first)
        notes: Optional notes about the pattern
        created_by_user_id: Optional user ID who created the pattern
        session: Optional database session
    
    Returns:
        Created SupplierExtractionPattern object
    """
    # Use provided session or create a new one
    close_session = False
    if session is None:
        session = SessionLocal()
        close_session = True
    
    try:
        # Validate pattern based on type
        if pattern_type == "regex":
            try:
                re.compile(pattern_value)
            except re.error:
                raise ValueError(f"Invalid regex pattern: {pattern_value}")
        
        # Create pattern
        pattern = SupplierExtractionPattern(
            supplier_name=supplier_name,
            field_name=field_name,
            pattern_type=pattern_type,
            pattern_value=pattern_value,
            tenant_id=tenant_id,
            priority=priority,
            notes=notes,
            created_by_user_id=created_by_user_id
        )
        
        session.add(pattern)
        session.commit()
        
        logger.info(f"Created {pattern_type} pattern for {supplier_name} - {field_name}")
        return pattern
    
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating pattern: {str(e)}")
        raise
    
    finally:
        # Close session if we created it
        if close_session:
            session.close()


def update_supplier_pattern(
    pattern_id: int,
    supplier_name: Optional[str] = None,
    field_name: Optional[str] = None,
    pattern_type: Optional[str] = None,
    pattern_value: Optional[str] = None,
    priority: Optional[int] = None,
    is_active: Optional[bool] = None,
    notes: Optional[str] = None,
    session: Optional[Session] = None
) -> Optional[SupplierExtractionPattern]:
    """
    Update an existing supplier extraction pattern.
    
    Args:
        pattern_id: ID of the pattern to update
        supplier_name: Optional new supplier name
        field_name: Optional new field name
        pattern_type: Optional new pattern type
        pattern_value: Optional new pattern value
        priority: Optional new priority
        is_active: Optional new active status
        notes: Optional new notes
        session: Optional database session
    
    Returns:
        Updated SupplierExtractionPattern object or None if not found
    """
    # Use provided session or create a new one
    close_session = False
    if session is None:
        session = SessionLocal()
        close_session = True
    
    try:
        # Get pattern
        pattern = session.query(SupplierExtractionPattern).filter(
            SupplierExtractionPattern.id == pattern_id
        ).first()
        
        if not pattern:
            return None
        
        # Update fields if provided
        if supplier_name is not None:
            pattern.supplier_name = supplier_name
        
        if field_name is not None:
            pattern.field_name = field_name
        
        if pattern_type is not None:
            pattern.pattern_type = pattern_type
        
        if pattern_value is not None:
            # Validate pattern based on type
            if pattern.pattern_type == "regex":
                try:
                    re.compile(pattern_value)
                except re.error:
                    raise ValueError(f"Invalid regex pattern: {pattern_value}")
            
            pattern.pattern_value = pattern_value
        
        if priority is not None:
            pattern.priority = priority
        
        if is_active is not None:
            pattern.is_active = is_active
        
        if notes is not None:
            pattern.notes = notes
        
        session.commit()
        
        logger.info(f"Updated pattern {pattern_id}")
        return pattern
    
    except Exception as e:
        session.rollback()
        logger.error(f"Error updating pattern: {str(e)}")
        raise
    
    finally:
        # Close session if we created it
        if close_session:
            session.close()


def delete_supplier_pattern(
    pattern_id: int,
    session: Optional[Session] = None
) -> bool:
    """
    Delete a supplier extraction pattern.
    
    Args:
        pattern_id: ID of the pattern to delete
        session: Optional database session
    
    Returns:
        True if deleted, False if not found
    """
    # Use provided session or create a new one
    close_session = False
    if session is None:
        session = SessionLocal()
        close_session = True
    
    try:
        # Get pattern
        pattern = session.query(SupplierExtractionPattern).filter(
            SupplierExtractionPattern.id == pattern_id
        ).first()
        
        if not pattern:
            return False
        
        # Delete pattern
        session.delete(pattern)
        session.commit()
        
        logger.info(f"Deleted pattern {pattern_id}")
        return True
    
    except Exception as e:
        session.rollback()
        logger.error(f"Error deleting pattern: {str(e)}")
        raise
    
    finally:
        # Close session if we created it
        if close_session:
            session.close()


def import_patterns_from_excel(
    file_path: str,
    tenant_id: Optional[int] = None,
    created_by_user_id: Optional[int] = None,
    session: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Import supplier extraction patterns from Excel file.
    
    Expected columns:
    - Supplier Name (required)
    - Field Name (required)
    - Pattern Type (required)
    - Pattern Value (required)
    - Priority (optional)
    - Notes (optional)
    
    Args:
        file_path: Path to Excel file
        tenant_id: Optional tenant ID for tenant-specific patterns
        created_by_user_id: Optional user ID who created the patterns
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
        required_columns = ["Supplier Name", "Field Name", "Pattern Type", "Pattern Value"]
        for col in required_columns:
            if col not in df.columns:
                return {
                    "success": False,
                    "message": f"Missing required column: {col}",
                    "created": 0,
                    "errors": []
                }
        
        # Process rows
        created = 0
        errors = []
        
        for _, row in df.iterrows():
            try:
                # Get values
                supplier_name = str(row["Supplier Name"])
                field_name = str(row["Field Name"])
                pattern_type = str(row["Pattern Type"])
                pattern_value = str(row["Pattern Value"])
                
                # Get optional values
                priority = int(row["Priority"]) if "Priority" in df.columns and not pd.isna(row["Priority"]) else 0
                notes = str(row["Notes"]) if "Notes" in df.columns and not pd.isna(row["Notes"]) else None
                
                # Skip rows with empty required values
                if pd.isna(supplier_name) or pd.isna(field_name) or pd.isna(pattern_type) or pd.isna(pattern_value):
                    errors.append(f"Row {_ + 2}: Empty required value")
                    continue
                
                # Create pattern
                create_supplier_pattern(
                    supplier_name=supplier_name,
                    field_name=field_name,
                    pattern_type=pattern_type,
                    pattern_value=pattern_value,
                    tenant_id=tenant_id,
                    priority=priority,
                    notes=notes,
                    created_by_user_id=created_by_user_id,
                    session=session
                )
                
                created += 1
            
            except Exception as e:
                errors.append(f"Row {_ + 2}: {str(e)}")
        
        return {
            "success": True,
            "message": f"Imported {created} patterns ({len(errors)} errors)",
            "created": created,
            "errors": errors
        }
    
    except Exception as e:
        logger.error(f"Error importing patterns: {str(e)}")
        return {
            "success": False,
            "message": f"Error importing patterns: {str(e)}",
            "created": 0,
            "errors": [str(e)]
        }
    
    finally:
        # Close session if we created it
        if close_session:
            session.close()


def export_patterns_to_excel(
    output_path: str,
    tenant_id: Optional[int] = None,
    supplier_name: Optional[str] = None,
    field_name: Optional[str] = None,
    include_inactive: bool = False,
    session: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Export supplier extraction patterns to Excel file.
    
    Args:
        output_path: Path to save Excel file
        tenant_id: Optional tenant ID to filter by
        supplier_name: Optional supplier name to filter by
        field_name: Optional field name to filter by
        include_inactive: Whether to include inactive patterns
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
        # Build query
        query = session.query(SupplierExtractionPattern)
        
        # Apply filters
        if tenant_id is not None:
            query = query.filter(
                or_(
                    SupplierExtractionPattern.tenant_id == tenant_id,
                    SupplierExtractionPattern.tenant_id.is_(None)  # Include global patterns
                )
            )
        
        if supplier_name:
            query = query.filter(SupplierExtractionPattern.supplier_name.ilike(f"%{supplier_name}%"))
        
        if field_name:
            query = query.filter(SupplierExtractionPattern.field_name == field_name)
        
        if not include_inactive:
            query = query.filter(SupplierExtractionPattern.is_active == True)
        
        # Get patterns
        patterns = query.order_by(
            SupplierExtractionPattern.supplier_name,
            SupplierExtractionPattern.field_name,
            SupplierExtractionPattern.priority.desc()
        ).all()
        
        # Convert to DataFrame
        data = []
        for pattern in patterns:
            data.append({
                "Supplier Name": pattern.supplier_name,
                "Field Name": pattern.field_name,
                "Pattern Type": pattern.pattern_type,
                "Pattern Value": pattern.pattern_value,
                "Priority": pattern.priority,
                "Is Active": pattern.is_active,
                "Notes": pattern.notes
            })
        
        df = pd.DataFrame(data)
        
        # Save to Excel
        df.to_excel(output_path, index=False)
        
        return {
            "success": True,
            "message": f"Exported {len(patterns)} patterns to {output_path}",
            "count": len(patterns),
            "path": output_path
        }
    
    except Exception as e:
        logger.error(f"Error exporting patterns: {str(e)}")
        return {
            "success": False,
            "message": f"Error exporting patterns: {str(e)}",
            "count": 0,
            "path": None
        }
    
    finally:
        # Close session if we created it
        if close_session:
            session.close()


def create_pattern_template(output_path: str) -> Dict[str, Any]:
    """
    Create Excel template for supplier extraction patterns.
    
    Args:
        output_path: Path to save Excel file
    
    Returns:
        Dictionary with result
    """
    try:
        # Create DataFrame with sample data
        df = pd.DataFrame({
            "Supplier Name": ["British Gas", "British Gas", "E.ON", "E.ON", "Opus Energy"],
            "Field Name": ["supplier_account_number", "billing_period_start", "supplier_account_number", "billing_period_start", "supplier_account_number"],
            "Pattern Type": ["regex", "regex", "regex", "regex", "regex"],
            "Pattern Value": [
                r'customer\s+reference\s+number[\s:]+([0-9\s-]{6,})',
                r'bill\s+period[\s:]+(\d{1,2}\s+[A-Za-z]{3}\s+\d{2})\s*[-–]\s*(\d{1,2}\s+[A-Za-z]{3}\s+\d{2})',
                r'account\s+number[\s:]+([0-9\s-]{6,})',
                r'billing\s+period[\s:]+(\d{1,2}\s+[A-Za-z]{3}\s+\d{2})\s*[-–]\s*(\d{1,2}\s+[A-Za-z]{3}\s+\d{2})',
                r'account\s+number\s*\n(?:[^\n]*\n){0,2}\s*([0-9]{6,})'
            ],
            "Priority": [100, 100, 100, 100, 100],
            "Notes": [
                "British Gas account number pattern",
                "British Gas billing period pattern",
                "E.ON account number pattern",
                "E.ON billing period pattern",
                "Opus Energy account number pattern (multi-line)"
            ]
        })
        
        # Save to Excel
        df.to_excel(output_path, index=False)
        
        return {
            "success": True,
            "message": f"Created pattern template at {output_path}",
            "path": output_path
        }
    
    except Exception as e:
        logger.error(f"Error creating pattern template: {str(e)}")
        return {
            "success": False,
            "message": f"Error creating pattern template: {str(e)}",
            "path": None
        }


def apply_extraction_patterns(
    content: str,
    patterns: List[SupplierExtractionPattern]
) -> Tuple[Optional[str], float]:
    """
    Apply extraction patterns to content and return the best match.
    
    Args:
        content: Text content to extract from
        patterns: List of SupplierExtractionPattern objects to apply
    
    Returns:
        Tuple of (extracted_value, confidence_score)
        - extracted_value: The extracted value or None if no match
        - confidence_score: Confidence score (0.0 to 1.0)
    """
    if not content or not patterns:
        return None, 0.0
    
    for pattern in patterns:
        if pattern.pattern_type == "regex":
            try:
                # Apply regex pattern
                match = re.search(pattern.pattern_value, content, re.IGNORECASE | re.MULTILINE)
                if match:
                    # Get first capture group
                    if len(match.groups()) >= 1:
                        value = match.group(1).strip()
                        # Calculate confidence based on pattern priority
                        confidence = min(0.5 + (pattern.priority / 100), 0.99)
                        return value, confidence
                    # If no capture groups, get the whole match
                    elif match.group(0):
                        value = match.group(0).strip()
                        confidence = min(0.3 + (pattern.priority / 100), 0.8)  # Lower confidence for whole match
                        return value, confidence
            except re.error:
                logger.error(f"Invalid regex pattern: {pattern.pattern_value}")
                continue
    
    return None, 0.0


def create_default_patterns(session: Session) -> int:
    """
    Create default extraction patterns for common suppliers.
    
    Args:
        session: Database session
    
    Returns:
        Number of patterns created
    """
    # Define default patterns
    default_patterns = [
        # British Gas patterns
        {
            "supplier_name": "British Gas",
            "field_name": "supplier_account_number",
            "pattern_type": "regex",
            "pattern_value": r'customer\s+reference\s+number[\s:]+([0-9\s-]{6,})',
            "priority": 100,
            "notes": "British Gas account number pattern"
        },
        {
            "supplier_name": "British Gas",
            "field_name": "supplier_account_number",
            "pattern_type": "regex",
            "pattern_value": r'customer\s+reference[\s:]+([0-9\s-]{6,})',
            "priority": 90,
            "notes": "British Gas account number pattern (alternative)"
        },
        {
            "supplier_name": "British Gas",
            "field_name": "billing_period_start",
            "pattern_type": "regex",
            "pattern_value": r'bill\s+period[\s:]+(\d{1,2}\s+[A-Za-z]{3}\s+\d{2})\s*[-–]\s*\d{1,2}\s+[A-Za-z]{3}\s+\d{2}',
            "priority": 100,
            "notes": "British Gas billing period start pattern"
        },
        {
            "supplier_name": "British Gas",
            "field_name": "billing_period_end",
            "pattern_type": "regex",
            "pattern_value": r'bill\s+period[\s:]+\d{1,2}\s+[A-Za-z]{3}\s+\d{2}\s*[-–]\s*(\d{1,2}\s+[A-Za-z]{3}\s+\d{2})',
            "priority": 100,
            "notes": "British Gas billing period end pattern"
        },
        
        # E.ON patterns
        {
            "supplier_name": "E.ON",
            "field_name": "supplier_account_number",
            "pattern_type": "regex",
            "pattern_value": r'account\s+number[\s:]+([0-9\s-]{6,})',
            "priority": 100,
            "notes": "E.ON account number pattern"
        },
        {
            "supplier_name": "E.ON",
            "field_name": "supplier_account_number",
            "pattern_type": "regex",
            "pattern_value": r'your\s+account\s+number[\s:]+([0-9\s-]{6,})',
            "priority": 90,
            "notes": "E.ON account number pattern (with 'your')"
        },
        {
            "supplier_name": "E.ON",
            "field_name": "supplier_account_number",
            "pattern_type": "regex",
            "pattern_value": r'your\s+account\s+number\s*\n\s*([0-9]{4}\s+[0-9]{4}\s+[0-9]{2})',
            "priority": 80,
            "notes": "E.ON account number pattern (multi-line)"
        },
        {
            "supplier_name": "E.ON",
            "field_name": "billing_period_start",
            "pattern_type": "regex",
            "pattern_value": r'billing\s+period[\s:]+(\d{1,2}\s+[A-Za-z]{3}\s+\d{2})\s*[-–]\s*\d{1,2}\s+[A-Za-z]{3}\s+\d{2}',
            "priority": 100,
            "notes": "E.ON billing period start pattern"
        },
        {
            "supplier_name": "E.ON",
            "field_name": "billing_period_end",
            "pattern_type": "regex",
            "pattern_value": r'billing\s+period[\s:]+\d{1,2}\s+[A-Za-z]{3}\s+\d{2}\s*[-–]\s*(\d{1,2}\s+[A-Za-z]{3}\s+\d{2})',
            "priority": 100,
            "notes": "E.ON billing period end pattern"
        },
        
        # Opus Energy patterns
        {
            "supplier_name": "Opus Energy",
            "field_name": "supplier_account_number",
            "pattern_type": "regex",
            "pattern_value": r'account\s+number\s*\n(?:[^\n]*\n){0,2}\s*([0-9]{6,})',
            "priority": 100,
            "notes": "Opus Energy account number pattern (multi-line)"
        },
        {
            "supplier_name": "Opus Energy",
            "field_name": "supplier_account_number",
            "pattern_type": "regex",
            "pattern_value": r'account\s+number\s*\n\s*([0-9]+)\s*\n\s*([0-9]+)',
            "priority": 90,
            "notes": "Opus Energy account number pattern (split across lines)"
        },
        
        # Generic patterns (lower priority)
        {
            "supplier_name": "Generic",
            "field_name": "supplier_account_number",
            "pattern_type": "regex",
            "pattern_value": r'(?:your\s+)?account\s+number[\s:]+([0-9\s-]{6,})',
            "priority": 50,
            "notes": "Generic account number pattern"
        },
        {
            "supplier_name": "Generic",
            "field_name": "supplier_account_number",
            "pattern_type": "regex",
            "pattern_value": r'customer\s+reference[\s:]+([0-9\s-]{6,})',
            "priority": 40,
            "notes": "Generic customer reference pattern"
        },
        {
            "supplier_name": "Generic",
            "field_name": "billing_period_start",
            "pattern_type": "regex",
            "pattern_value": r'(?:billing|bill)\s+period[\s:]+(\d{1,2}[\/\s.-][A-Za-z]{3}[\/\s.-]\d{2,4})\s*[-–]\s*\d{1,2}[\/\s.-][A-Za-z]{3}[\/\s.-]\d{2,4}',
            "priority": 50,
            "notes": "Generic billing period start pattern"
        },
        {
            "supplier_name": "Generic",
            "field_name": "billing_period_end",
            "pattern_type": "regex",
            "pattern_value": r'(?:billing|bill)\s+period[\s:]+\d{1,2}[\/\s.-][A-Za-z]{3}[\/\s.-]\d{2,4}\s*[-–]\s*(\d{1,2}[\/\s.-][A-Za-z]{3}[\/\s.-]\d{2,4})',
            "priority": 50,
            "notes": "Generic billing period end pattern"
        }
    ]
    
    # Create patterns
    created = 0
    for pattern_data in default_patterns:
        try:
            # Check if pattern already exists
            existing = session.query(SupplierExtractionPattern).filter(
                SupplierExtractionPattern.supplier_name == pattern_data["supplier_name"],
                SupplierExtractionPattern.field_name == pattern_data["field_name"],
                SupplierExtractionPattern.pattern_value == pattern_data["pattern_value"],
                SupplierExtractionPattern.tenant_id.is_(None)  # Only check global patterns
            ).first()
            
            if not existing:
                # Create pattern directly without using create_supplier_pattern
                pattern = SupplierExtractionPattern(
                    supplier_name=pattern_data["supplier_name"],
                    field_name=pattern_data["field_name"],
                    pattern_type=pattern_data["pattern_type"],
                    pattern_value=pattern_data["pattern_value"],
                    priority=pattern_data["priority"],
                    notes=pattern_data["notes"],
                    tenant_id=None  # Global pattern
                )
                
                session.add(pattern)
                session.flush()
                created += 1
        except Exception as e:
            logger.error(f"Error creating pattern: {str(e)}")
    
    # Commit all patterns at once
    session.commit()
    return created