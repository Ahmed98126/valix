# 📄 PDF Invoice Integration Plan - Valix

## 🎯 **Executive Summary**

**Recommendation: Azure Document Intelligence (Invoice Model)** ✅

**Why:**
- ✅ You're already on Azure (seamless integration)
- ✅ Built-in invoice model (no training needed to start)
- ✅ Excellent table & line-item extraction
- ✅ Multi-page invoice support
- ✅ API-first, clean JSON output
- ✅ Strong performance on UK energy invoices (British Gas, E.ON, Octopus)

**Timeline:** 3-5 days for V1 implementation

---

## 🏗️ **Architecture Design**

### **Current Flow (Excel/CSV):**
```
User Uploads Excel/CSV
    ↓
Column Mapping (per-tenant)
    ↓
Pandas DataFrame
    ↓
Normalize to Invoice Schema
    ↓
Validation Engine
    ↓
Results
```

### **New Flow (PDF):**
```
User Uploads PDF Invoice
    ↓
Azure Document Intelligence (Invoice Model)
    ↓
Structured JSON (tables + fields)
    ↓
PDF Normalization Layer (NEW)
    ↓
Standard Invoice Schema (same as Excel/CSV)
    ↓
Validation Engine (existing - no changes!)
    ↓
Results
```

**Key Insight:** PDF extraction feeds into the SAME validation engine. No changes needed to validation logic!

---

## 📋 **Implementation Plan**

### **Phase 1: Core PDF Processing (2-3 days)**

#### **Step 1: Set Up Azure Document Intelligence**

1. **Create Azure Document Intelligence Resource**
   - Go to Azure Portal
   - Create "Form Recognizer" or "Document Intelligence" resource
   - Get API endpoint and key
   - Add to environment variables

2. **Install SDK**
   ```bash
   pip install azure-ai-formrecognizer
   ```

3. **Add to `requirements.txt`**
   ```
   azure-ai-formrecognizer>=3.3.0
   ```

#### **Step 2: Create PDF Processing Module**

**New File: `app/pdf_processor.py`**

