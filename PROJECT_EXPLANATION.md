# Commercial Property Invoice Validator - Simple Explanation

## 🎯 The Business Problem

**Landlords receive utility bills (electricity, gas, water) for their commercial properties.**

**Question:** Should I pay this invoice, or is something wrong with it?

---

## 📊 The Three Main Data Types (Models)

### 1. **Unit** = A Physical Property Space
**Real-world example:**
- "Shop 1A at 123 High Street, London"
- "Office Suite 5B at Business Park"

**What it stores:**
- Unit ID (like "SHOP-1A")
- Building name
- Full address

**Think of it as:** A contact card for each property space you own.

---

### 2. **Lease** = When a Tenant Rented a Unit
**Real-world example:**
- "Coffee Shop Ltd rented Shop 1A from January 1, 2023 to December 31, 2023"
- "Tech Corp rented Office 5B from March 1, 2022 to present (ongoing)"

**What it stores:**
- Which unit was rented
- Tenant name
- Start date
- End date (or null if still ongoing)

**Think of it as:** A rental agreement that tells you when a unit was occupied.

---

### 3. **Invoice** = A Bill You Received
**Real-world example:**
- "Electricity bill #12345 from British Gas"
- "For Shop 1A"
- "£500 for the period January 1-31, 2023"

**What it stores:**
- Invoice number
- Supplier name (e.g., "British Gas")
- Which unit it's for
- Billing period (start and end dates)
- Amount (£500)
- Type of utility (Electricity, Gas, Water)

**Think of it as:** The actual bill that needs to be checked.

---

## 🔍 What We're Building

### **Phase 1 (COMPLETED ✅)**
We built the foundation:
- ✅ Database to store Units, Leases, and Invoices
- ✅ Way to load invoices from CSV files
- ✅ Basic structure

**Right now:** We can store data, but we can't validate it yet.

---

### **Phase 2 (NEXT - What We Need to Build)**
We need to build the "validation engine" - the brain that checks invoices.

**The validation engine will:**
1. Look at each invoice
2. Check it against the property data (units + leases)
3. Flag problems like:
   - ❌ Invoice for a period when the unit was VACANT (no tenant)
   - ❌ Invoice for a period with NO LEASE (shouldn't be paying)
   - ❌ DUPLICATE invoice (same invoice number already paid)
   - ❌ SUSPICIOUS amount (unusually high compared to normal)

4. Give each invoice a determination:
   - ✅ **OK TO PAY** - Everything looks good
   - ❌ **DO NOT PAY** - Something is wrong
   - ⚠️ **LANDLORD SUPPLY - OK TO PAY** - Unit was vacant, but landlord pays utilities

---

## 🎬 Real-World Example Flow

### Scenario:
You own a shopping center with 10 shops.

1. **You have Units:**
   - Shop 1A, Shop 1B, Shop 2A, etc.

2. **You have Leases:**
   - Shop 1A: Coffee Shop rented Jan 1, 2023 - Dec 31, 2023
   - Shop 1A: New tenant (Bakery) rented Jan 1, 2024 - present
   - Shop 1B: Vacant since Dec 31, 2023 (no lease)

3. **You receive an Invoice:**
   - Invoice #999 from British Gas
   - For Shop 1A
   - £600 for period: March 1-31, 2023
   - Type: Electricity

4. **The Validation Engine Checks:**
   - ✅ Is there a lease for Shop 1A covering March 2023? YES (Coffee Shop)
   - ✅ Is the amount reasonable? YES (similar to previous months)
   - ✅ Is this a duplicate? NO (first time seeing invoice #999)
   - **Result: OK TO PAY** ✅

---

### Another Scenario (Problem Invoice):

**Invoice:**
- Invoice #888 from Thames Water
- For Shop 1B
- £300 for period: February 1-28, 2024
- Type: Water

**The Validation Engine Checks:**
- ❌ Is there a lease for Shop 1B covering February 2024? NO (Shop 1B has been vacant since Dec 31, 2023)
- **Result: DO NOT PAY** ❌ (or maybe "LANDLORD SUPPLY - OK TO PAY" if landlord pays for vacant units)

---

## 🚀 Current Status

**What we have:**
- ✅ Database tables (Units, Leases, Invoices)
- ✅ CSV loader (can import invoices from files)
- ✅ Basic structure

**What we're missing:**
- ❌ Validation engine (the brain that checks invoices)
- ❌ Unit timeline (a table that shows when each unit was occupied/vacant)
- ❌ Validation results table (where we store the "OK TO PAY" or "DO NOT PAY" decisions)

**Next step:** Build Phase 2 - the validation engine!

