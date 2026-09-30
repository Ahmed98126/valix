#!/usr/bin/env python
"""
Batch test PDF extraction on multiple files.

This script processes multiple PDF files and generates a summary report
of extraction accuracy.

Usage:
    python scripts/batch_test_pdfs.py --input-dir path/to/pdfs [--enhanced] [--output-dir path/to/output]
"""

import os
import sys
import json
import argparse
import glob
from pathlib import Path
from datetime import datetime
from decimal import Decimal

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.pdf_processor import PDFProcessor
from app.pdf_normalizer import normalize_pdf_invoice
from app.enhanced_pdf_processor import process_pdf_with_enhanced_extraction
from app.db import SessionLocal


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal and datetime objects."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def process_pdf(pdf_path, use_enhanced=False):
    """
    Process a single PDF file.
    
    Args:
        pdf_path: Path to PDF file
        use_enhanced: Whether to use enhanced extraction
        
    Returns:
        Dictionary with processing results
    """
    try:
        if use_enhanced:
            # Use enhanced extraction with supplier patterns
            session = SessionLocal()
            try:
                # Tenant ID 1 for testing
                result = process_pdf_with_enhanced_extraction(
                    pdf_path=pdf_path,
                    tenant_id=1,
                    queue_if_low_confidence=False,
                    session=session
                )
                
                if result["status"] == "success":
                    return {
                        "success": True,
                        "pdf_path": pdf_path,
                        "extracted_data": result["extracted_data"],
                        "normalized_data": result["normalized_data"],
                        "confidence_scores": result.get("confidence_scores", {})
                    }
                else:
                    return {
                        "success": False,
                        "pdf_path": pdf_path,
                        "error": result["message"]
                    }
            finally:
                session.close()
        else:
            # Use standard extraction
            processor = PDFProcessor()
            extracted_data = processor.extract_invoice(pdf_path)
            normalized_data = normalize_pdf_invoice(extracted_data)
            
            if normalized_data and len(normalized_data) > 0:
                return {
                    "success": True,
                    "pdf_path": pdf_path,
                    "extracted_data": extracted_data,
                    "normalized_data": normalized_data
                }
            else:
                return {
                    "success": False,
                    "pdf_path": pdf_path,
                    "error": "Failed to normalize data"
                }
    
    except Exception as e:
        return {
            "success": False,
            "pdf_path": pdf_path,
            "error": str(e)
        }


def extract_key_fields(result):
    """
    Extract key fields from processing result.
    
    Args:
        result: Processing result dictionary
        
    Returns:
        Dictionary with key fields
    """
    if not result["success"] or not result.get("normalized_data") or len(result["normalized_data"]) == 0:
        return {
            "success": False,
            "error": result.get("error", "Unknown error")
        }
    
    invoice = result["normalized_data"][0]
    
    return {
        "success": True,
        "invoice_number": invoice.get("invoice_number"),
        "supplier_name": invoice.get("supplier_name"),
        "supplier_account_number": invoice.get("supplier_account_number"),
        "address": invoice.get("address"),
        "billing_period_start": invoice.get("billing_period_start"),
        "billing_period_end": invoice.get("billing_period_end"),
        "invoice_date": invoice.get("invoice_date"),
        "gross_amount": invoice.get("gross_amount"),
        "net_amount": invoice.get("net_amount"),
        "vat_amount": invoice.get("vat_amount"),
        "utility_type": invoice.get("utility_type"),
        "confidence_scores": result.get("confidence_scores", {})
    }


