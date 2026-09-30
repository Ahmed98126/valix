# Client Onboarding Guide

## Welcome to Invoice Validator!

This guide will walk you through setting up your account and importing your data.

---

## Step 1: Create Your Account

1. Go to the signup page
2. Enter your details:
   - **Email:** Your business email
   - **Password:** Choose a secure password
   - **Full Name:** Your name
   - **Organization Name:** Your company name (e.g., "ABC Property Management")
3. Click "Sign Up"
4. You'll be automatically logged in

**✅ Done!** You now have your own secure workspace.

---

## Step 2: Import Your Units

Units are the properties/spaces you manage (shops, offices, etc.).

### What You Need:
An Excel or CSV file with your units data.

### Required Columns:
- **unit_id** - Unique identifier (e.g., "SHOP-001", "OFFICE-101")
- **building_name** - Name of the building
- **address_line_1** - Street address
- **city** - City name
- **postcode** - Postal code

### Optional Columns:
- **address_line_2** - Additional address line

### Example Excel Format:
```
unit_id    | building_name              | address_line_1      | city      | postcode
SHOP-001   | High Street Shopping Centre | 123 High Street    | London    | SW1A 1AA
SHOP-002   | High Street Shopping Centre | 123 High Street    | London    | SW1A 1AA
OFFICE-101 | Business Park Tower         | 456 Business Park  | Manchester| M1 1AA
```

### How to Import:
1. Go to **"Import Units"** in the sidebar
2. Click "Upload a file" or drag and drop your Excel/CSV file
3. Click "Import Units"
4. Wait for confirmation message

**✅ Done!** Your units are now in the system.

---

## Step 3: Import Your Leases

Leases show when each unit was occupied by a tenant.

### What You Need:
An Excel or CSV file with your lease data.

### Required Columns:
- **unit_id** - Must match a unit you imported (e.g., "SHOP-001")
- **tenant_name** - Name of the tenant/company
- **lease_start** - Start date (YYYY-MM-DD or DD/MM/YYYY)
- **lease_end** - End date (YYYY-MM-DD or DD/MM/YYYY). Leave empty for ongoing leases

### Example Excel Format:
```
unit_id    | tenant_name      | lease_start  | lease_end
SHOP-001   | Coffee Shop Ltd  | 2024-01-01   | (empty for ongoing)
SHOP-002   | Bakery Corp      | 2023-12-02   | 2025-09-02
SHOP-002   | Tech Store Inc   | 2025-12-31   | (empty for ongoing)
```

### How to Import:
1. Go to **"Import Leases"** in the sidebar
2. Click "Upload a file" or drag and drop your Excel/CSV file
3. Click "Import Leases"
4. Wait for confirmation message

**✅ Done!** Your leases are imported and unit timelines are automatically generated.

---

## Step 4: Configure Column Mappings (If Needed)

**When to do this:** Only if your Excel column names are different from the standard ones.

### Example:
Your Excel uses:
- `Invoice Number` instead of `invoice_number`
- `Vendor` instead of `supplier_name`
- `Property Code` instead of `unit_id`

### How to Configure:
1. Go to **"Settings"** in the sidebar
2. Scroll to "Column Mappings"
3. Edit the mappings to match your Excel column names
4. Click "Save Column Mappings"

**✅ Done!** The system will now recognize your column names.

---

## Step 5: Upload and Validate Invoices

Now you're ready to validate invoices!

### What You Need:
An Excel or CSV file with invoice data.

### Required Columns:
- **invoice_number** - Invoice number
- **supplier_name** - Supplier/vendor name
- **unit_id** - Must match a unit you imported
- **billing_period_start** - Start date (YYYY-MM-DD or DD/MM/YYYY)
- **billing_period_end** - End date (YYYY-MM-DD or DD/MM/YYYY)
- **gross_amount** - Total invoice amount
- **utility_type** - Type (Electricity, Gas, Water, etc.)

### Optional Columns:
- **invoice_date** - Invoice date
- **net_amount** - Net amount
- **vat_amount** - VAT amount
- **currency** - Currency code

### How to Upload:
1. Go to **"Upload Invoices"** in the sidebar
2. Click "Upload a file" or drag and drop your Excel/CSV file
3. Click "Upload and Validate"
4. Watch the progress bar
5. When complete, view results in **"Invoices"** page

**✅ Done!** Your invoices are validated!

---

## Step 6: View Results

### Dashboard:
- See summary statistics
- View recent invoices
- Check validation status breakdown

### Invoices Page:
- View all invoices
- Filter by:
  - **Status:** Valid, Invalid, Needs Review
  - **Determination:** OK TO PAY, DO NOT PAY, COT, etc.
  - **Batch:** Filter by upload batch
- Export filtered results to CSV
- Click "View" to see detailed validation information

### Data Management:
- View all your units and leases
- Edit unit/lease information
- Delete units/leases (if needed)

---

## Understanding Validation Results

### Status Types:
- **Valid:** Invoice is valid (landlord liable)
- **Invalid:** Invoice is invalid (tenant liable)
- **Needs Review:** Requires manual review

### Common Determinations:
- **OK TO PAY:** Invoice is valid, proceed with payment
- **DO NOT PAY:** Invoice is invalid, do not pay
- **COT:** Check Other Things - needs review
- **Landlord Supply - OK TO PAY:** Unit is vacant, landlord pays utilities

---

## Troubleshooting

### "Missing required columns" Error:
- Check your Excel has all required columns
- Column names must match (case-insensitive)
- Go to Settings to configure column mappings if needed

### "Invalid unit_id" Error:
- Make sure the unit_id in your invoice file matches a unit you imported
- Check for typos or extra spaces

### "Duplicate invoice" Warning:
- This invoice was already uploaded before
- Duplicates are skipped automatically

### Need Help?
Contact support with:
- Your organization name
- Screenshot of the error
- Sample of your Excel file (first few rows)

---

## Quick Reference

### Login:
- URL: Your system URL
- Email: Your registered email
- Password: Your password

### Key Pages:
- **Dashboard:** Overview and statistics
- **Upload Invoices:** Upload new invoices
- **Import Units:** Import property units
- **Import Leases:** Import lease data
- **Data Management:** View/edit units and leases
- **Invoices:** View all invoices and results
- **Settings:** Configure column mappings

### Data Requirements:
- **Units:** unit_id, building_name, address_line_1, city, postcode
- **Leases:** unit_id, tenant_name, lease_start, lease_end
- **Invoices:** invoice_number, supplier_name, unit_id, billing_period_start, billing_period_end, gross_amount, utility_type

---

## Next Steps

1. ✅ Complete Steps 1-3 (Account, Units, Leases)
2. ✅ Upload your first invoice batch
3. ✅ Review validation results
4. ✅ Export results for your records
5. ✅ Set up regular invoice uploads

**You're all set!** 🎉


