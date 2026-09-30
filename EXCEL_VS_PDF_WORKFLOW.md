# Excel vs PDF Invoice Processing: Complete Comparison

## Overview

Your system supports **two invoice input methods**:
1. **Excel/CSV Upload** - Structured data from spreadsheets
2. **PDF Upload** - Unstructured invoices from suppliers (British Gas, E.ON, Opus Energy)

Both methods go through the same validation engine, but the extraction and mapping steps differ.

---

## Excel/CSV Invoice Workflow

### Step 1: Prepare Excel/CSV File
**Client Action:**
- Export invoices from their accounting system or create a spreadsheet
- Ensure required columns are present:
  - `invoice_number` (required)
  - `supplier_account_number` (required)
  - `supplier_name` (required)
  - `unit_id` (required) - **Client provides this directly**
  - `billing_period_start` (required)
  - `billing_period_end` (required)
  - `gross_amount` (required)
  - `utility_type` (required)
  - Optional: `net_amount`, `vat_amount`, `invoice_date`, `currency`

**Example Excel Structure:**
```
invoice_number | supplier_account_number | supplier_name | unit_id | billing_period_start | billing_period_end | gross_amount | utility_type
INV-001        | 1234 1234 1234          | British Gas   | SHOP-001| 2024-01-01          | 2024-01-31        | 150.00       | Electricity
```

### Step 2: Upload Excel/CSV
**Client Action:**
- Navigate to `/upload`
- Select Excel (.xlsx, .xls) or CSV file
- Click "Upload and Validate"

**System Processing:**
1. Reads file and maps columns (using tenant's column mapping config)
2. Validates required columns are present
3. Parses dates and amounts
4. **Uses `unit_id` directly from Excel** (no matching needed)
5. Creates Invoice records in database
6. Runs validation engine
7. Returns results

### Step 3: Review Results
**Client Action:**
- View invoices at `/invoices`
- Check validation status (Valid/Invalid/Needs Review)
- Review determination (OK TO PAY/DO NOT PAY/COT)

**Key Characteristics:**
- ✅ **Fast** - No AI extraction needed
- ✅ **Accurate** - Client controls the data
- ✅ **Requires unit_id** - Client must know which unit each invoice belongs to
- ✅ **Best for**: Bulk imports, structured data, clients with unit IDs

---

## PDF Invoice Workflow

### Step 1: Collect PDF Invoices
**Client Action:**
- Download invoices from supplier portals (British Gas, E.ON, Opus Energy)
- Save PDF files locally
- No data entry needed!

**Example PDFs:**
- `british_gas_invoice_jan_2024.pdf`
- `eon_electricity_feb_2024.pdf`
- `opus_energy_march_2024.pdf`

### Step 2: Upload PDF(s)
**Client Action:**
- Navigate to `/upload`
- Select PDF file(s) or drag and drop
- Click "Upload and Validate"

**System Processing:**
1. **PDF Extraction** (Azure Document Intelligence)
   - Extracts text, tables, and structured fields
   - Identifies supplier (British Gas, E.ON, Opus, etc.)
   - Extracts: invoice number, account number, dates, amounts, addresses

2. **Normalization** (PDF Normalizer)
   - Converts Azure output to your Invoice schema
   - Supplier-specific rules (British Gas, E.ON, Opus patterns)
   - Extracts: billing period, account number, supply address

3. **Unit Mapping** (InvoiceUnitMapper)
   - **Strategy 1**: Exact unit_id match (if invoice has unit_id)
   - **Strategy 2**: Account number mapping (custom mappings)
   - **Strategy 3**: Address similarity matching (fuzzy match)
   - **Strategy 4**: Manual mapping (if needed)

4. **Invoice Creation**
   - Creates Invoice records with matched unit_id
   - Stores extracted address for reference

5. **Validation**
   - Runs validation engine
   - Returns results

### Step 3: Review Results
**Client Action:**
- View invoices at `/invoices`
- Check if unit_id was matched correctly
- Review validation status
- **Manual mapping** if unit_id is "UNKNOWN" or incorrect

**Key Characteristics:**
- ✅ **No data entry** - Fully automated
- ✅ **Handles variations** - Different supplier formats
- ✅ **Smart matching** - Address-based unit matching
- ⚠️ **May need review** - Low-confidence matches flagged
- ✅ **Best for**: PDF invoices, clients without unit IDs, UK utility bills

---

## Key Differences

| Aspect | Excel/CSV | PDF |
|--------|-----------|-----|
| **Data Entry** | Client must prepare spreadsheet | No data entry needed |
| **Unit ID** | Client provides in Excel | System matches automatically |
| **Speed** | Fast (direct import) | Slower (AI extraction) |
| **Accuracy** | High (client controls data) | High (AI + validation) |
| **Cost** | Free | Azure API costs per page |
| **Best For** | Bulk imports, structured data | PDF invoices, automation |
| **Address Matching** | Not needed (unit_id provided) | Automatic (address similarity) |
| **Manual Mapping** | Rarely needed | May be needed for low-confidence matches |

---

## Combined Workflow (Real-World Scenario)

**Typical client workflow:**

1. **Initial Setup**
   - Import units (`/import-units`)
   - Import leases (`/import-leases`)
   - Configure column mappings if needed (`/settings`)

2. **Monthly Invoice Processing**
   - **Option A**: Upload Excel with all invoices (if they have unit IDs)
   - **Option B**: Upload PDFs from suppliers (if they don't have unit IDs)
   - **Option C**: Mix of both (some Excel, some PDF)

3. **Review & Validation**
   - Check unmapped invoices (unit_id = "UNKNOWN")
   - Manually map if needed
   - Review validation results
   - Export for payment processing

---

## System Architecture

```
┌─────────────────┐
│  Client Upload  │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼────┐
│ Excel │ │  PDF │
│  CSV  │ │      │
└───┬───┘ └──┬────┘
    │        │
    │   ┌────▼──────────────┐
    │   │ Azure Document    │
    │   │ Intelligence       │
    │   └────┬──────────────┘
    │        │
    │   ┌────▼──────────────┐
    │   │ PDF Normalizer    │
    │   │ (Supplier Rules)  │
    │   └────┬──────────────┘
    │        │
    └────────┴────────┐
                      │
            ┌─────────▼─────────┐
            │  InvoiceUnitMapper│
            │  (4 Strategies)   │
            └─────────┬─────────┘
                      │
            ┌─────────▼─────────┐
            │  Invoice Creation │
            └─────────┬─────────┘
                      │
            ┌─────────▼─────────┐
            │ Validation Engine │
            └─────────┬─────────┘
                      │
            ┌─────────▼─────────┐
            │  Results Display  │
            └───────────────────┘
```

---

## Next Steps for Testing

See `TESTING_AND_CLIENT_ONBOARDING.md` for detailed testing strategy and client onboarding guide.

