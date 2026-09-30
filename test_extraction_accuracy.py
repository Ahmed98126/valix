"""Test PDF extraction accuracy for different suppliers."""

import os
import json
from dotenv import load_dotenv
from app.pdf_processor import PDFProcessor
from app.pdf_normalizer import PDFNormalizer

# Load environment variables from .env file
load_dotenv()

def test_extraction_accuracy(pdf_path):
    """Test extraction accuracy of a PDF invoice."""
    print(f"\n=== Testing extraction of {pdf_path} ===")
    
    # Check if Azure credentials are set
    endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
    api_key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_API_KEY")
    
    if not endpoint or not api_key:
        print("Azure Document Intelligence credentials not found in .env file.")
        return
    
    try:
        # Initialize processor
        processor = PDFProcessor(endpoint=endpoint, api_key=api_key)
        
        # Extract invoice data
        print("Extracting data...")
        extracted_data = processor.extract_invoice(pdf_path)
        
        # Print raw fields extracted by Azure
        print("\nRaw fields extracted by Azure:")
        fields = extracted_data.get("fields", {})
        for field_name, field_data in fields.items():
            if isinstance(field_data, dict) and "value" in field_data:
                print(f"  {field_name}: {field_data['value']}")
            else:
                print(f"  {field_name}: {field_data}")
        
        # Normalize data
        print("\nNormalizing extracted data...")
        normalizer = PDFNormalizer()
        normalized_invoices = normalizer.normalize(extracted_data)
        
        # Print normalized invoice data
        print("\nNormalized invoice data:")
        for i, invoice in enumerate(normalized_invoices):
            print(f"\nInvoice {i+1}:")
            for key, value in invoice.items():
                if key != "raw_data":  # Skip raw data to keep output clean
                    print(f"  {key}: {value}")
        
        return normalized_invoices
    
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Test British Gas bill
    british_gas_invoice = test_extraction_accuracy("british gas energy bill.pdf")
    
    # Test E.ON bill
    eon_invoice = test_extraction_accuracy("EonElectricityBill.pdf")
    
    # Test Opus invoice
    opus_invoice = test_extraction_accuracy("Opus-Invoice.pdf")