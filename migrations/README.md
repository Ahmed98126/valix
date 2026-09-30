# Database Migrations

This directory contains SQL migration scripts for the invoice validator database.

## How to Run Migrations

### Option 1: Using Supabase Dashboard (Recommended)

1. Go to your Supabase project dashboard
2. Navigate to **SQL Editor**
3. Click **New Query**
4. Copy and paste the contents of the migration file
5. Click **Run** to execute the migration

### Option 2: Using Supabase CLI

If you have Supabase CLI installed:

```bash
supabase db push
```

### Option 3: Using psql

If you have direct database access:

```bash
psql -h <your-supabase-host> -U postgres -d postgres -f migrations/add_address_to_invoices.sql
```

## Migration Files

- `add_address_to_invoices.sql` - Adds `address` column to `invoices` table (2025-12-31)

## Important Notes

- Always backup your database before running migrations
- Test migrations on a development/staging environment first
- Run migrations during low-traffic periods if possible
- The `IF NOT EXISTS` clause prevents errors if the column already exists

