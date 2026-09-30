# Commercial Property Invoice Validator

AI-assisted invoice validation tool for commercial property portfolios.

## Project Status

**Phase 1** ✅ - Foundation: Data model and CSV loading  
**Phase 2** ✅ - Validation engine with rules  
**Phase 4** ✅ - FastAPI web UI (Phase 3 - AI explanations skipped for now)

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

2. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Initialize the database:
   ```bash
   python -m app.db
   ```
   This creates `app.db` in the project root with all required tables.

## Important Version Notes

This project requires specific versions of FastAPI, Starlette, and Jinja2 to avoid template rendering issues:

- fastapi==0.95.1
- starlette==0.26.1
- jinja2==3.0.3
- pydantic<2.0.0

If you encounter a `TypeError: cannot use 'tuple' as a dict key (unhashable type: 'dict')` error when rendering templates, ensure you're using these exact versions.

## Usage

### Loading Invoice CSV Files

Create a CSV file in `data/sample_invoices.csv` (or provide a path) with the following columns:

- `invoice_number` (required)
- `supplier_name` (required)
- `unit_id` (required)
- `billing_period_start` (required, format: YYYY-MM-DD or DD/MM/YYYY)
- `billing_period_end` (required, format: YYYY-MM-DD or DD/MM/YYYY)
- `invoice_date` (optional, format: YYYY-MM-DD or DD/MM/YYYY)
- `gross_amount` (required, numeric)
- `net_amount` (optional, numeric)
- `vat_amount` (optional, numeric)
- `utility_type` (required, e.g., 'Electricity', 'Gas', 'Water')
- `currency` (optional, defaults to 'GBP')
- `source_batch` (optional)

Then run:
```bash
python scripts/load_invoices.py [path_to_csv_file]
```

If no path is provided, it defaults to `data/sample_invoices.csv`.

### Validating Invoices

After loading invoices and setting up units/leases, you can validate invoices:

```bash
python scripts/validate_invoices.py [batch_number]
```

If `batch_number` is provided, only validates invoices from that batch. Otherwise, validates all invoices.

The validation engine will:
1. Generate unit timeline (vacancy periods) from leases
2. Check for duplicate invoices
3. Calculate invoice-vacancy overlap
4. Determine validation status (Valid/Invalid/Needs Review)
5. Generate final determinations (OK TO PAY, DO NOT PAY, COT, etc.)

Results are saved to the `invoice_validation` table.

### Running the FastAPI Web Application

```bash
uvicorn main:app --reload
```

Then visit:
- **Web UI**: `http://localhost:8000/invoices` - View and manage invoices
- **API Docs**: `http://localhost:8000/docs` - Interactive API documentation
- **API Root**: `http://localhost:8000` - API information

### Loading Sample Data

To test the system with sample data:

```bash
# 1. Load sample units and leases
python scripts/load_sample_data.py

# 2. Load invoices
python scripts/load_invoices.py

# 3. Validate invoices
python scripts/validate_invoices.py

# 4. Start the web app
uvicorn main:app --reload
```

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── config.py          # Configuration settings
│   ├── db.py              # Database connection and session management
│   ├── models.py          # SQLAlchemy models (Invoice, Unit, Lease, UnitTimeline, InvoiceValidation)
│   ├── schemas.py         # Pydantic schemas (for future API use)
│   └── validation.py      # Validation engine logic
├── scripts/
│   ├── load_invoices.py   # CSV loading script
│   └── validate_invoices.py  # Invoice validation script
├── data/
│   └── sample_invoices.csv # Sample CSV file (create this)
├── main.py                # FastAPI application entry point
├── requirements.txt       # Python dependencies
└── app.db                # SQLite database (created after initialization)
```

## Data Models

### Invoice
Stores invoice records with billing periods, amounts, and supplier information.

### Unit
Commercial property units (shops, offices, etc.) with address information.

### Lease
Lease periods linking units to tenants with start/end dates.

### UnitTimeline
Derived table showing occupied/vacant periods for each unit. Generated from Units + Leases.

### InvoiceValidation
Validation results for each invoice, including:
- Validation status (Valid/Invalid/Needs Review)
- Vacancy overlap calculations
- Duplicate detection
- Daily rate calculations
- Final determination (OK TO PAY, DO NOT PAY, COT, etc.)

## Validation Rules

The validation engine implements the following checks:

1. **Duplicate Detection**: Checks for duplicate invoices based on `invoice_number` + `gross_amount`
2. **Vacancy Overlap**: Calculates days of overlap between invoice billing period and vacancy periods
3. **Validation Status**: Determines if invoice is Valid, Invalid, or Needs Review
4. **Determinations**: Applies business rules to generate final determinations:
   - **OK TO PAY**: Valid invoice, unpaid, daily rate < £4
   - **OK TO PAY, SUBMIT METER READING**: Valid invoice, unpaid, daily rate £4-£10
   - **DO NOT PAY, SUBMIT METER READING**: Valid invoice, unpaid, daily rate >= £10
   - **COT** (Check on This): Needs Review or Invalid invoice
   - **CREDIT OWED**: Invalid invoice that was already paid
   - **Landlord Supply - OK TO PAY**: Unit ending in '00'
   - And more...

## API Endpoints

### Web UI
- `GET /invoices` - View all invoices in a web interface
- `GET /invoice/{invoice_id}` - View detailed invoice information

### REST API
- `GET /api/invoices` - List invoices with validation results (supports filtering)
- `GET /api/invoices/{invoice_id}` - Get single invoice details
- `POST /api/validate` - Trigger validation for invoices
- `GET /api/stats` - Get validation statistics

### Example API Usage

```bash
# List all invoices
curl http://localhost:8000/api/invoices

# Get validation stats
curl http://localhost:8000/api/stats

# Validate all invoices
curl -X POST http://localhost:8000/api/validate \
  -H "Content-Type: application/json" \
  -d '{"batch_number": null}'
```

## Next Steps (Future Phases)

- Phase 3: AI-generated explanations (skipped for now)
- Phase 5: PDF ingestion via OCR