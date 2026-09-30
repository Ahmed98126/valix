"""Enhanced PDF invoice processor with supplier-specific extraction patterns.

This module extends the basic PDF processor with:
1. Supplier-specific extraction patterns
2. Multi-method extraction
3. Confidence scoring
4. Field validation
"""

import os
import json
import logging
import re
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Any, Optional, Tuple, Union
from sqlalchemy.orm import Session

from app.pdf_processor import PDFProcessor
from app.pdf_normalizer import PDFNormalizer, normalize_pdf_invoice
from app.extraction_patterns import get_supplier_patterns, apply_extraction_patterns
from app.manual_review import queue_for_manual_review
from app.db import SessionLocal

logger = logging.getLogger(__name__)


class EnhancedPDFProcessor:
    """Enhanced PDF processor with supplier-specific extraction patterns."""
    
    # Minimum confidence thresholds for different fields
    CONFIDENCE_THRESHOLDS = {
        "invoice_number": 0.7,
        "supplier_name": 0.8,
        "supplier_account_number": 0.8,  # Critical field
        "billing_period_start": 0.7,
        "billing_period_end": 0.7,
        "invoice_date": 0.6,
        "gross_amount": 0.8,  # Critical field
        "default": 0.6  # Default threshold for other fields
    }
    
    def __init__(
        self,
        azure_endpoint: Optional[str] = None,
        azure_api_key: Optional[str] = None,
        tenant_id: Optional[int] = None,
        session: Optional[Session] = None
    ):
        """
        Initialize the enhanced PDF processor.
        
        Args:
            azure_endpoint: Azure Document Intelligence endpoint
            azure_api_key: Azure Document Intelligence API key
            tenant_id: Optional tenant ID for tenant-specific patterns
            session: Optional database session
        """
        self.pdf_processor = PDFProcessor(endpoint=azure_endpoint, api_key=azure_api_key)
        self.normalizer = PDFNormalizer()
        self.tenant_id = tenant_id
        
        # Use provided session or create a new one
        self.session = session
        self.close_session = False
        if self.session is None:
            self.session = SessionLocal()
            self.close_session = True
    
    def __del__(self):
        """Clean up resources."""
        if hasattr(self, 'session') and hasattr(self, 'close_session') and self.close_session:
            self.session.close()
    
    def process_invoice(
        self,
        pdf_path: str,
        queue_if_low_confidence: bool = True
    ) -> Dict[str, Any]:
        """
        Process a PDF invoice with enhanced extraction.
        
        Args:
            pdf_path: Path to the PDF file
            queue_if_low_confidence: Whether to queue for manual review if confidence is low
        
        Returns:
            Dictionary with processing results
        """
        try:
            logger.info(f"Processing PDF invoice: {pdf_path}")
            
            # Step 1: Extract data using Azure Document Intelligence
            extracted_data = self.pdf_processor.extract_invoice(pdf_path)
            
            # Step 2: Try to detect supplier name first (needed for patterns)
            supplier_name = self._extract_supplier_name(extracted_data)
            logger.info(f"Detected supplier: {supplier_name}")
            
            # Step 3: Get supplier-specific patterns
            patterns = {}
            if supplier_name:
                for field in [
                    "supplier_account_number", "billing_period_start", "billing_period_end",
                    "invoice_number", "invoice_date", "gross_amount"
                ]:
                    patterns[field] = get_supplier_patterns(
                        supplier_name=supplier_name,
                        field_name=field,
                        tenant_id=self.tenant_id,
                        session=self.session
                    )
            
            # Step 4: Normalize data with enhanced extraction
            normalized_data = self._enhanced_normalize(extracted_data, supplier_name, patterns)
            
            # Step 5: Calculate confidence scores
            confidence_scores = self._calculate_confidence_scores(normalized_data)
            
            # Step 6: Validate required fields
            validation_result = self._validate_fields(normalized_data, confidence_scores)
            
            # Step 7: Handle low confidence or missing fields
            if not validation_result["valid"]:
                logger.warning(f"Low confidence or missing fields: {validation_result['issues']}")
                
                if queue_if_low_confidence:
                    # Queue for manual review
                    queue_for_manual_review(
                        pdf_path=pdf_path,
                        tenant_id=self.tenant_id,
                        extracted_data=normalized_data[0] if normalized_data else None,
                        raw_data=extracted_data,
                        confidence_scores=confidence_scores,
                        original_filename=os.path.basename(pdf_path),
                        notes=f"Issues: {', '.join(validation_result['issues'])}",
                        session=self.session
                    )
                    
                    return {
                        "status": "queued",
                        "message": "Invoice queued for manual review due to low confidence or missing fields",
                        "issues": validation_result["issues"],
                        "confidence_scores": confidence_scores,
                        "extracted_data": normalized_data[0] if normalized_data else None,
                        "pdf_path": pdf_path
                    }
            
            # Step 8: Return successful result
            return {
                "status": "success",
                "message": "Successfully processed invoice with enhanced extraction",
                "normalized_data": normalized_data,
                "confidence_scores": confidence_scores,
                "pdf_path": pdf_path
            }
        
        except Exception as e:
            logger.error(f"Error processing PDF invoice: {str(e)}")
            return {
                "status": "error",
                "message": f"Error processing PDF invoice: {str(e)}",
                "pdf_path": pdf_path
            }
    
    def _extract_supplier_name(self, extracted_data: Dict[str, Any]) -> Optional[str]:
        """
        Extract supplier name from Azure data.
        
        Args:
            extracted_data: Extracted data from Azure
        
        Returns:
            Supplier name or None if not found
        """
        # Try to get from Azure fields
        fields = extracted_data.get("fields", {})
        for field_name in ["VendorName", "SupplierName", "Vendor", "Supplier", "CompanyName"]:
            if field_name in fields and "value" in fields[field_name]:
                supplier = fields[field_name]["value"]
                if supplier:
                    return str(supplier).strip()
        
        # Try to get from content
        content = extracted_data.get("content", "")
        if content:
            # Look for common supplier names
            suppliers = [
                "British Gas", "E.ON", "E.ON Energy", "Octopus Energy", "Octopus",
                "EDF", "EDF Energy", "npower", "Scottish Power", "SSE", "Utility Warehouse",
                "OVO", "OVO Energy", "Bulb", "Shell Energy", "Green Energy", "Ecotricity",
                "Opus Energy", "Opus", "Gazprom", "Corona Energy", "Total Gas & Power"
            ]
            
            for supplier in suppliers:
                if re.search(rf'\b{re.escape(supplier)}\b', content, re.IGNORECASE):
                    return supplier
        
        return None
    
    def _enhanced_normalize(
        self,
        extracted_data: Dict[str, Any],
        supplier_name: Optional[str],
        patterns: Dict[str, List]
    ) -> List[Dict[str, Any]]:
        """
        Normalize data with enhanced extraction using supplier-specific patterns.
        
        Args:
            extracted_data: Extracted data from Azure
            supplier_name: Detected supplier name
            patterns: Dictionary of supplier-specific patterns
        
        Returns:
            List of normalized invoice dictionaries
        """
        # First use standard normalizer
        normalized_data = normalize_pdf_invoice(extracted_data)
        
        if not normalized_data:
            normalized_data = [{}]
        
        # Get content for pattern matching
        content = extracted_data.get("content", "")
        
        # Apply supplier-specific patterns for each field
        for field, field_patterns in patterns.items():
            # Skip if field already has a value with high confidence
            if field in normalized_data[0] and normalized_data[0][field]:
                continue
            
            # Apply patterns
            value, confidence = apply_extraction_patterns(content, field_patterns)
            if value:
                # For date fields, parse the date
                if field in ["billing_period_start", "billing_period_end", "invoice_date"]:
                    value = self._parse_date(value)
                
                # For amount fields, parse the decimal
                elif field in ["gross_amount", "net_amount", "vat_amount"]:
                    value = self._parse_decimal(value)
                
                # Set the value in normalized data
                normalized_data[0][field] = value
        
        # Set supplier name if detected
        if supplier_name and (not normalized_data[0].get("supplier_name") or normalized_data[0].get("supplier_name") == "Unknown Supplier"):
            normalized_data[0]["supplier_name"] = supplier_name
        
        return normalized_data
    
    def _calculate_confidence_scores(self, normalized_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate confidence scores for extracted fields.
        
        Args:
            normalized_data: Normalized invoice data
        
        Returns:
            Dictionary of confidence scores (0.0 to 1.0)
        """
        if not normalized_data:
            return {}
        
        invoice_data = normalized_data[0]
        confidence_scores = {}
        
        # Supplier name confidence
        if "supplier_name" in invoice_data and invoice_data["supplier_name"] != "Unknown Supplier":
            confidence_scores["supplier_name"] = 0.9
        else:
            confidence_scores["supplier_name"] = 0.3
        
        # Invoice number confidence
        if "invoice_number" in invoice_data and invoice_data["invoice_number"]:
            # Higher confidence if it contains both letters and numbers
            if re.search(r'[A-Za-z]', invoice_data["invoice_number"]) and re.search(r'[0-9]', invoice_data["invoice_number"]):
                confidence_scores["invoice_number"] = 0.9
            else:
                confidence_scores["invoice_number"] = 0.7
        else:
            confidence_scores["invoice_number"] = 0.0
        
        # Account number confidence
        if "supplier_account_number" in invoice_data and invoice_data["supplier_account_number"]:
            # Higher confidence if it's a typical account number format
            if re.match(r'^[0-9\s-]{6,}$', invoice_data["supplier_account_number"]):
                confidence_scores["supplier_account_number"] = 0.9
            else:
                confidence_scores["supplier_account_number"] = 0.7
        else:
            confidence_scores["supplier_account_number"] = 0.0
        
        # Billing period confidence
        if "billing_period_start" in invoice_data and "billing_period_end" in invoice_data:
            if invoice_data["billing_period_start"] and invoice_data["billing_period_end"]:
                # Check if dates are valid and end is after start
                if isinstance(invoice_data["billing_period_start"], date) and isinstance(invoice_data["billing_period_end"], date):
                    if invoice_data["billing_period_end"] >= invoice_data["billing_period_start"]:
                        confidence_scores["billing_period_start"] = 0.9
                        confidence_scores["billing_period_end"] = 0.9
                    else:
                        confidence_scores["billing_period_start"] = 0.5
                        confidence_scores["billing_period_end"] = 0.5
                else:
                    confidence_scores["billing_period_start"] = 0.6
                    confidence_scores["billing_period_end"] = 0.6
            else:
                confidence_scores["billing_period_start"] = 0.0 if not invoice_data.get("billing_period_start") else 0.5
                confidence_scores["billing_period_end"] = 0.0 if not invoice_data.get("billing_period_end") else 0.5
        
        # Amount confidence
        if "gross_amount" in invoice_data and invoice_data["gross_amount"]:
            if isinstance(invoice_data["gross_amount"], (int, float, Decimal)):
                confidence_scores["gross_amount"] = 0.9
            else:
                confidence_scores["gross_amount"] = 0.5
        else:
            confidence_scores["gross_amount"] = 0.0
        
        # Unit ID confidence - always low since it's derived from account mapping
        confidence_scores["unit_id"] = 0.0
        
        return confidence_scores
    
    def _validate_fields(
        self,
        normalized_data: List[Dict[str, Any]],
        confidence_scores: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Validate required fields and confidence scores.
        
        Args:
            normalized_data: Normalized invoice data
            confidence_scores: Confidence scores
        
        Returns:
            Dictionary with validation result
        """
        if not normalized_data:
            return {
                "valid": False,
                "issues": ["No normalized data"]
            }
        
        invoice_data = normalized_data[0]
        issues = []
        
        # Check required fields
        required_fields = [
            "invoice_number",
            "supplier_name",
            "supplier_account_number",
            "billing_period_start",
            "billing_period_end",
            "gross_amount"
        ]
        
        for field in required_fields:
            # Check if field is missing
            if field not in invoice_data or not invoice_data[field]:
                issues.append(f"Missing {field}")
                continue
            
            # Check confidence threshold
            threshold = self.CONFIDENCE_THRESHOLDS.get(field, self.CONFIDENCE_THRESHOLDS["default"])
            if field in confidence_scores and confidence_scores[field] < threshold:
                issues.append(f"Low confidence for {field}: {confidence_scores[field]:.2f} < {threshold:.2f}")
        
        # Check specific field validations
        if "supplier_account_number" in invoice_data and "invoice_number" in invoice_data:
            if invoice_data["supplier_account_number"] == invoice_data["invoice_number"]:
                issues.append("Account number same as invoice number")
        
        # Check billing period
        if "billing_period_start" in invoice_data and "billing_period_end" in invoice_data:
            if invoice_data["billing_period_start"] and invoice_data["billing_period_end"]:
                if isinstance(invoice_data["billing_period_start"], date) and isinstance(invoice_data["billing_period_end"], date):
                    if invoice_data["billing_period_end"] < invoice_data["billing_period_start"]:
                        issues.append("Billing period end before start")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }
    
    def _parse_date(self, date_str: str) -> Optional[date]:
        """
        Parse a date string with multiple formats.
        
        Args:
            date_str: Date string
        
        Returns:
            Date object or None if parsing fails
        """
        if not date_str:
            return None
        
        # Clean up date string
        date_str = str(date_str).strip()
        
        # Try different date formats
        formats = [
            "%d %b %y",  # 25 Dec 20
            "%d %B %y",  # 25 December 20
            "%d %b %Y",  # 25 Dec 2020
            "%d %B %Y",  # 25 December 2020
            "%d/%m/%y",  # 25/12/20
            "%d/%m/%Y",  # 25/12/2020
            "%Y-%m-%d",  # 2020-12-25
            "%d-%m-%Y",  # 25-12-2020
            "%d-%m-%y",  # 25-12-20
            "%d.%m.%Y",  # 25.12.2020
            "%d.%m.%y",  # 25.12.20
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        return None
    
    def _parse_decimal(self, value: str) -> Optional[Decimal]:
        """
        Parse a decimal value from string.
        
        Args:
            value: String value
        
        Returns:
            Decimal value or None if parsing fails
        """
        if not value:
            return None
        
        # Clean up value
        value_str = str(value).strip()
        
        # Remove currency symbols
        value_str = re.sub(r'[£$€]', '', value_str)
        
        # Replace commas with nothing
        value_str = value_str.replace(',', '')
        
        try:
            return Decimal(value_str)
        except:
            return None


def process_pdf_with_enhanced_extraction(
    pdf_path: str,
    tenant_id: int,
    queue_if_low_confidence: bool = True,
    session: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Process a PDF invoice with enhanced extraction (convenience function).
    
    Args:
        pdf_path: Path to the PDF file
        tenant_id: Tenant ID
        queue_if_low_confidence: Whether to queue for manual review if confidence is low
        session: Optional database session
    
    Returns:
        Dictionary with processing results
    """
    processor = EnhancedPDFProcessor(tenant_id=tenant_id, session=session)
    return processor.process_invoice(pdf_path, queue_if_low_confidence)