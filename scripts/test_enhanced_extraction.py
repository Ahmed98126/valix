"""Test enhanced PDF extraction with supplier-specific patterns.

This script tests the enhanced PDF extraction with supplier-specific patterns
on a given PDF invoice file.

Usage:
    python scripts/test_enhanced_extraction.py path/to/invoice.pdf
"""

import sys
import json
from pathlib import Path
from pprint import pprint

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.enhanced_pdf_processor import EnhancedPDFProcessor
from app.extraction_patterns import get_supplier_patterns
from app.db import get_session, init_db


def print_section(title):
    """Print a section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def print_field(label, value, confidence=None, indent=0):
    """Print a field with label, value, and confidence."""
    prefix = "  " * indent
    
    # Format value
    if value is None:
        value_str = "❌ None"
    elif value == "":
        value_str = "⚠️  Empty"
    else:
        value_str = f"✅ {value}"
    
    # Format confidence
    if confidence is not None:
        if confidence >= 0.8:
            conf_str = f"🟢 {confidence:.2f}"
        elif confidence >= 0.6:
            conf_str = f"🟡 {confidence:.2f}"
        else:
            conf_str = f"🔴 {confidence:.2f}"
        
        print(f"{prefix}{label:30} {value_str:40} Confidence: {conf_str}")
    else:
        print(f"{prefix}{label:30} {value_str}")


def test_enhanced_extraction(pdf_path):
    """Test enhanced PDF extraction."""
    pdf_path = Path(pdf_path)
    
    if not pdf_path.exists():
        print(f"❌ PDF file not found: {pdf_path}")
        return
    
    print_section(f"Testing Enhanced PDF Extraction: {pdf_path.name}")
    
    # Initialize database
    init_db()
    
    with get_session() as session:
        # Create processor
        processor = EnhancedPDFProcessor(session=session)
        
        # Process invoice
        result = processor.process_invoice(str(pdf_path), queue_if_low_confidence=False)
        
        # Print result status
        print(f"Status: {result['status']}")
        print(f"Message: {result['message']}")
        
        if result["status"] == "error":
            print(f"❌ Error: {result['message']}")
            return
        
        # Print extracted data
        if result["status"] == "success" and "normalized_data" in result:
            print_section("Extracted Invoice Data")
            
            invoice_data = result["normalized_data"][0]
            confidence_scores = result.get("confidence_scores", {})
            
            print_field("Invoice Number", invoice_data.get("invoice_number"), confidence_scores.get("invoice_number"))
            print_field("Supplier Name", invoice_data.get("supplier_name"), confidence_scores.get("supplier_name"))
            print_field("Supplier Account Number", invoice_data.get("supplier_account_number"), confidence_scores.get("supplier_account_number"))
            print_field("Billing Period Start", invoice_data.get("billing_period_start"), confidence_scores.get("billing_period_start"))
            print_field("Billing Period End", invoice_data.get("billing_period_end"), confidence_scores.get("billing_period_end"))
            print_field("Invoice Date", invoice_data.get("invoice_date"), confidence_scores.get("invoice_date"))
            print_field("Gross Amount", invoice_data.get("gross_amount"), confidence_scores.get("gross_amount"))
            print_field("Net Amount", invoice_data.get("net_amount"))
            print_field("VAT Amount", invoice_data.get("vat_amount"))
            print_field("Utility Type", invoice_data.get("utility_type"))
            print_field("Currency", invoice_data.get("currency"))
            print_field("Address", invoice_data.get("address"))
            
            # Print validation
            print_section("Validation")
            validation_result = processor._validate_fields(result["normalized_data"], confidence_scores)
            print(f"Valid: {'✅ Yes' if validation_result['valid'] else '❌ No'}")
            
            if validation_result["issues"]:
                print("Issues:")
                for issue in validation_result["issues"]:
                    print(f"  - ❌ {issue}")
            else:
                print("  ✅ No issues")
        
        # Print patterns used
        print_section("Supplier-Specific Patterns")
        supplier_name = result["normalized_data"][0].get("supplier_name") if result.get("normalized_data") else None
        
        if supplier_name:
            patterns = {}
            for field in ["supplier_account_number", "billing_period_start", "billing_period_end", "invoice_number"]:
                field_patterns = get_supplier_patterns(
                    supplier_name=supplier_name,
                    field_name=field,
                    session=session
                )
                
                if field_patterns:
                    print(f"\n{field} patterns:")
                    for i, pattern in enumerate(field_patterns):
                        print(f"  {i+1}. {pattern.pattern_value} (priority: {pattern.priority})")
                else:
                    print(f"\n{field} patterns: None")
        else:
            print("No supplier name detected")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_enhanced_extraction.py path/to/invoice.pdf")
        sys.exit(1)
    
    test_enhanced_extraction(sys.argv[1])