```python
"""PDF invoice processing using Azure Document Intelligence."""

from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
import os
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class PDFInvoiceProcessor:
    """Process PDF invoices using Azure Document Intelligence."""
    
    def __init__(self):
        endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
        key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")
        
        if not endpoint or not key:
            raise ValueError("Azure Document Intelligence credentials not configured")
        
        self.client = DocumentAnalysisClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(key)
        )
    
    def extract_invoice_data(self, pdf_path: str) -> Dict:
        """
        Extract structured data from PDF invoice.
        
        Returns:
            {
                "invoice_number": str,
                "supplier_name": str,
                "invoice_date": datetime,
                "due_date": datetime,
                "billing_period_start": date,
                "billing_period_end": date,
                "gross_amount": float,
                "net_amount": float,
                "vat_amount": float,
                "currency": str,
                "line_items": List[Dict],
                "unit_id": str,  # Extracted from address or line items
                "utility_type": str,  # Detected from invoice content
                "confidence_scores": Dict,
                "raw_data": Dict  # Full Azure response for debugging
            }
        """
        with open(pdf_path, "rb") as f:
            poller = self.client.begin_analyze_document(
                model_id="prebuilt-invoice",  # Azure's prebuilt invoice model
                document=f
            )
            result = poller.result()
        
        # Normalize Azure response to our schema
        return self._normalize_azure_response(result)
    
    def _normalize_azure_response(self, azure_result) -> Dict:
        """Convert Azure Document Intelligence response to Valix invoice schema."""
        
        # Azure returns fields in a structured format
        fields = azure_result.documents[0].fields if azure_result.documents else {}
        
        # Extract basic fields
        invoice_data = {
            "invoice_number": self._extract_field(fields, "InvoiceId", "InvoiceNumber"),
            "supplier_name": self._extract_field(fields, "VendorName", "SupplierName"),
            "invoice_date": self._parse_date(fields.get("InvoiceDate")),
            "due_date": self._parse_date(fields.get("DueDate")),
            "gross_amount": self._extract_amount(fields.get("TotalTax")),
            "net_amount": self._extract_amount(fields.get("SubTotal")),
            "vat_amount": self._extract_amount(fields.get("TotalTax")),
            "currency": self._extract_currency(fields),
            "line_items": self._extract_line_items(azure_result),
            "billing_period_start": self._extract_billing_period_start(fields),
            "billing_period_end": self._extract_billing_period_end(fields),
            "unit_id": self._extract_unit_id(fields, azure_result),
            "utility_type": self._detect_utility_type(fields, azure_result),
            "confidence_scores": self._get_confidence_scores(fields),
            "raw_data": {}  # Store full response for debugging
        }
        
        return invoice_data
    
    def _extract_field(self, fields: Dict, *possible_keys: str) -> Optional[str]:
        """Extract field value trying multiple possible keys."""
        for key in possible_keys:
            if key in fields and fields[key]:
                value = fields[key]
                if hasattr(value, 'value'):
                    return str(value.value)
                return str(value)
        return None
    
    def _parse_date(self, date_field) -> Optional[datetime]:
        """Parse date from Azure field."""
        if not date_field:
            return None
        if hasattr(date_field, 'value'):
            return date_field.value
        if isinstance(date_field, datetime):
            return date_field
        if isinstance(date_field, str):
            # Try parsing common date formats
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d']:
                try:
                    return datetime.strptime(date_field, fmt)
                except:
                    continue
        return None
    
    def _extract_amount(self, amount_field) -> Optional[float]:
        """Extract numeric amount from Azure field."""
        if not amount_field:
            return None
        if hasattr(amount_field, 'value'):
            return float(amount_field.value)
        if isinstance(amount_field, (int, float)):
            return float(amount_field)
        if isinstance(amount_field, str):
            # Remove currency symbols and parse
            cleaned = amount_field.replace('£', '').replace(',', '').strip()
            try:
                return float(cleaned)
            except:
                return None
        return None
    
    def _extract_currency(self, fields: Dict) -> str:
        """Extract currency, default to GBP for UK invoices."""
        currency = self._extract_field(fields, "CurrencyCode", "Currency")
        return currency.upper() if currency else "GBP"
    
    def _extract_line_items(self, azure_result) -> List[Dict]:
        """Extract line items from invoice tables."""
        line_items = []
        
        # Azure extracts tables from invoices
        if hasattr(azure_result, 'tables'):
            for table in azure_result.tables:
                # Look for line item table (usually has description, quantity, amount)
                # This is supplier-specific, so we'll need to adapt per supplier
                for row in table.rows:
                    cells = [cell.content for cell in row.cells]
                    if len(cells) >= 3:  # At least description, quantity, amount
                        line_items.append({
                            "description": cells[0] if len(cells) > 0 else "",
                            "quantity": cells[1] if len(cells) > 1 else "",
                            "unit_price": cells[2] if len(cells) > 2 else "",
                            "total": cells[-1] if len(cells) > 2 else ""
                        })
        
        return line_items
    
    def _extract_billing_period_start(self, fields: Dict) -> Optional[datetime]:
        """Extract billing period start from invoice."""
        # Try multiple field names
        period_start = self._extract_field(
            fields, 
            "BillingPeriodStart", 
            "PeriodStart", 
            "ServiceStartDate",
            "FromDate"
        )
        return self._parse_date(period_start)
    
    def _extract_billing_period_end(self, fields: Dict) -> Optional[datetime]:
        """Extract billing period end from invoice."""
        period_end = self._extract_field(
            fields,
            "BillingPeriodEnd",
            "PeriodEnd",
            "ServiceEndDate",
            "ToDate"
        )
        return self._parse_date(period_end)
    
    def _extract_unit_id(self, fields: Dict, azure_result) -> Optional[str]:
        """
        Extract unit/property ID from invoice.
        
        This is tricky - unit IDs might be in:
        - Customer address
        - Invoice reference
        - Line items
        - Custom fields
        
        We'll need supplier-specific logic here.
        """
        # Try customer address first (often contains property reference)
        customer_address = self._extract_field(fields, "CustomerAddress", "BillingAddress")
        
        # Try to extract unit ID from address
        # UK energy invoices often have property references in address
        if customer_address:
            # Look for patterns like "Unit 1", "Shop 5", "OFFICE-101", etc.
            import re
            patterns = [
                r'(?:Unit|Shop|Office|Suite)\s*([A-Z0-9-]+)',
                r'([A-Z]{2,}-\d{3,})',  # Pattern like SHOP-001
                r'(\d{1,3}[A-Z]\d{1,3})'  # Pattern like 1A2
            ]
            for pattern in patterns:
                match = re.search(pattern, customer_address, re.IGNORECASE)
                if match:
                    return match.group(1).upper()
        
        # Fallback: try invoice reference
        invoice_ref = self._extract_field(fields, "InvoiceReference", "Reference")
        if invoice_ref:
            return invoice_ref
        
        return None
    
    def _detect_utility_type(self, fields: Dict, azure_result) -> str:
        """
        Detect utility type from invoice content.
        
        UK energy suppliers:
        - British Gas: Usually says "Gas" or "Electricity"
        - E.ON: Similar
        - Octopus Energy: Similar
        
        We'll look for keywords in supplier name and invoice content.
        """
        supplier = self._extract_field(fields, "VendorName", "SupplierName", "").lower()
        description = self._extract_field(fields, "Description", "").lower()
        
        # Check for utility keywords
        if "electricity" in supplier or "electricity" in description:
            return "Electricity"
        elif "gas" in supplier or "gas" in description:
            return "Gas"
        elif "water" in supplier or "water" in description:
            return "Water"
        else:
            # Default based on supplier name
            if "british gas" in supplier:
                return "Gas"  # Default for British Gas
            elif "eon" in supplier or "e.on" in supplier:
                return "Electricity"  # Default for E.ON
            else:
                return "Unknown"
    
    def _get_confidence_scores(self, fields: Dict) -> Dict:
        """Extract confidence scores for quality assessment."""
        scores = {}
        for key, field in fields.items():
            if hasattr(field, 'confidence'):
                scores[key] = field.confidence
        return scores
```

