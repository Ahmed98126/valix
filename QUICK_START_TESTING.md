# Quick Start: Testing the Invoice Validation System

## 🚀 One-Command Setup

Run this to set up everything for testing:

```bash
python scripts/test_workflow.py --comprehensive
```

This will:
- ✅ Load 20+ units and 30+ leases (comprehensive portfolio)
- ✅ Generate 3 test Excel files (50 invoices each)
- ✅ Give you step-by-step instructions

## 📋 Manual Setup (If Needed)

### Step 1: Load Sample Data

```bash
# Basic (4 units, 5 leases)
python scripts/load_sample_data.py

# Comprehensive (20+ units, 30+ leases)
python scripts/load_sample_data.py --comprehensive
```

### Step 2: Generate Test Excel Files

```bash
# Generate one file with 50 invoices
python scripts/generate_test_excel.py

# Generate multiple files
python scripts/generate_test_excel.py --output test_batch_01.xlsx --count 50
python scripts/generate_test_excel.py --output test_batch_02.xlsx --count 50
python scripts/generate_test_excel.py --output test_batch_03.xlsx --count 50
```

### Step 3: Start Web Server

```bash
python main.py
```

Then open: `http://localhost:8000`

## 🧪 Testing Checklist

### ✅ Upload Test
- [ ] Upload test Excel file
- [ ] See progress bar
- [ ] Check for errors/warnings
- [ ] Verify invoice count matches

### ✅ Validation Logic
- [ ] TEST-OCC-* invoices → **Invalid** (tenant liable)
- [ ] TEST-VAC-* invoices → **Valid** (landlord liable)
- [ ] TEST-LS-* invoices → **Landlord Supply - OK TO PAY**
- [ ] Daily rate determinations correct

### ✅ Duplicate Detection
- [ ] Upload same file twice
- [ ] See duplicate warnings
- [ ] Duplicates not saved

### ✅ Filtering & Export
- [ ] Filter by Status (Valid/Invalid/Needs Review)
- [ ] Filter by Determination
- [ ] Filter by Batch
- [ ] Export to CSV (respects filters)

### ✅ Dashboard
- [ ] View KPIs
- [ ] See recent invoices
- [ ] Navigation works

## 📊 Expected Results

**Test File with 50 invoices:**
- ~17 TEST-OCC-* → Invalid
- ~17 TEST-VAC-* → Valid
- ~5 TEST-LS-* → Landlord Supply
- ~11 TEST-RATE-* → Various determinations

## 🔍 Verify Validation Logic

1. **Vacant Periods** → Valid (landlord liable)
2. **Occupied Periods** → Invalid (tenant liable)
3. **Landlord Supply (units ending '00')** → OK TO PAY
4. **Daily Rate < £4** → OK TO PAY
5. **Daily Rate £4-£10** → OK TO PAY, SUBMIT METER READING
6. **Daily Rate >= £10** → DO NOT PAY, SUBMIT METER READING

## 📚 More Details

- **Full Testing Guide**: `TESTING_WORKFLOW_GUIDE.md`
- **System Status**: `PROJECT_STATUS_AND_NEXT_STEPS.md`
- **Quick Recap**: `QUICK_RECAP.md`

## 🆘 Troubleshooting

**No units found?**
```bash
python scripts/load_sample_data.py --comprehensive
```

**Check database?**
```bash
python scripts/inspect_database.py
```

**Clear and restart?**
```bash
# Delete app.db and restart
rm app.db
python -m app.db
python scripts/load_sample_data.py --comprehensive
```


