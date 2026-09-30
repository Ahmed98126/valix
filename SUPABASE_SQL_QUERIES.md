# Useful Supabase SQL Queries

## 🎯 Quick Reference for Exploring Your Data

### **1. View All Units**
```sql
SELECT * FROM units
ORDER BY tenant_id, unit_id;
```

### **2. View All Leases**
```sql
SELECT 
    l.id,
    l.tenant_id,
    l.unit_id,
    l.tenant_name,
    l.lease_start,
    l.lease_end,
    CASE 
        WHEN l.lease_end IS NULL THEN 'Ongoing'
        ELSE 'Ended'
    END as lease_status
FROM leases l
ORDER BY l.tenant_id, l.unit_id, l.lease_start;
```

### **3. View All Invoices**
```sql
SELECT 
    i.id,
    i.invoice_number,
    i.supplier_name,
    i.unit_id,
    i.billing_period_start,
    i.billing_period_end,
    i.gross_amount,
    i.utility_type,
    i.created_at
FROM invoices i
ORDER BY i.tenant_id, i.created_at DESC;
```

### **4. View Invoices with Validation Results**
```sql
SELECT 
    i.invoice_number,
    i.supplier_name,
    i.unit_id,
    i.billing_period_start,
    i.billing_period_end,
    i.gross_amount,
    v.validation_status,
    v.determination,
    v.total_vacancy_overlap_days,
    v.invoice_days,
    v.daily_rate,
    v.is_duplicate
FROM invoices i
LEFT JOIN invoice_validation v ON i.id = v.invoice_id
ORDER BY i.tenant_id, i.created_at DESC;
```

### **5. View Unit Timeline (Occupancy/Vacancy)**
```sql
SELECT 
    t.unit_id,
    t.status,
    t.period_start,
    t.period_end,
    t.days_in_period,
    CASE 
        WHEN t.period_end IS NULL THEN 'Ongoing'
        ELSE 'Ended'
    END as period_status
FROM unit_timeline t
ORDER BY t.tenant_id, t.unit_id, t.period_start;
```

### **6. Count Invoices by Status**
```sql
SELECT 
    v.validation_status,
    COUNT(*) as count,
    SUM(i.gross_amount) as total_amount
FROM invoice_validation v
JOIN invoices i ON v.invoice_id = i.id
GROUP BY v.validation_status
ORDER BY count DESC;
```

### **7. Count Invoices by Determination**
```sql
SELECT 
    v.determination,
    COUNT(*) as count,
    AVG(v.daily_rate) as avg_daily_rate
FROM invoice_validation v
GROUP BY v.determination
ORDER BY count DESC;
```

### **8. View Invoices by Tenant**
```sql
SELECT 
    t.name as tenant_name,
    COUNT(i.id) as invoice_count,
    SUM(i.gross_amount) as total_amount,
    COUNT(CASE WHEN v.validation_status = 'Valid' THEN 1 END) as valid_count,
    COUNT(CASE WHEN v.validation_status = 'Invalid' THEN 1 END) as invalid_count
FROM tenants t
LEFT JOIN invoices i ON t.id = i.tenant_id
LEFT JOIN invoice_validation v ON i.id = v.invoice_id
GROUP BY t.id, t.name
ORDER BY invoice_count DESC;
```

### **9. Find Invoices Needing Review**
```sql
SELECT 
    i.invoice_number,
    i.unit_id,
    i.billing_period_start,
    i.billing_period_end,
    i.gross_amount,
    v.determination,
    v.total_vacancy_overlap_days,
    v.invoice_days
FROM invoices i
JOIN invoice_validation v ON i.id = v.invoice_id
WHERE v.validation_status = 'Needs Review'
   OR v.determination = 'COT'
ORDER BY i.created_at DESC;
```

### **10. Find High-Value Invoices**
```sql
SELECT 
    i.invoice_number,
    i.unit_id,
    i.gross_amount,
    v.daily_rate,
    v.determination
FROM invoices i
JOIN invoice_validation v ON i.id = v.invoice_id
WHERE v.daily_rate >= 10
ORDER BY v.daily_rate DESC;
```

### **11. View Duplicate Invoices**
```sql
SELECT 
    i.invoice_number,
    i.gross_amount,
    i.unit_id,
    i.billing_period_start,
    v.is_duplicate,
    v.duplicate_batch,
    COUNT(*) OVER (PARTITION BY i.invoice_number, i.gross_amount) as duplicate_count
FROM invoices i
JOIN invoice_validation v ON i.id = v.invoice_id
WHERE v.is_duplicate = 'Yes'
ORDER BY i.invoice_number, i.gross_amount;
```

### **12. Units with Most Invoices**
```sql
SELECT 
    i.unit_id,
    COUNT(*) as invoice_count,
    SUM(i.gross_amount) as total_amount,
    AVG(v.daily_rate) as avg_daily_rate
FROM invoices i
LEFT JOIN invoice_validation v ON i.id = v.invoice_id
GROUP BY i.unit_id
ORDER BY invoice_count DESC;
```

