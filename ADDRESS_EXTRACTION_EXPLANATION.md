# Address Extraction Strategy for Invoice-to-Unit Matching

## The Confusion: Customer Address vs Supply Address

You're right to be confused! Different suppliers use different terminology, and sometimes the addresses are the same, sometimes different.

## Two Types of Addresses on Invoices

### 1. **Customer/Billing Address** (Where the bill is sent)
- The address where the invoice is mailed
- Could be company headquarters, accounting office, or property management office
- **Example (British Gas)**: "2 SAMPLE STREET, SAMPLETOWN, SAMPLESHIRE, AB12 3CD"

### 2. **Supply/Service Address** (Where the utility is consumed)
- The physical location where the utility meter is located
- This is what we need to match to units!
- **Example (British Gas)**: "86 EDLESTONE ROAD, CREWE, CW8 1AB"

## When Are They Different?

- **Different**: When bill is sent to company HQ but utility is consumed at a property location
  - Example: Company HQ in London, but property in Crewe
- **Same**: When bill is sent to the same location where utility is consumed
  - Example: Small business owner receives bill at their shop address

## How Our System Handles This

### Priority Order (What We Extract First)

1. **Supply/Service Address from Content** (Highest Priority)
   - British Gas: "Supply address: 86 EDLESTONE ROAD..."
   - E.ON: "For electricity supplied to Street, City..."
   - Opus: "For: Car Park Deer Park Road..."

2. **ServiceAddress from Azure Fields**
   - Azure Document Intelligence's extracted service address

3. **CustomerAddress from Azure Fields** (Fallback)
   - Only used if supply/service address not found
   - Sometimes they're the same, so this works too

### Why This Approach?

For **commercial real estate**, we need the **supply/service address** because:
- ✅ That's where the utility meter is physically located
- ✅ That's where the unit/property is located
- ✅ That's what matches to your `Units` table

The customer address might be your company's HQ, which doesn't help match to units.

## Examples from Your Invoices

### British Gas Invoice
- **Customer Address**: "2 SAMPLE STREET, SAMPLETOWN..." (where bill is sent)
- **Supply Address**: "86 EDLESTONE ROAD, CREWE, CW8 1AB" (where electricity is consumed)
- **We Extract**: Supply address ✅ (matches to SHOP-003)

### E.ON Invoice
- **Customer Address**: "Business name, Street, City..." (where bill is sent)
- **Service Address**: "For electricity supplied to Street, City..." (where electricity is consumed)
- **We Extract**: Service address ✅

### Opus Energy Invoice
- **Service Address**: "For: Car Park Deer Park Road..." (where electricity is consumed)
- **We Extract**: Service address ✅

## What If They're the Same?

If the customer address and supply address are the same (common for small businesses), it doesn't matter which one we extract - they'll both match to the same unit! ✅

## Summary

- **We prioritize supply/service address** (where utility is consumed)
- **We fall back to customer address** if supply address not found
- **Both work** if they're the same location
- **For commercial real estate**, supply address is usually what we need

The system is now smart enough to:
1. Look for supply/service address patterns first
2. Fall back to customer address if needed
3. Try both and use whichever matches better to your units

