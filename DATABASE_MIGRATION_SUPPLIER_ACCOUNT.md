# Database Migration: Add supplier_account_number Field

## **Change Summary**

Added `supplier_account_number` field to the `invoices` table to store supplier account numbers separately from `unit_id`.

## **What Changed**

1. **Model** (`app/models.py`):
   - Added `supplier_account_number = Column(String, nullable=True)` to `Invoice` model

2. **Column Mapping** (`app/column_mapping.py`):
   - Added mapping for `supplier_account_number` with common column name variations

3. **PDF Normalizer** (`app/pdf_normalizer.py`):
   - Extracts account number separately (not as unit_id)
   - Stores in `supplier_account_number` field

4. **Schemas** (`app/schemas.py`):
   - Added `supplier_account_number: Optional[str]` to `InvoiceResponse`

5. **Processing** (`main.py`):
   - Excel/CSV processing includes `supplier_account_number`
   - PDF processing includes `supplier_account_number`

## **Database Migration**

### **For PostgreSQL (Supabase):**

Run this SQL to add the column:

```sql
ALTER TABLE invoices 
ADD COLUMN supplier_account_number VARCHAR;

-- Add index if needed (optional)
CREATE INDEX idx_invoices_supplier_account_number ON invoices(supplier_account_number);
```

### **For SQLite (Development):**

SQLite doesn't support `ALTER TABLE ADD COLUMN` easily. Options:

1. **Recreate table** (if no important data):
   ```python
   # Drop and recreate (WARNING: loses data)
   from app.db import Base, engine
   Base.metadata.drop_all(bind=engine, tables=[Invoice.__table__])
   Base.metadata.create_all(bind=engine, tables=[Invoice.__table__])
   ```

2. **Manual migration** (preserves data):
   ```sql
   -- Create new table with new column
   CREATE TABLE invoices_new (
       -- ... all columns including supplier_account_number
   );
   
   -- Copy data
   INSERT INTO invoices_new SELECT *, NULL as supplier_account_number FROM invoices;
   
   -- Drop old, rename new
   DROP TABLE invoices;
   ALTER TABLE invoices_new RENAME TO invoices;
   ```

3. **Use Alembic** (recommended for production):
   ```bash
   alembic revision --autogenerate -m "add_supplier_account_number"
   alembic upgrade head
   ```

## **Testing**

After migration:

1. **Test Excel/CSV upload** with `supplier_account_number` column
2. **Test PDF upload** - should extract account number
3. **Verify** account number appears in invoice details

## **Notes**

- Field is **nullable** (optional) - existing invoices will have `NULL`
- Account number is **separate** from `unit_id` (property/unit reference)
- Column mapping supports common variations: "account_number", "account number", "account", etc.