def save_results(results, output_dir):
    """
    Save processing results to output directory.
    
    Args:
        results: List of processing results
        output_dir: Output directory
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Save full results
    full_results_path = os.path.join(output_dir, "full_results.json")
    with open(full_results_path, 'w') as f:
        json.dump(results, f, cls=DecimalEncoder, indent=2)
    
    # Save summary
    summary = []
    for result in results:
        pdf_name = os.path.basename(result["pdf_path"])
        summary_item = {
            "pdf_name": pdf_name,
            "success": result["success"],
        }
        
        if result["success"]:
            key_fields = extract_key_fields(result)
            if key_fields["success"]:
                summary_item.update(key_fields)
            else:
                summary_item["error"] = key_fields["error"]
        else:
            summary_item["error"] = result.get("error", "Unknown error")
        
        summary.append(summary_item)
    
    summary_path = os.path.join(output_dir, "summary.json")
    with open(summary_path, 'w') as f:
        json.dump(summary, f, cls=DecimalEncoder, indent=2)
    
    # Save CSV summary
    csv_path = os.path.join(output_dir, "summary.csv")
    with open(csv_path, 'w') as f:
        # Write header
        f.write("pdf_name,success,invoice_number,supplier_name,supplier_account_number,invoice_date,gross_amount,error\n")
        
        # Write rows
        for item in summary:
            row = [
                item["pdf_name"],
                str(item["success"]),
                item.get("invoice_number", ""),
                item.get("supplier_name", ""),
                item.get("supplier_account_number", ""),
                str(item.get("invoice_date", "")),
                str(item.get("gross_amount", "")),
                item.get("error", "")
            ]
            # Escape commas in fields
            row = [f'"{field}"' if ',' in str(field) else str(field) for field in row]
            f.write(",".join(row) + "\n")
    
    print(f"Results saved to {output_dir}")
    print(f"Full results: {full_results_path}")
    print(f"Summary: {summary_path}")
    print(f"CSV Summary: {csv_path}")


def print_summary(results):
    """
    Print summary of processing results.
    
    Args:
        results: List of processing results
    """
    total = len(results)
    successful = sum(1 for r in results if r["success"])
    failed = total - successful
    
    print("\n" + "="*80)
    print(f"BATCH PROCESSING SUMMARY ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    print("="*80)
    print(f"Total PDFs processed: {total}")
    print(f"Successful: {successful} ({successful/total:.1%})")
    print(f"Failed: {failed} ({failed/total:.1%})")
    
    if failed > 0:
        print("\nFailed PDFs:")
        for result in results:
            if not result["success"]:
                pdf_name = os.path.basename(result["pdf_path"])
                error = result.get("error", "Unknown error")
                print(f"- {pdf_name}: {error}")
    
    print("\nExtracted fields summary:")
    
    # Count PDFs with each field successfully extracted
    field_counts = {}
    for result in results:
        if result["success"]:
            key_fields = extract_key_fields(result)
            if key_fields["success"]:
                for field, value in key_fields.items():
                    if field not in ["success", "confidence_scores"]:
                        if value is not None:
                            field_counts[field] = field_counts.get(field, 0) + 1
    
    # Print field extraction rates
    print(f"{'Field':<25} {'Count':<10} {'Rate':<10}")
    print("-"*45)
    for field, count in field_counts.items():
        rate = count / successful if successful > 0 else 0
        print(f"{field:<25} {count:<10} {rate:.1%}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Batch test PDF extraction')
    parser.add_argument('--input-dir', required=True, help='Directory containing PDF files')
    parser.add_argument('--pattern', default='*.pdf', help='Glob pattern to match PDF files (default: *.pdf)')
    parser.add_argument('--enhanced', action='store_true', help='Use enhanced extraction with supplier patterns')
    parser.add_argument('--output-dir', default='batch_results', help='Directory to save results (default: batch_results)')
    parser.add_argument('--limit', type=int, help='Limit number of PDFs to process')
    
    args = parser.parse_args()
    
    # Check if input directory exists
    if not os.path.isdir(args.input_dir):
        print(f"Error: Input directory not found: {args.input_dir}")
        return 1
    
    # Find PDF files
    pdf_pattern = os.path.join(args.input_dir, args.pattern)
    pdf_files = glob.glob(pdf_pattern)
    
    if not pdf_files:
        print(f"Error: No PDF files found matching pattern: {pdf_pattern}")
        return 1
    
    # Apply limit if specified
    if args.limit and args.limit > 0:
        pdf_files = pdf_files[:args.limit]
    
    print(f"Found {len(pdf_files)} PDF files")
    print(f"Using {'enhanced' if args.enhanced else 'standard'} extraction")
    
    # Process PDFs
    results = []
    for i, pdf_path in enumerate(pdf_files):
        print(f"Processing {i+1}/{len(pdf_files)}: {os.path.basename(pdf_path)}")
        result = process_pdf(pdf_path, args.enhanced)
        result["pdf_path"] = pdf_path  # Ensure pdf_path is included
        results.append(result)
    
    # Print summary
    print_summary(results)
    
    # Save results
    save_results(results, args.output_dir)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())