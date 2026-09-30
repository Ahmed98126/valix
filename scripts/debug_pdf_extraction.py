"""Debug script to see what Azure actually extracted from the PDF."""

import sys
import json
import re
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.pdf_processor import PDFProcessor
from app.pdf_normalizer import PDFNormalizer

if len(sys.argv) < 2:
    print("Usage: python scripts/debug_pdf_extraction.py path/to/invoice.pdf")
    sys.exit(1)

pdf_path = sys.argv[1]

print("=" * 70)
print("Debugging PDF Extraction")
print("=" * 70)
print(f"\nPDF: {pdf_path}\n")

try:
    processor = PDFProcessor()
    extracted_data = processor.extract_invoice(pdf_path)
    
    print("=" * 70)
    print("FIELDS EXTRACTED BY AZURE:")
    print("=" * 70)
    
    fields = extracted_data.get("fields", {})
    if fields:
        for field_name, field_value in fields.items():
            if isinstance(field_value, dict):
                value = field_value.get("value") or field_value.get("content", "N/A")
                confidence = field_value.get("confidence")
                print(f"\n{field_name}:")
                print(f"  Value: {value}")
                if confidence:
                    print(f"  Confidence: {confidence:.2%}")
            else:
                print(f"\n{field_name}: {field_value}")
    else:
        print("No fields found!")
    
    # Check for account number in fields
    print("\n" + "=" * 70)
    print("ACCOUNT NUMBER SEARCH:")
    print("=" * 70)
    
    account_fields = ["CustomerAccountNumber", "AccountNumber", "Account", "CustomerNumber"]
    found_account = False
    for field_name in account_fields:
        if field_name in fields:
            value = fields[field_name]
            if isinstance(value, dict):
                account_value = value.get("value") or value.get("content", "")
            else:
                account_value = str(value)
            if account_value:
                print(f"✓ Found in {field_name}: {account_value}")
                found_account = True
    
    if not found_account:
        print("✗ Account number NOT found in Azure fields")
    
    # Check content for account number
    content = extracted_data.get("content", "")
    if content:
        print(f"\nContent length: {len(content)} characters")
        print(f"Content sample (first 500 chars):\n{content[:500]}\n")
        
        # Search for account number patterns
        account_patterns = [
            r'(?:your\s+)?account\s+number[\s:]+([0-9\s-]{6,})',
            r'account\s+number[\s:]+([0-9\s-]{6,})',
            r'account[\s:]+([0-9\s-]{6,})',
            r'customer\s+account[\s:]+([0-9\s-]{6,})',
            r'account\s+no[\s:\.]+([0-9\s-]{6,})',
            r'(?:account|account\s+number|account\s+no)[\s:\.]*([0-9]{4}\s+[0-9]{4}\s+[0-9]{2})',
        ]
        
        print("Searching for account number patterns in content...")
        for i, pattern in enumerate(account_patterns):
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                account_str = match.group(1).strip()
                print(f"  Pattern {i+1} matched: '{account_str}' (at position {match.start()})")
                # Show context
                start = max(0, match.start() - 50)
                end = min(len(content), match.end() + 50)
                context = content[start:end]
                print(f"    Context: ...{context}...")
    else:
        print("✗ No content field found in extraction")
    
    # Try normalization
    print("\n" + "=" * 70)
    print("NORMALIZATION TEST:")
    print("=" * 70)
    
    try:
        normalizer = PDFNormalizer()
        normalized = normalizer.normalize(extracted_data)
        if normalized:
            invoice = normalized[0]
            print(f"\n✓ Normalized invoice:")
            print(f"  Invoice Number: {invoice.get('invoice_number')}")
            print(f"  Account Number: {invoice.get('supplier_account_number')}")
            print(f"  Supplier: {invoice.get('supplier_name')}")
            print(f"  Unit ID: {invoice.get('unit_id')}")
        else:
            print("✗ Normalization returned empty list")
    except Exception as e:
        print(f"✗ Normalization failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Save full extraction to file
    output_file = Path("debug_extraction_full.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(extracted_data, f, indent=2, default=str, ensure_ascii=False)
    
    print(f"\n{'=' * 70}")
    print(f"Full extraction saved to: {output_file}")
    print("=" * 70)
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

