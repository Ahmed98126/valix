"""Test Opus account number extraction."""

import sys
from pathlib import Path
import re

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.pdf_processor import PDFProcessor

processor = PDFProcessor()
result = processor.extract_invoice("Opus-Invoice.pdf")
content = result.get('content', '')

print("Searching for 'Your account number'...")
match = re.search(r'Your account number', content, re.IGNORECASE)
if match:
    start = match.end()
    context = content[start:start+200]
    print(f"Found! Context after 'Your account number':")
    print(repr(context))
    print("\nTrying Opus pattern...")
    opus_pattern = r'(?:your\s+)?account\s+number\s*\n\s*([0-9]+)\s*\n\s*([0-9]+)'
    opus_match = re.search(opus_pattern, content, re.IGNORECASE | re.MULTILINE)
    if opus_match:
        print(f"MATCHED! Group 1: {opus_match.group(1)}, Group 2: {opus_match.group(2)}")
        print(f"Combined: {opus_match.group(1) + opus_match.group(2)}")
    else:
        print("Pattern did NOT match")
        # Try simpler pattern
        simple_pattern = r'account\s+number\s*\n\s*([0-9]+)'
        simple_match = re.search(simple_pattern, content, re.IGNORECASE | re.MULTILINE)
        if simple_match:
            print(f"Simple pattern matched: {simple_match.group(1)}")
            # Look for next number
            next_num = re.search(r'\n\s*([0-9]+)', content[simple_match.end():simple_match.end()+50], re.MULTILINE)
            if next_num:
                print(f"Next number found: {next_num.group(1)}")
                print(f"Combined: {simple_match.group(1) + next_num.group(1)}")
else:
    print("'Your account number' not found in content")

