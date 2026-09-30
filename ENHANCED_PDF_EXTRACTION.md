# Enhanced PDF Extraction

This document explains the enhanced PDF extraction features implemented in Phase 2 of the Valix project.

## Overview

The enhanced PDF extraction system improves the accuracy and reliability of extracting data from invoice PDFs by:

1. **Supplier-Specific Extraction Patterns**: Custom regex patterns for different suppliers and fields
2. **Multi-Method Extraction**: Multiple approaches to extract each field
3. **Confidence Scoring**: Assessing the reliability of extracted data
4. **Manual Review Queue**: Handling invoices that can't be automatically processed

## Multi-Tenant Architecture

This implementation fully supports the existing multi-tenant architecture:

- All new tables include `tenant_id` columns
- Proper foreign key constraints to the `tenants` table
- Row-level security policies for tenant isolation in Supabase
- Tenant-specific and global extraction patterns
- Proper tenant filtering in all queries

## Components

### 1. Supplier Extraction Patterns

The system uses a database of supplier-specific extraction patterns to improve data extraction accuracy. These patterns are stored in the `supplier_extraction_patterns` table.

Each pattern includes:
- Tenant ID (NULL for global patterns, specific tenant ID for tenant-specific patterns)
- Supplier name (e.g., "British Gas", "E.ON")
- Field name (e.g., "supplier_account_number", "billing_period_start")
- Pattern type (e.g., "regex", "xpath", "table_cell")
- Pattern value (the actual pattern)
- Priority (higher priority patterns are tried first)

Example patterns:
```
British Gas account number: r'customer\s+reference\s+number[\s:]+([0-9\s-]{6,})'
E.ON billing period: r'billing\s+period[\s:]+(\d{1,2}\s+[A-Za-z]{3}\s+\d{2})\s*[-–]\s*(\d{1,2}\s+[A-Za-z]{3}\s+\d{2})'
```

### 2. Enhanced PDF Processor

The `EnhancedPDFProcessor` class in `app/enhanced_pdf_processor.py` extends the basic PDF processor with:

- Supplier detection
- Application of supplier-specific patterns
- Multi-method extraction
- Confidence scoring
- Field validation

### 3. Manual Review Queue

The system includes a manual review queue for invoices that:
- Have low confidence scores
- Are missing required fields
- Have conflicting or ambiguous data

The queue is managed through the `ManualReviewQueue` model and the `app/manual_review.py` module.

## Workflow

1. **PDF Upload**: User uploads an invoice PDF
2. **Azure Extraction**: Azure Document Intelligence extracts raw data
3. **Supplier Detection**: System detects the supplier from the extracted data
4. **Enhanced Extraction**: 
   - Apply supplier-specific patterns
   - Use multi-method extraction
   - Calculate confidence scores
5. **Validation**:
   - Check required fields
   - Validate field formats
   - Assess overall confidence
6. **Decision**:
   - If valid: Process invoice normally
   - If invalid: Queue for manual review

## Manual Review Process

1. **Queue**: Invoices with low confidence or missing fields are added to the queue
2. **Review**: Users review these invoices in the UI
3. **Correction**: Users can correct extracted data
4. **Processing**: Once corrected, invoices are processed normally

## Managing Extraction Patterns

Users can manage extraction patterns through the UI:
- View existing patterns
- Add new patterns
- Edit patterns
- Import/export patterns using Excel templates

## Default Patterns

The system includes default patterns for common suppliers:
- British Gas
- E.ON
- Opus Energy
- Generic patterns (lower priority)

Run `python scripts/init_extraction_patterns.py` to initialize these patterns.

## Testing and Validation

Use the following scripts to test the enhanced extraction:

- `scripts/test_enhanced_extraction.py`: Test extraction on a specific PDF
- `scripts/test_manual_review.py`: Test the manual review queue

## Configuration

Confidence thresholds for different fields can be configured in the `EnhancedPDFProcessor` class:

```python
CONFIDENCE_THRESHOLDS = {
    "invoice_number": 0.7,
    "supplier_name": 0.8,
    "supplier_account_number": 0.8,  # Critical field
    "billing_period_start": 0.7,
    "billing_period_end": 0.7,
    "invoice_date": 0.6,
    "gross_amount": 0.8,  # Critical field
    "default": 0.6  # Default threshold for other fields
}
```

## Implementation Steps

1. Create database models:
   - `SupplierExtractionPattern`
   - `ManualReviewQueue`

2. Create database migrations:
   - `migrations/add_enhanced_pdf_extraction_tables.sql`
   - Includes proper tenant isolation and row-level security for Supabase

3. Implement core modules:
   - `app/extraction_patterns.py`
   - `app/manual_review.py`
   - `app/enhanced_pdf_processor.py`

4. Update existing code:
   - `app/pdf_workflow.py`

5. Create UI routes and templates:
   - `app/routes/extraction_patterns.py`
   - `app/routes/manual_review.py`
   - `templates/extraction_patterns.html`
   - `templates/manual_review.html`
   - `templates/manual_review_item.html`

6. Create utility scripts:
   - `scripts/init_extraction_patterns.py`
   - `scripts/test_enhanced_extraction.py`
   - `scripts/test_manual_review.py`
   - `scripts/migrate_enhanced_extraction_tables.py`

## Applying the Migration

To apply the migration to your Supabase database:

1. Run the migration script:
   ```
   python scripts/migrate_enhanced_extraction_tables.py
   ```

2. The script will:
   - Apply the SQL migration to create the new tables
   - Set up proper tenant isolation with row-level security
   - Create default extraction patterns

3. Alternatively, you can apply the migration manually:
   - Go to the Supabase dashboard
   - Open the SQL Editor
   - Copy and paste the contents of `migrations/add_enhanced_pdf_extraction_tables.sql`
   - Execute the SQL
   - Then run `python scripts/init_extraction_patterns.py` to create default patterns