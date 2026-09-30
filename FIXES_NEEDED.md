# 🔧 Fixes Needed Based on PDF Testing

## 📊 **Test Results**

### ✅ **Working:**
1. **E.ON Invoice** - Perfect extraction
2. **Opus Invoice** - Working (minor formatting issues)

### ❌ **Issues Found:**
1. **British Gas** - Normalization failing
2. **Opus** - Newline characters in extracted values

---

## 🛠️ **Fix 1: Text Cleaning (Opus Invoice)**

**Problem**: Newlines in extracted values
- Account number: "495174\n2" → should be "4951742"
- Supplier name: "OPUS\nenergy" → should be "OPUS energy"

**Solution**: Add text cleaning function to:
- Strip newlines
- Normalize whitespace
- Clean currency symbols

**Location**: `app/pdf_normalizer.py`

---

## 🛠️ **Fix 2: British Gas Normalization**

**Problem**: Normalization returns empty list

**Investigation Needed**:
1. Check if account number is being extracted
2. Check if validation is failing
3. Check supplier-specific extraction patterns

**Action**: Run debug script to see what Azure extracted

---

## 📋 **Next Steps**

1. **Run debug script** on British Gas PDF
2. **Fix text cleaning** for Opus
3. **Fix British Gas** normalization
4. **Re-test all PDFs**
5. **Test in UI**

---

**Let's start by investigating British Gas issue!**

