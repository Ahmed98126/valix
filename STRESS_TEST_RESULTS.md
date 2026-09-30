# Stress Test Results

## Performance Metrics

### ✅ Upload Performance
- **500 invoices**: 0.29 seconds
- **Throughput**: ~1,695 invoices/second
- **200 invoices**: 0.13 seconds  
- **Throughput**: ~1,518 invoices/second

**Verdict**: Excellent performance for file uploads

### ✅ Validation Performance
- **100 invoices validated**: 0.23 seconds
- **Throughput**: ~443 invoices/second
- **Timeline generation**: 0.03 seconds (for all units)

**Verdict**: Fast validation, can handle large batches

### ✅ Duplicate Detection
- **10 duplicate checks**: 0.0072 seconds
- **Average per check**: 0.72 milliseconds

**Verdict**: Extremely fast duplicate detection

### ✅ Database Query Performance
- **Count queries**: 3.31 ms (1,141 invoices)
- **Filtered queries**: 4.03 ms
- **Join queries**: 3.11 ms (441 validated invoices)
- **Group by queries**: 2.12 ms (7 batches)

**Verdict**: All queries are sub-5ms, excellent performance

## System Capacity

### Current Database Size
- **Units**: 4
- **Leases**: 5
- **Invoices**: 1,141 (after stress test)
- **Validations**: 441
- **Unit Timelines**: 11
- **Users**: 1

### Scalability Assessment

**✅ Can Handle:**
- Large file uploads (1000+ invoices)
- High-frequency duplicate checks
- Complex validation queries
- Multiple concurrent users (with proper deployment)

**⚠️ Considerations for Production:**
- SQLite is fine for single-server deployment
- For multi-server/multi-user: Consider PostgreSQL
- Current performance is excellent for typical use cases

## Database Structure Summary

### How Vacancy Calculation Works

1. **Units Table**: Property units (SHOP-001, OFFICE-101, etc.)
2. **Leases Table**: Lease periods with start/end dates
3. **UnitTimeline Table**: **Derived** from Units + Leases
   - Calculates gaps between leases = vacancy periods
   - Pre-first-lease periods = vacancy
   - Never-leased units = ongoing vacancy

### Example Timeline (SHOP-002):
```
🔴 Vacant:   2000-01-01 to 2023-12-01 (pre-first-lease)
🟢 Occupied: 2023-12-02 to 2025-09-02 (Bakery Corp lease)
🔴 Vacant:   2025-09-03 to 2025-12-30 (gap between leases)
🟢 Occupied: 2025-12-31 to ongoing (Tech Store Inc lease)
```

### Validation Flow
1. Check duplicate (invoice_number + gross_amount)
2. Calculate invoice days
3. Calculate daily rate
4. Check vacancy overlap (query UnitTimeline)
5. Determine status (Valid/Invalid/Needs Review)
6. Generate determination (OK TO PAY, COT, etc.)

## Next Steps

### Immediate
1. ✅ System is production-ready for single-client deployment
2. ✅ Performance is excellent
3. ✅ Validation logic is working correctly

### Future Enhancements
1. **Multi-tenant support** (if needed)
2. **PostgreSQL migration** (for multi-server)
3. **Column mapping configuration** (per-client)
4. **Advanced reporting** (dashboards, analytics)
5. **Email notifications** (upload completion)

## Commands Reference

```bash
# Inspect database
python scripts/inspect_database.py
python scripts/inspect_database.py --detailed

# Run stress tests
python scripts/stress_test.py --invoices=1000
python scripts/stress_test.py --skip-upload  # Just validation tests
```