#### **Step 3: Create Normalization Layer**

**New File: `app/pdf_normalizer.py`**

```python
"""Normalize PDF-extracted data to Valix invoice schema."""

from typing import Dict, List
from datetime import datetime, date
from app.pdf_processor import PDFInvoiceProcessor

class PDFInvoiceNormalizer:
    """Normalize PDF invoice data to standard Valix schema."""
    
    def __init__(self):
        self.processor = PDFInvoiceProcessor()
    
    def normalize_pdf_invoice(self, pdf_path: str, tenant_id: int) -> List[Dict]:
        """
        Extract and normalize PDF invoice to Valix invoice format.
        
        Returns:
            List of invoice dictionaries matching Excel/CSV format
        """
        # Extract data from PDF
        extracted_data = self.processor.extract_invoice_data(pdf_path)
        
        # Normalize to Valix schema
        normalized_invoices = []
        
        # Single invoice from PDF (unlike Excel which can have multiple rows)
        invoice = {
            "invoice_number": extracted_data.get("invoice_number", "UNKNOWN"),
            "supplier_name": extracted_data.get("supplier_name", "Unknown Supplier"),
            "unit_id": extracted_data.get("unit_id", "UNKNOWN"),
            "billing_period_start": self._to_date(extracted_data.get("billing_period_start")),
            "billing_period_end": self._to_date(extracted_data.get("billing_period_end")),
            "invoice_date": self._to_date(extracted_data.get("invoice_date")),
            "gross_amount": extracted_data.get("gross_amount", 0.0),
            "net_amount": extracted_data.get("net_amount"),
            "vat_amount": extracted_data.get("vat_amount"),
            "utility_type": extracted_data.get("utility_type", "Unknown"),
            "currency": extracted_data.get("currency", "GBP"),
            "source_type": "pdf",  # Mark as PDF source
            "extraction_confidence": self._calculate_overall_confidence(
                extracted_data.get("confidence_scores", {})
            ),
            "raw_extraction": extracted_data  # Store for debugging/review
        }
        
        normalized_invoices.append(invoice)
        
        return normalized_invoices
    
    def _to_date(self, dt: datetime) -> Optional[date]:
        """Convert datetime to date."""
        if dt is None:
            return None
        if isinstance(dt, date):
            return dt
        if isinstance(dt, datetime):
            return dt.date()
        return None
    
    def _calculate_overall_confidence(self, scores: Dict) -> float:
        """Calculate overall confidence score."""
        if not scores:
            return 0.0
        values = [v for v in scores.values() if isinstance(v, (int, float))]
        return sum(values) / len(values) if values else 0.0
```

#### **Step 4: Integrate with Existing Upload Flow**

**Modify: `main.py` - `upload_file` endpoint**

