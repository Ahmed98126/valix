#!/usr/bin/env python
"""
Evaluate PDF extraction accuracy against expected values.

This script compares the extracted invoice data with expected values
to measure extraction accuracy.

Usage:
    python scripts/evaluate_extraction.py path/to/invoice.pdf --expected path/to/expected.json [--enhanced]
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


def normalize_value(value):
    """Normalize value for comparison."""
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, str):
        return value.strip()
    return value


def compare_values(extracted, expected, field):
    """
    Compare extracted and expected values.
    
    Args:
        extracted: Extracted value
        expected: Expected value
        field: Field name
        
    Returns:
        Tuple of (match, message)
    """
    if extracted is None and expected is None:
        return True, "Both values are None"
    
    if extracted is None:
        return False, f"Extracted value is None, expected {expected}"
    
    if expected is None:
        return False, f"Expected value is None, extracted {extracted}"
    
    # Normalize values for comparison
    norm_extracted = normalize_value(extracted)
    norm_expected = normalize_value(expected)
    
    # Special handling for dates
    if field in ['billing_period_start', 'billing_period_end', 'invoice_date']:
        # If either is a string, convert to date for comparison
        if isinstance(norm_extracted, str) and not isinstance(norm_expected, str):
            try:
                norm_extracted = datetime.fromisoformat(norm_extracted).date().isoformat()
                norm_expected = norm_expected.isoformat()
            except ValueError:
                pass
        elif isinstance(norm_expected, str) and not isinstance(norm_extracted, str):
            try:
                norm_expected = datetime.fromisoformat(norm_expected).date().isoformat()
                norm_extracted = norm_extracted.isoformat()
            except ValueError:
                pass
    
    # Special handling for monetary amounts
    if field in ['gross_amount', 'net_amount', 'vat_amount']:
        # Convert to float for comparison with small tolerance
        try:
            float_extracted = float(norm_extracted)
            float_expected = float(norm_expected)
            # Allow small difference (1 penny)
            if abs(float_extracted - float_expected) < 0.01:
                return True, f"Match within tolerance: {float_extracted} ≈ {float_expected}"
            else:
                return False, f"Mismatch: {float_extracted} != {float_expected}"
        except (ValueError, TypeError):
            pass
    
    # Default comparison
    if norm_extracted == norm_expected:
        return True, "Exact match"
    
    # For strings, check if one contains the other
    if isinstance(norm_extracted, str) and isinstance(norm_expected, str):
        norm_extracted_lower = norm_extracted.lower()
        norm_expected_lower = norm_expected.lower()
        
        if norm_extracted_lower in norm_expected_lower or norm_expected_lower in norm_extracted_lower:
            return True, f"Partial match: '{norm_extracted}' ~ '{norm_expected}'"
    
    return False, f"Mismatch: '{norm_extracted}' != '{norm_expected}'"


def evaluate_extraction(normalized_data, expected_data):
    """
    Evaluate extraction accuracy against expected values.
    
    Args:
        normalized_data: List of normalized invoice dictionaries
        expected_data: Dictionary of expected values
        
    Returns:
        Dictionary with evaluation results
    """
    if not normalized_data or len(normalized_data) == 0:
        return {
            "success": False,
            "message": "No normalized data",
            "fields_evaluated": 0,
            "fields_matched": 0,
            "accuracy": 0.0,
            "field_results": {}
        }
    
    invoice = normalized_data[0]
    field_results = {}
    fields_matched = 0
    fields_evaluated = 0
    
    # Fields to evaluate
    fields = [
        "invoice_number",
        "supplier_name",
        "supplier_account_number",
        "address",
        "billing_period_start",
        "billing_period_end",
        "invoice_date",
        "gross_amount",
        "net_amount",
        "vat_amount",
        "utility_type",
        "currency"
    ]
    
    for field in fields:
        if field in expected_data:
            fields_evaluated += 1
            extracted_value = invoice.get(field)
            expected_value = expected_data[field]
            
            match, message = compare_values(extracted_value, expected_value, field)
            
            if match:
                fields_matched += 1
            
            field_results[field] = {
                "extracted": extracted_value,
                "expected": expected_value,
                "match": match,
                "message": message
            }
    
    # Calculate accuracy
    accuracy = fields_matched / fields_evaluated if fields_evaluated > 0 else 0.0
    
    return {
        "success": True,
        "message": f"Evaluated {fields_evaluated} fields, matched {fields_matched}",
        "fields_evaluated": fields_evaluated,
        "fields_matched": fields_matched,
        "accuracy": accuracy,
        "field_results": field_results
    }


def print_evaluation_results(evaluation_results):
    """
    Print evaluation results in a readable format.
    
    Args:
        evaluation_results: Dictionary with evaluation results
    """
    print("\n" + "="*80)
    print("EXTRACTION EVALUATION RESULTS")
    print("="*80)
    
    if not evaluation_results["success"]:
        print(f"\nError: {evaluation_results['message']}")
        return
    
    print(f"\nAccuracy: {evaluation_results['accuracy']:.2%} ({evaluation_results['fields_matched']}/{evaluation_results['fields_evaluated']} fields matched)")
    
    print("\nField-by-field comparison:")
    print("-"*80)
    print(f"{'Field':<25} {'Match':<10} {'Extracted':<25} {'Expected':<25} {'Message'}")
    print("-"*80)
    
    for field, result in evaluation_results["field_results"].items():
        match_str = "✓" if result["match"] else "✗"
        extracted = str(result["extracted"])[:25]
        expected = str(result["expected"])[:25]
        
        print(f"{field:<25} {match_str:<10} {extracted:<25} {expected:<25} {result['message']}")


def create_expected_template(normalized_data, output_path):
    """
    Create a template JSON file with expected values.
    
    Args:
        normalized_data: List of normalized invoice dictionaries
        output_path: Path to save the template
    """
    if not normalized_data or len(normalized_data) == 0:
        print("Error: No normalized data to create template")
        return
    
    invoice = normalized_data[0]
    
    # Fields to include in template
    fields = [
        "invoice_number",
        "supplier_name",
        "supplier_account_number",
        "address",
        "billing_period_start",
        "billing_period_end",
        "invoice_date",
        "gross_amount",
        "net_amount",
        "vat_amount",
        "utility_type",
        "currency"
    ]
    
    template = {}
    for field in fields:
        template[field] = invoice.get(field)
    
    with open(output_path, 'w') as f:
        json.dump(template, f, cls=DecimalEncoder, indent=2)
    
    print(f"Created expected values template: {output_path}")
    print("Edit this file with the correct expected values, then run evaluation again.")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Evaluate PDF extraction accuracy')
    parser.add_argument('pdf_path', help='Path to PDF invoice file')
    parser.add_argument('--expected', help='Path to JSON file with expected values')
    parser.add_argument('--enhanced', action='store_true', help='Use enhanced extraction with supplier patterns')
    parser.add_argument('--create-template', action='store_true', help='Create template JSON file with expected values')
    
    args = parser.parse_args()
    
    # Check if PDF file exists
    if not os.path.isfile(args.pdf_path):
        print(f"Error: PDF file not found: {args.pdf_path}")
        return 1
    
    # Check if expected file exists when not creating template
    if not args.create_template and args.expected and not os.path.isfile(args.expected):
        print(f"Error: Expected values file not found: {args.expected}")
        return 1
    
    try:
        print(f"Processing PDF: {args.pdf_path}")
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
                    normalized_data = result["normalized_data"]
                else:
                    print(f"Error: {result['message']}")
                    return 1
            finally:
                session.close()
        else:
            # Use standard extraction
            processor = PDFProcessor()
            extracted_data = processor.extract_invoice(args.pdf_path)
            normalized_data = normalize_pdf_invoice(extracted_data)
        
        if args.create_template:
            # Create template with extracted values
            template_path = args.expected or f"{os.path.splitext(args.pdf_path)[0]}_expected.json"
            create_expected_template(normalized_data, template_path)
            return 0
        
        if args.expected:
            # Load expected values
            with open(args.expected, 'r') as f:
                expected_data = json.load(f)
            
            # Evaluate extraction
            evaluation_results = evaluate_extraction(normalized_data, expected_data)
            print_evaluation_results(evaluation_results)
            
            # Return success based on accuracy threshold
            return 0 if evaluation_results["accuracy"] >= 0.8 else 1
        else:
            print("No expected values provided. Use --expected or --create-template.")
            return 1
    
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())