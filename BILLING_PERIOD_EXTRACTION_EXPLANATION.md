# Billing Period Extraction - Generic Implementation

## ✅ **It's Generic, NOT Hard-Coded!**

The billing period extraction uses **regex patterns** that work with **any dates**, not just the specific dates from your test invoice.

---

## 🔍 **How It Works**

### **Pattern 1: British Gas Format**
```regex
bill\s+period[\s:]+(\d{1,2}\s+[A-Za-z]{3}\s+\d{2})\s*[-–]\s*(\d{1,2}\s+[A-Za-z]{3}\s+\d{2})
```

**What this matches:**
- `bill\s+period` - Looks for "bill period" (with spaces)
- `[\s:]+` - Followed by spaces or colon
- `(\d{1,2}\s+[A-Za-z]{3}\s+\d{2})` - **Captures ANY date** in format "DD MMM YY"
  - `\d{1,2}` = 1-2 digits (day: 1-31)
  - `\s+` = space
  - `[A-Za-z]{3}` = 3 letters (month: Jan, Feb, Mar, etc.)
  - `\s+` = space
  - `\d{2}` = 2 digits (year: 09, 10, 24, etc.)
- `\s*[-–]\s*` - Dash separator (regular or em dash)
- `(\d{1,2}\s+[A-Za-z]{3}\s+\d{2})` - **Captures second date** in same format

---

## 📋 **Examples of What It Will Match**

✅ **"Bill period: 25 Nov 09 - 03 Mar 10"** (your test invoice)  
✅ **"Bill period: 01 Jan 24 - 31 Jan 24"** (any January 2024 invoice)  
✅ **"Bill period: 15 Dec 23 - 14 Jan 24"** (any December-January period)  
✅ **"Bill period: 01 Apr 25 - 30 Apr 25"** (any future dates)  
✅ **"Billing period: 10 Feb 20 - 09 Mar 20"** (alternative wording)

**Any date in the format "DD MMM YY" separated by a dash will work!**

---

## 🎯 **Multiple Patterns for Flexibility**

The code tries **multiple patterns** to catch different variations:

1. **"Bill period: DD MMM YY - DD MMM YY"** (British Gas standard)
2. **"Billing period: DD MMM YY - DD MMM YY"** (alternative wording)
3. **"DD MMM YY - DD MMM YY"** (generic, without "Bill period" prefix)
4. **"DD MMM YY to DD MMM YY"** (E.ON format with "to")

---

## ✅ **Date Parsing**

The dates are then parsed using `_parse_date()` which handles:
- ✅ "25 Nov 09" → 2009-11-25
- ✅ "03 Mar 10" → 2010-03-03
- ✅ "01 Jan 24" → 2024-01-01
- ✅ Any date in "DD MMM YY" format

The year conversion logic:
- Years 00-49 → 2000-2049
- Years 50-99 → 1950-1999

---

## 🧪 **Test It Yourself**

You can test with any British Gas invoice that has:
- "Bill period: [date] - [date]" format
- Dates in "DD MMM YY" format (e.g., "25 Nov 09", "01 Jan 24")

**It will work for any dates, not just your test invoice!**

---

## 📊 **Summary**

✅ **Generic regex patterns** - work with any dates  
✅ **Multiple pattern variations** - catches different wording  
✅ **Flexible date parsing** - handles various date formats  
✅ **No hard-coded dates** - completely dynamic  

**Your British Gas invoices will extract correctly regardless of the dates!** 🎉

