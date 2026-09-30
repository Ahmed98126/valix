-- Migration: Add address column to invoices table
-- Date: 2025-12-31
-- Description: Adds address field to store full address extracted from PDF invoices

-- Add address column to invoices table
ALTER TABLE invoices 
ADD COLUMN IF NOT EXISTS address VARCHAR;

-- Add comment to document the column
COMMENT ON COLUMN invoices.address IS 'Full address extracted from invoice (for PDF extraction)';

