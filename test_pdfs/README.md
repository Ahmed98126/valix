# PDF Extraction Testing Guide

This directory contains tools and sample PDFs for testing the extraction accuracy of the invoice validation system.

## Available Scripts

### 1. Test PDF Extraction

Tests the extraction of a single PDF file and displays the results:

```bash
python scripts/test_pdf_extraction.py path/to/invoice.pdf [--enhanced] [--save]
```

Options:
- `--enhanced`: Use enhanced extraction with supplier patterns
- `--save`: Save extraction results to JSON files in the `test_results` directory

Example:
```bash
python scripts/test_pdf_extraction.py test_pdfs/BATCH_20251230_212454_3ce656e5_EonElectricityBill.pdf --enhanced
```

### 2. Evaluate Extraction Accuracy

Compares extracted data with expected values to measure accuracy:

```bash
python scripts/evaluate_extraction.py path/to/invoice.pdf --expected path/to/expected.json [--enhanced]
```

Options:
- `--enhanced`: Use enhanced extraction with supplier patterns
- `--create-template`: Create a template JSON file with expected values

Example:
```bash
# First create a template with the current extraction results
python scripts/evaluate_extraction.py test_pdfs/BATCH_20251230_212454_3ce656e5_EonElectricityBill.pdf --create-template --expected test_pdfs/eon_expected.json

# Edit the template with correct expected values, then evaluate
python scripts/evaluate_extraction.py test_pdfs/BATCH_20251230_212454_3ce656e5_EonElectricityBill.pdf --expected test_pdfs/eon_expected.json --enhanced
```

### 3. Batch Test Multiple PDFs

Processes multiple PDF files and generates a summary report:

```bash
python scripts/batch_test_pdfs.py --input-dir path/to/pdfs [--enhanced] [--output-dir path/to/output]
```

Options:
- `--enhanced`: Use enhanced extraction with supplier patterns
- `--pattern`: Glob pattern to match PDF files (default: `*.pdf`)
- `--limit`: Limit number of PDFs to process
- `--output-dir`: Directory to save results (default: `batch_results`)

Example:
```bash
python scripts/batch_test_pdfs.py --input-dir test_pdfs --enhanced --output-dir test_pdfs/batch_results
```

## Testing Workflow

1. **Collect Sample PDFs**: Gather a diverse set of invoice PDFs from different suppliers
2. **Initial Extraction**: Run the test script on each PDF to see what data is extracted
3. **Create Expected Values**: Create templates with the correct expected values for each PDF
4. **Evaluate Accuracy**: Compare extraction results with expected values
5. **Identify Issues**: Note fields with low extraction accuracy
6. **Improve Extraction**: Enhance the extraction patterns and algorithms
7. **Re-evaluate**: Test again to measure improvement

## Key Metrics to Track

- **Overall Accuracy**: Percentage of fields correctly extracted across all PDFs
- **Field-Specific Accuracy**: Accuracy for each field (invoice number, account number, etc.)
- **Supplier-Specific Accuracy**: Accuracy for each supplier's invoices
- **Confidence Scores**: Average confidence scores for each field

## Common Issues and Solutions

- **Missing Account Numbers**: Check if the account number appears in a different format or location
- **Incorrect Billing Periods**: Verify date format patterns in the normalizer
- **Address Extraction Issues**: Review address patterns for different suppliers
- **Low Confidence Scores**: Consider adding more specific extraction patterns for the supplier

## Adding New Supplier Patterns

If you identify a new invoice format that isn't being extracted correctly:

1. Create a new supplier-specific extraction pattern in `app/supplier_extraction_patterns.py`
2. Test with sample PDFs from that supplier
3. Adjust patterns based on test results
4. Add to the database using the extraction patterns UI