```python
@app.post("/api/upload")
async def upload_file(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Handle file upload (Excel/CSV/PDF) and trigger validation."""
    
    # Check file type
    file_ext = file.filename.lower().split('.')[-1]
    
    if file_ext in ('xlsx', 'xls', 'csv'):
        # Existing Excel/CSV flow
        # ... (existing code)
        
    elif file_ext == 'pdf':
        # NEW: PDF processing flow
        batch_id = f"BATCH_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        file_path = UPLOAD_DIR / f"{batch_id}_{file.filename}"
        
        content = await file.read()
        if len(content) > MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=400, 
                detail=f"File too large. Maximum size is {MAX_UPLOAD_SIZE / 1024 / 1024:.0f}MB"
            )
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Process PDF in background
        background_tasks.add_task(
            process_pdf_invoice, 
            str(file_path), 
            batch_id, 
            user.id
        )
        
        return JSONResponse({
            "status": "success",
            "message": "PDF invoice uploaded. Processing with AI extraction...",
            "batch_id": batch_id,
            "file_type": "pdf"
        })
    
    else:
        raise HTTPException(
            status_code=400, 
            detail="Unsupported file type. Please upload Excel (.xlsx, .xls), CSV, or PDF files."
        )
```

**New Function: `process_pdf_invoice`**

```python
def process_pdf_invoice(file_path: str, batch_id: str, user_id: int):
    """Process PDF invoice using Azure Document Intelligence."""
    from app.db import SessionLocal
    from app.pdf_normalizer import PDFInvoiceNormalizer
    from app.models import Invoice, User
    from app.validation import validate_invoice
    
    session = SessionLocal()
    
    try:
        # Get user and tenant
        user = session.query(User).filter(User.id == user_id).first()
        tenant_id = user.tenant_id
        
        # Normalize PDF to invoice schema
        normalizer = PDFInvoiceNormalizer()
        normalized_invoices = normalizer.normalize_pdf_invoice(file_path, tenant_id)
        
        # Create Invoice records (same as Excel/CSV flow)
        for invoice_data in normalized_invoices:
            invoice = Invoice(
                tenant_id=tenant_id,
                invoice_number=invoice_data["invoice_number"],
                supplier_name=invoice_data["supplier_name"],
                unit_id=invoice_data["unit_id"],
                billing_period_start=invoice_data["billing_period_start"],
                billing_period_end=invoice_data["billing_period_end"],
                invoice_date=invoice_data["invoice_date"],
                gross_amount=invoice_data["gross_amount"],
                net_amount=invoice_data.get("net_amount"),
                vat_amount=invoice_data.get("vat_amount"),
                utility_type=invoice_data["utility_type"],
                currency=invoice_data.get("currency", "GBP"),
                source_batch=batch_id
            )
            session.add(invoice)
            session.flush()  # Get invoice.id
            
            # Validate invoice (existing validation engine!)
            validate_invoice(invoice, session, tenant_id)
        
        session.commit()
        logger.info(f"✅ Processed PDF invoice: {batch_id}")
        
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Error processing PDF: {e}", exc_info=True)
    finally:
        session.close()
```

#### **Step 5: Update Upload UI**

**Modify: `templates/upload.html`**

```html
<!-- Update file input to accept PDF -->
<input 
    id="file-upload" 
    name="file" 
    type="file" 
    class="sr-only" 
    accept=".xlsx,.xls,.csv,.pdf"  <!-- Added .pdf -->
    required
>

<!-- Update help text -->
<p class="text-sm text-gray-600">
    Excel (.xlsx, .xls), CSV, or PDF files up to 50MB
</p>

<!-- Add PDF-specific messaging -->
<div id="pdf-info" class="hidden mt-2 p-3 bg-blue-50 rounded-lg">
    <p class="text-sm text-blue-800">
        📄 PDF invoices will be automatically extracted using AI. 
        Please ensure the PDF is clear and readable.
    </p>
</div>
```

---

### **Phase 2: Supplier-Specific Enhancements (1-2 days)**

#### **Supplier-Specific Normalizers**

**New File: `app/supplier_normalizers.py`**

