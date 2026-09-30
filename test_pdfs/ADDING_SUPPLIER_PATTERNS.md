# Adding Supplier-Specific Extraction Patterns

This guide explains how to add new supplier-specific extraction patterns to improve PDF extraction accuracy.

## Understanding Extraction Patterns

Extraction patterns are supplier-specific regex patterns and rules that help extract data from invoices more accurately. They're particularly useful for:

1. Account numbers in non-standard formats
2. Billing periods with unusual date formats
3. Invoice numbers in supplier-specific locations
4. Addresses with unique formatting

## Adding Patterns Through the UI

The easiest way to add patterns is through the application's UI:

1. Log in to the application
2. Navigate to "Extraction Patterns" in the sidebar
3. Click "Add New Pattern"
4. Fill in the following fields:
   - **Supplier Name**: The supplier's name (e.g., "British Gas", "E.ON")
   - **Field Name**: The field to extract (e.g., "supplier_account_number", "billing_period_start")
   - **Pattern Type**: Usually "regex" for regular expressions
   - **Pattern Value**: The regex pattern to match the field
   - **Priority**: Higher numbers are tried first (1-100)
   - **Description**: A clear explanation of what the pattern matches

## Pattern Types

### Regex Patterns

Most patterns use regular expressions to extract data from the invoice text:

```json
{
  "type": "regex",
  "pattern": "account\\s+number[\\s:]+([0-9\\s-]{6,})",
  "flags": "i"
}
```

The pattern should include a capturing group `()` that extracts the actual value.

### Field Mapping Patterns

For mapping Azure field names to our schema:

```json
{
  "type": "field_mapping",
  "azure_fields": ["CustomerAccountNumber", "AccountNumber", "Account"],
  "fallback_to_content": true
}
```

### Table Extraction Patterns

For extracting data from tables:

```json
{
  "type": "table",
  "row_match": "billing period",
  "column_index": 1,
  "table_index": 0
}
```

## Example Patterns by Supplier

### E.ON Energy

#### Account Number Pattern
```json
{
  "type": "regex",
  "pattern": "your\\s+account\\s+number[\\s:]+([0-9]{4}\\s+[0-9]{4}\\s+[0-9]{2})",
  "flags": "i"
}
```

#### Billing Period Pattern
```json
{
  "type": "regex",
  "pattern": "(\\d{1,2}\\s+[A-Za-z]{3}\\s+\\d{2})\\s+to\\s+(\\d{1,2}\\s+[A-Za-z]{3}\\s+\\d{2})",
  "flags": "i"
}
```

### British Gas

#### Customer Reference Pattern
```json
{
  "type": "regex",
  "pattern": "customer\\s+reference\\s+number[\\s:]+([0-9]{4}\\s+[0-9]{4}\\s+[0-9]{4})",
  "flags": "i"
}
```

#### Supply Address Pattern
```json
{
  "type": "regex",
  "pattern": "supply\\s+address[\\s:]+([^\\n]+(?:\\n[^\\n]+){0,2})",
  "flags": "i"
}
```

## Testing New Patterns

After adding a new pattern:

1. Upload a test PDF from the supplier
2. Check if the field is extracted correctly
3. If not, adjust the pattern and try again
4. Use the "Test Pattern" feature in the UI to validate the pattern against sample text

## Best Practices

1. **Start Specific**: Begin with specific patterns that match exactly what you see in the invoice
2. **Add Variations**: If the pattern doesn't match all invoices from the supplier, add variations
3. **Use Capturing Groups**: Make sure your regex has capturing groups `()` to extract the actual value
4. **Set Priorities**: Give more specific patterns higher priority
5. **Document Patterns**: Add clear descriptions to help others understand the pattern
6. **Test Thoroughly**: Test with multiple invoices from the same supplier

## Common Fields to Extract

Focus on these critical fields for each supplier:

1. **supplier_account_number**: The account number used by the supplier
2. **invoice_number**: The unique invoice identifier
3. **billing_period_start** and **billing_period_end**: The service period dates
4. **address**: The service/supply address
5. **gross_amount**: The total invoice amount

## Debugging Extraction Issues

If extraction is failing:

1. Check the raw extraction data to see what text is available
2. Test your regex patterns against the actual text
3. Adjust patterns to be more flexible if needed
4. Consider adding multiple patterns with different priorities
5. Use the manual review queue for invoices that can't be automatically processed