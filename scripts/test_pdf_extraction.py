#!/usr/bin/env python
"""
Test PDF extraction accuracy.

This script tests the PDF extraction pipeline by:
1. Extracting data from PDF using Azure Document Intelligence
2. Normalizing the data to invoice schema
3. Displaying the extracted fields and their values
4. Optionally comparing with expected values

Usage:
    python scripts/test_pdf_extraction.py path/to/invoice.pdf [--enhanced]
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, date
from decimal import Decimal

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.pdf_processor import PDFProcessor
from app.pdf_normalizer import normalize_pdf_invoice
from app.enhanced_pdf_processor import process_pdf_with_enhanced_extraction
from app.db import SessionLocal


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal and date objects."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)


def print_extraction_results(extracted_data, normalized_data):
    """
    Print the extraction results in a readable format.
    
    Args:
        extracted_data: Raw data from Azure Document Intelligence
        normalized_data: Normalized invoice data
    """
    print("\n" + "="*80)
    print("PDF EXTRACTION RESULTS")
    print("="*80)
    
    # Print raw extraction summary
    print("\nRAW EXTRACTION SUMMARY:")
    print(f"Model ID: {extracted_data.get('model_id')}")
    print(f"Pages: {len(extracted_data.get('pages', []))}")
    print(f"Fields: {len(extracted_data.get('fields', {}))}")
    print(f"Tables: {len(extracted_data.get('tables', []))}")
    
    # Print normalized data
    if normalized_data and len(normalized_data) > 0:
        invoice = normalized_data[0]
        print("\nNORMALIZED INVOICE DATA:")
        print(f"Invoice Number: {invoice.get('invoice_number')}")
        print(f"Supplier Name: {invoice.get('supplier_name')}")
        print(f"Supplier Account Number: {invoice.get('supplier_account_number')}")
        print(f"Unit ID: {invoice.get('unit_id')}")
        print(f"Address: {invoice.get('address')}")
        
        # Format dates
        billing_start = invoice.get('billing_period_start')
        if billing_start and isinstance(billing_start, (date, datetime)):
            billing_start = billing_start.strftime('%Y-%m-%d')
        
        billing_end = invoice.get('billing_period_end')
        if billing_end and isinstance(billing_end, (date, datetime)):
            billing_end = billing_end.strftime('%Y-%m-%d')
        
        invoice_date = invoice.get('invoice_date')
        if invoice_date and isinstance(invoice_date, (date, datetime)):
            invoice_date = invoice_date.strftime('%Y-%m-%d')
        
        print(f"Billing Period: {billing_start} to {billing_end}")
        print(f"Invoice Date: {invoice_date}")
        print(f"Gross Amount: {invoice.get('gross_amount')}")
        print(f"Net Amount: {invoice.get('net_amount')}")
        print(f"VAT Amount: {invoice.get('vat_amount')}")
        print(f"Utility Type: {invoice.get('utility_type')}")
        print(f"Currency: {invoice.get('currency')}")
    else:
        print("\nNORMALIZED INVOICE DATA: None (extraction failed)")
    
    # Print raw fields
    print("\nRAW EXTRACTED FIELDS:")
    for field_name, field_data in extracted_data.get('fields', {}).items():
        if isinstance(field_data, dict):
            value = field_data.get('value')
            confidence = field_data.get('confidence')
            print(f"{field_name}: {value} (confidence: {confidence:.2f})")
        else:
            print(f"{field_name}: {field_data}")
    
    # Print content sample
    content = extracted_data.get('content', '')
    if content:
        print("\nCONTENT SAMPLE (first 500 chars):")
        print(content[:500] + "...")
    
    print("\n" + "="*80)


def save_extraction_results(pdf_path, extracted_data, normalized_data, output_dir):
    """
    Save extraction results to JSON files.
    
    Args:
        pdf_path: Path to the PDF file
        extracted_data: Raw data from Azure Document Intelligence
        normalized_data: Normalized invoice data
        output_dir: Directory to save results
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get base filename without extension
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    
    # Save raw extraction data
    raw_path = os.path.join(output_dir, f"{base_name}_raw.json")
    with open(raw_path, 'w') as f:
        json.dump(extracted_data, f, cls=DecimalEncoder, indent=2)
    
    # Save normalized data
    norm_path = os.path.join(output_dir, f"{base_name}_normalized.json")
    with open(norm_path, 'w') as f:
        json.dump(normalized_data, f, cls=DecimalEncoder, indent=2)
    
    print(f"Saved extraction results to {output_dir}")
    print(f"Raw data: {raw_path}")
    print(f"Normalized data: {norm_path}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Test PDF extraction accuracy')
    parser.add_argument('pdf_path', help='Path to PDF invoice file')
    parser.add_argument('--enhanced', action='store_true', help='Use enhanced extraction with supplier patterns')
    parser.add_argument('--save', action='store_true', help='Save extraction results to JSON files')
    parser.add_argument('--output-dir', default='test_results', help='Directory to save results (default: test_results)')
    
    args = parser.parse_args()
    
    # Check if PDF file exists
    if not os.path.isfile(args.pdf_path):
        print(f"Error: PDF file not found: {args.pdf_path}")
        return 1
    
    try:
        print(f"Testing extraction for PDF: {args.pdf_path}")
        print(f"Using {'enhanced' if args.enhanced else 'standard'} extraction")
        
        if args.enhanced:
            # Use enhanced extraction with supplier patterns
            session = SessionLocal()
            try:
                # Tenant ID 1 for testing
                result = process_pdf_with_enhanced_extraction(
                    pdf_path=args.pdf_path,
                    tenant_id=1,
                    queue_if_low_confidence=False,
                    session=session
                )
                
                if result["status"] == "success":
                    extracted_data = result["extracted_data"]
                    normalized_data = result["normalized_data"]
                    confidence_scores = result.get("confidence_scores", {})
                    
                    print_extraction_results(extracted_data, normalized_data)
                    
                    # Print confidence scores
                    print("\nCONFIDENCE SCORES:")
                    for field, score in confidence_scores.items():
                        print(f"{field}: {score:.2f}")
                    
                    if args.save:
                        save_extraction_results(args.pdf_path, extracted_data, normalized_data, args.output_dir)
                else:
                    print(f"Error: {result['message']}")
            finally:
                session.close()
        else:
            # Use standard extraction
            # Step 1: Extract data using Azure Document Intelligence
            processor = PDFProcessor()
            extracted_data = processor.extract_invoice(args.pdf_path)
            
            # Step 2: Normalize data to invoice schema
            normalized_data = normalize_pdf_invoice(extracted_data)
            
            # Print results
            print_extraction_results(extracted_data, normalized_data)
            
            # Save results if requested
            if args.save:
                save_extraction_results(args.pdf_path, extracted_data, normalized_data, args.output_dir)
        
        return 0
    
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())