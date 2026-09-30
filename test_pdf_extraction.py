"""Test PDF extraction with Azure Document Intelligence."""

import os
import json
from dotenv import load_dotenv
from app.pdf_processor import PDFProcessor
from app.pdf_normalizer import PDFNormalizer

# Load environment variables from .env file
load_dotenv()

def test_extraction(pdf_path):
    """Test extraction of a PDF invoice."""
    print(f"Testing extraction of {pdf_path}...")
    
    # Check if Azure credentials are set
    endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
    api_key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_API_KEY")
    
    if not endpoint or not api_key:
        print("Azure Document Intelligence credentials not found in .env file.")
        return
    
    print(f"Azure Document Intelligence endpoint: {endpoint[:30]}...")
    
    try:
        # Initialize processor
        processor = PDFProcessor(endpoint=endpoint, api_key=api_key)
        print("PDF Processor initialized successfully.")
        
        # Extract invoice data
        print(f"Extracting data from {pdf_path}...")
        extracted_data = processor.extract_invoice(pdf_path)
        print("Extraction successful!")
        
        # Normalize data
        print("Normalizing extracted data...")
        normalizer = PDFNormalizer()
        normalized_invoices = normalizer.normalize(extracted_data)
        
        # Print results
        print(f"Normalized {len(normalized_invoices)} invoice(s):")
        for i, invoice in enumerate(normalized_invoices):
            print(f"\nInvoice {i+1}:")
            print(f"  Invoice Number: {invoice.get('invoice_number')}")
            print(f"  Supplier: {invoice.get('supplier_name')}")
            print(f"  Account Number: {invoice.get('supplier_account_number')}")
            print(f"  Unit ID: {invoice.get('unit_id')}")
            print(f"  Address: {invoice.get('address')}")
            print(f"  Billing Period: {invoice.get('billing_period_start')} to {invoice.get('billing_period_end')}")
            print(f"  Invoice Date: {invoice.get('invoice_date')}")
            print(f"  Gross Amount: {invoice.get('gross_amount')}")
            print(f"  Net Amount: {invoice.get('net_amount')}")
            print(f"  VAT Amount: {invoice.get('vat_amount')}")
            print(f"  Utility Type: {invoice.get('utility_type')}")
            print(f"  Currency: {invoice.get('currency')}")
        
        return normalized_invoices
    
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Test British Gas bill
    british_gas_invoice = test_extraction("british gas energy bill.pdf")
    
    # Test E.ON bill
    eon_invoice = test_extraction("EonElectricityBill.pdf")
    
    # Test Opus invoice
    opus_invoice = test_extraction("Opus-Invoice.pdf")