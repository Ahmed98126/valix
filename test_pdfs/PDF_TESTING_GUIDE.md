# PDF Extraction Testing Guide

This guide outlines the process for testing PDF extraction accuracy in the invoice validation system.

## Testing Approach

Since the PDF extraction is working through the application's UI, we'll use that as our primary testing method. This approach allows us to test the entire workflow from upload to validation.

## Testing Process

### 1. Collect Sample PDFs

Gather a diverse set of invoice PDFs from different suppliers:

- **Current Samples**: E.ON electricity bills (in the `test_pdfs` directory)
- **Needed Samples**:
  - British Gas
  - SSE
  - Octopus Energy
  - Water suppliers
  - Other common utility providers

### 2. Document Expected Values

For each test PDF:

1. Manually review the PDF and record the expected values in the `extraction_test_results.csv` spreadsheet
2. Include at minimum:
   - Invoice number
   - Supplier account number
   - Billing period start/end
   - Invoice amount
   - Address/unit information

### 3. Test Through UI

For each test PDF:

1. Log in to the application
2. Navigate to the Upload page
3. Upload the PDF file
4. Wait for processing to complete
5. Navigate to the Invoices page
6. Find the newly created invoice
7. Compare the extracted values with the expected values
8. Record the results in the spreadsheet

### 4. Analyze Results

After testing multiple PDFs:

1. Calculate extraction accuracy for each field
2. Identify patterns in extraction failures
3. Determine which suppliers have the lowest extraction accuracy
4. Note fields that consistently fail across suppliers

### 5. Improve Extraction Patterns

Based on the analysis:

1. Update supplier-specific extraction patterns in the code
2. Add new patterns for suppliers with poor extraction results
3. Improve regex patterns for problematic fields
4. Re-test to verify improvements

## Testing Metrics

Track the following metrics:

- **Overall Accuracy**: Percentage of fields correctly extracted across all PDFs
- **Field-Specific Accuracy**: Accuracy for each field (invoice number, account number, etc.)
- **Supplier-Specific Accuracy**: Accuracy for each supplier's invoices

## Common Issues to Watch For

- **Account Number Extraction**: Suppliers format account numbers differently
- **Billing Period Detection**: Date formats vary between suppliers
- **Address Extraction**: Address formats and placement vary significantly
- **Multi-Page Invoices**: Some information may be on different pages
- **Table Extraction**: Line items and tables may not extract correctly

## Supplier-Specific Notes

### E.ON Energy

- Account numbers typically formatted as: `1234 5678 90`
- Billing period often found near the top of the invoice
- Supply address format: "For electricity supplied to [address]"

### British Gas

- Customer reference number format: `1234 5678 9012`
- Billing period format: "Bill period: 25 Nov 09 - 03 Mar 10"
- Supply address format: "Supply address: [address]"

## Next Steps After Testing

1. **Document Findings**: Create a detailed report of extraction accuracy
2. **Prioritize Improvements**: Focus on high-impact, low-accuracy areas
3. **Update Extraction Code**: Modify patterns based on findings
4. **Add New Supplier Patterns**: Create patterns for suppliers not currently supported
5. **Re-test**: Verify improvements with the same test set