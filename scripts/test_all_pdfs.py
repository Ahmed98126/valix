"""Test all PDF invoices and report extraction results."""

import sys
from pathlib import Path
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.pdf_processor import PDFProcessor
from app.pdf_normalizer import PDFNormalizer
from app.config import (
    AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT,
    AZURE_DOCUMENT_INTELLIGENCE_API_KEY
)

def test_pdf_extraction(pdf_path: Path):
    """Test PDF extraction and normalization."""
    print(f"\n{'='*80}")
    print(f"Testing: {pdf_path.name}")
    print(f"{'='*80}\n")
    
    if not pdf_path.exists():
        print(f"ERROR: File not found: {pdf_path}")
        return None
    
    try:
        # Initialize processor
        processor = PDFProcessor()
        normalizer = PDFNormalizer()
        
        # Extract data
        print("Step 1: Extracting data from PDF...")
        extraction_result = processor.extract_invoice(str(pdf_path))
        
        if not extraction_result:
            print("ERROR: No data extracted from PDF")
            return None
        
        print(f"[OK] Extraction successful")
        print(f"   - Pages: {extraction_result.get('pages', 'Unknown')}")
        print(f"   - Content length: {len(str(extraction_result.get('content', '')))} chars")
        
        # Show key Azure fields
        print("\nStep 2: Azure Document Intelligence Fields:")
        print("-" * 80)
        
        # Check invoice fields
        fields = extraction_result.get('fields', {})
        key_fields = [
            'InvoiceId', 'InvoiceDate', 'DueDate', 'VendorName', 
            'CustomerName', 'CustomerAccountNumber', 'InvoiceTotal',
            'Items', 'BillingAddress', 'RemittanceAddress'
        ]
        
        for field in key_fields:
            value = fields.get(field)
            if value:
                if field == 'Items' and isinstance(value, list):
                    print(f"   {field}: {len(value)} items")
                else:
                    # Truncate long values
                    str_value = str(value)
                    if len(str_value) > 100:
                        str_value = str_value[:100] + "..."
                    print(f"   {field}: {str_value}")
        
        # Normalize data
        print("\nStep 3: Normalizing to Invoice schema...")
        normalized_list = normalizer.normalize(extraction_result)
        
        if not normalized_list or len(normalized_list) == 0:
            print("ERROR: Normalization failed - no invoices returned")
            return None
        
        normalized = normalized_list[0]  # Get first invoice
        print("[OK] Normalization successful")
        print(f"   - Found {len(normalized_list)} invoice(s)")
        print("\nStep 4: Normalized Invoice Data:")
        print("-" * 80)
        
        # Show normalized fields
        required_fields = [
            'invoice_number', 'supplier_account_number', 'supplier_name',
            'unit_id', 'billing_period_start', 'billing_period_end',
            'gross_amount', 'utility_type', 'invoice_date'
        ]
        
        for field in required_fields:
            value = normalized.get(field)
            status = "[OK]" if value else "[MISSING]"
            print(f"   {status} {field}: {value}")
        
        # Check for issues
        print("\nStep 5: Validation Check:")
        print("-" * 80)
        
        issues = []
        
        if not normalized.get('supplier_account_number'):
            issues.append("[ERROR] Missing supplier_account_number (REQUIRED)")
        elif normalized.get('supplier_account_number') == normalized.get('invoice_number'):
            issues.append("[WARNING] supplier_account_number same as invoice_number (should be different)")
        
        if not normalized.get('invoice_number'):
            issues.append("[ERROR] Missing invoice_number (REQUIRED)")
        
        if not normalized.get('supplier_name'):
            issues.append("[WARNING] Missing supplier_name")
        
        if not normalized.get('billing_period_start') or not normalized.get('billing_period_end'):
            issues.append("[WARNING] Missing billing period")
        
        if not normalized.get('gross_amount'):
            issues.append("[WARNING] Missing gross_amount")
        
        if not normalized.get('unit_id'):
            issues.append("[WARNING] Missing unit_id (will need manual mapping)")
        
        if issues:
            for issue in issues:
                print(f"   {issue}")
        else:
            print("   [OK] All required fields present!")
        
        return {
            'pdf_path': pdf_path,
            'extraction': extraction_result,
            'normalized': normalized,
            'issues': issues
        }
        
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Test all PDFs in the project directory."""
    
    # Check Azure credentials
    if not AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT or not AZURE_DOCUMENT_INTELLIGENCE_API_KEY:
        print("ERROR: Azure Document Intelligence credentials not configured")
        print("Please set AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT and AZURE_DOCUMENT_INTELLIGENCE_API_KEY")
        return
    
    # Find all PDFs in project root
    project_root = Path(__file__).parent.parent
    pdf_files = list(project_root.glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found in project root directory")
        print(f"Looking in: {project_root}")
        return
    
    print(f"\nFound {len(pdf_files)} PDF file(s):")
    for pdf in pdf_files:
        print(f"  - {pdf.name}")
    
    # Test each PDF
    results = []
    for pdf_file in pdf_files:
        result = test_pdf_extraction(pdf_file)
        if result:
            results.append(result)
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}\n")
    
    print(f"Total PDFs tested: {len(results)}")
    
    for result in results:
        pdf_name = result['pdf_path'].name
        issues = result['issues']
        normalized = result['normalized']
        
        print(f"\n{pdf_name}:")
        if not issues:
            print("  [OK] All fields extracted successfully!")
        else:
            print(f"  [WARNING] {len(issues)} issue(s) found:")
            for issue in issues:
                print(f"     {issue}")
        
        # Show key extracted values
        print(f"  Invoice #: {normalized.get('invoice_number', 'N/A')}")
        print(f"  Account #: {normalized.get('supplier_account_number', 'N/A')}")
        print(f"  Supplier: {normalized.get('supplier_name', 'N/A')}")
        print(f"  Amount: {normalized.get('gross_amount', 'N/A')}")

if __name__ == "__main__":
    main()