### **13. Recent Uploads**
```sql
SELECT 
    u.batch_id,
    u.file_name,
    u.status,
    u.invoices_created,
    u.total_rows,
    u.started_at,
    u.completed_at,
    EXTRACT(EPOCH FROM (u.completed_at - u.started_at)) as processing_seconds
FROM upload_status u
ORDER BY u.started_at DESC
LIMIT 10;
```

### **14. Validation Summary by Tenant**
```sql
SELECT 
    t.name as tenant_name,
    COUNT(DISTINCT i.id) as total_invoices,
    COUNT(DISTINCT CASE WHEN v.validation_status = 'Valid' THEN i.id END) as valid_invoices,
    COUNT(DISTINCT CASE WHEN v.validation_status = 'Invalid' THEN i.id END) as invalid_invoices,
    COUNT(DISTINCT CASE WHEN v.validation_status = 'Needs Review' THEN i.id END) as needs_review,
    SUM(i.gross_amount) as total_amount
FROM tenants t
LEFT JOIN invoices i ON t.id = i.tenant_id
LEFT JOIN invoice_validation v ON i.id = v.invoice_id
GROUP BY t.id, t.name
ORDER BY total_invoices DESC;
```

### **15. Units with Vacancy Periods**
```sql
SELECT 
    t.unit_id,
    COUNT(*) as vacancy_periods,
    SUM(t.days_in_period) as total_vacancy_days,
    MIN(t.period_start) as first_vacancy,
    MAX(COALESCE(t.period_end, CURRENT_DATE)) as last_vacancy
FROM unit_timeline t
WHERE t.status = 'vacant'
GROUP BY t.unit_id, t.tenant_id
ORDER BY total_vacancy_days DESC;
```

---

## 🔍 Advanced Queries

### **Find Invoices During Vacant Periods**
```sql
SELECT 
    i.invoice_number,
    i.unit_id,
    i.billing_period_start,
    i.billing_period_end,
    v.total_vacancy_overlap_days,
    v.invoice_days,
    CASE 
        WHEN v.total_vacancy_overlap_days = v.invoice_days THEN 'Fully Vacant'
        WHEN v.total_vacancy_overlap_days > 0 THEN 'Partially Vacant'
        ELSE 'Occupied'
    END as period_type
FROM invoices i
JOIN invoice_validation v ON i.id = v.invoice_id
WHERE v.total_vacancy_overlap_days > 0
ORDER BY v.total_vacancy_overlap_days DESC;
```

### **Monthly Invoice Summary**
```sql
SELECT 
    DATE_TRUNC('month', i.billing_period_start) as month,
    COUNT(*) as invoice_count,
    SUM(i.gross_amount) as total_amount,
    AVG(v.daily_rate) as avg_daily_rate,
    COUNT(CASE WHEN v.validation_status = 'Valid' THEN 1 END) as valid_count
FROM invoices i
LEFT JOIN invoice_validation v ON i.id = v.invoice_id
GROUP BY DATE_TRUNC('month', i.billing_period_start)
ORDER BY month DESC;
```

### **Units Without Leases**
```sql
SELECT 
    u.unit_id,
    u.building_name,
    u.city,
    COUNT(i.id) as invoice_count
FROM units u
LEFT JOIN leases l ON u.unit_id = l.unit_id AND u.tenant_id = l.tenant_id
LEFT JOIN invoices i ON u.unit_id = i.unit_id AND u.tenant_id = i.tenant_id
WHERE l.id IS NULL
GROUP BY u.id, u.unit_id, u.building_name, u.city
ORDER BY invoice_count DESC;
```

---

## 💡 Tips

1. **Filter by Tenant**: Add `WHERE tenant_id = 1` to any query to filter by specific tenant
2. **Export Results**: Click the "Export" tab in Supabase SQL Editor to download as CSV
3. **Save Queries**: Click the star icon to save frequently used queries
4. **Share Queries**: Use the "Share" button to share queries with your team

---

## 🎯 Quick Stats Query

```sql
-- Overall Statistics
SELECT 
    (SELECT COUNT(*) FROM tenants) as total_tenants,
    (SELECT COUNT(*) FROM units) as total_units,
    (SELECT COUNT(*) FROM leases) as total_leases,
    (SELECT COUNT(*) FROM invoices) as total_invoices,
    (SELECT COUNT(*) FROM invoice_validation WHERE validation_status = 'Valid') as valid_invoices,
    (SELECT COUNT(*) FROM invoice_validation WHERE validation_status = 'Invalid') as invalid_invoices,
    (SELECT SUM(gross_amount) FROM invoices) as total_invoice_amount;
```

---

**Happy Querying! 🚀**