```python
"""Supplier-specific normalization rules for UK energy invoices."""

class BritishGasNormalizer:
    """Normalization rules specific to British Gas invoices."""
    
    @staticmethod
    def extract_unit_id(fields: Dict, address: str) -> Optional[str]:
        """British Gas often puts property reference in customer address."""
        # British Gas specific patterns
        patterns = [
            r'Property\s*Ref[:\s]+([A-Z0-9-]+)',
            r'MPAN[:\s]+([0-9]+)',  # Meter Point Administration Number
        ]
        # ... implementation
    
    @staticmethod
    def extract_billing_period(fields: Dict) -> Tuple[date, date]:
        """British Gas billing period extraction."""
        # British Gas specific logic
        pass

class EONNormalizer:
    """Normalization rules specific to E.ON invoices."""
    # Similar structure
    pass

class OctopusNormalizer:
    """Normalization rules specific to Octopus Energy invoices."""
    # Similar structure
    pass
```

---

### **Phase 3: Manual Correction UI (Future)**

**For invoices with low confidence or extraction errors:**

1. **Review Page** - Show extracted data with confidence scores
2. **Edit Fields** - Allow manual correction before validation
3. **Learn from Corrections** - Store corrections to improve future extractions

---

## 🔧 **Configuration**

### **Environment Variables**

Add to `.env`:
```env
# Azure Document Intelligence
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_DOCUMENT_INTELLIGENCE_KEY=your-api-key-here
```

### **Azure Setup Steps**

1. **Create Document Intelligence Resource:**
   - Azure Portal → Create Resource → "Form Recognizer" or "Document Intelligence"
   - Choose pricing tier (F0 for testing, S0 for production)
   - Get endpoint and key

2. **Test Connection:**
   ```python
   from app.pdf_processor import PDFInvoiceProcessor
   processor = PDFInvoiceProcessor()
   # Should not raise error
   ```

---

## 📊 **Cost Estimation**

### **Azure Document Intelligence Pricing (as of 2024):**

- **F0 (Free):** 500 pages/month
- **S0 (Standard):** $1.50 per 1,000 pages

**For 3,000 invoices/month:**
- Cost: ~$4.50/month (very affordable!)

**Recommendation:** Start with F0 for testing, upgrade to S0 for production.

---

## 🎯 **Success Metrics**

### **V1 Goals:**
- ✅ Extract 80%+ of invoice fields correctly
- ✅ Handle multi-page invoices
- ✅ Process British Gas, E.ON, Octopus invoices
- ✅ Integrate seamlessly with existing validation

### **V2 Goals:**
- ✅ 95%+ accuracy with supplier-specific rules
- ✅ Manual correction UI
- ✅ Confidence-based routing (auto vs. manual review)

---

## 🚀 **Implementation Timeline**

### **Week 1: Core Integration**
- **Day 1-2:** Set up Azure Document Intelligence, create PDF processor
- **Day 3:** Create normalization layer
- **Day 4:** Integrate with upload flow
- **Day 5:** Test with sample invoices

### **Week 2: Polish & Supplier Rules**
- **Day 1-2:** Add supplier-specific normalizers
- **Day 3:** Improve unit_id extraction
- **Day 4:** Add confidence scoring
- **Day 5:** Testing and bug fixes

---

## 💡 **Key Design Decisions**

1. **Same Validation Engine:** PDF extraction feeds into existing validation - no changes needed!

2. **Normalization Layer:** Critical component that converts Azure output to Valix schema

3. **Supplier-Specific Rules:** Start generic, add supplier rules as you learn patterns

4. **Confidence Scores:** Track extraction quality for manual review queue

5. **Fallback Strategy:** If PDF extraction fails, allow manual entry

---

## 🔄 **Future Enhancements**

1. **Batch PDF Processing:** Upload multiple PDFs at once
2. **Email Integration:** Auto-process invoices from email attachments
3. **Custom Training:** Train Azure model on your specific invoice formats (advanced)
4. **OCR Fallback:** If Azure fails, try generic OCR as backup

---

## ✅ **Next Steps**

1. **This Week:**
   - Set up Azure Document Intelligence resource
   - Install SDK and test with one British Gas invoice
   - Create basic PDF processor

2. **Next Week:**
   - Build normalization layer
   - Integrate with upload flow
   - Test with E.ON and Octopus invoices

3. **Week 3:**
   - Add supplier-specific rules
   - Polish and optimize
   - Deploy to production

---

**Ready to start? Let me know and I'll help you implement the PDF processor module!** 🚀

