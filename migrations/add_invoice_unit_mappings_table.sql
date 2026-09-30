-- Migration: Add invoice_unit_mappings table for custom account number to unit_id mappings
-- Created: 2026-01-05

CREATE TABLE IF NOT EXISTS invoice_unit_mappings (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    supplier_account_number VARCHAR NOT NULL,
    unit_id VARCHAR NOT NULL,
    supplier_name VARCHAR,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    created_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    notes TEXT,
    
    -- Unique constraint: one active mapping per tenant + account number
    UNIQUE(tenant_id, supplier_account_number)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_invoice_unit_mappings_tenant_id ON invoice_unit_mappings(tenant_id);
CREATE INDEX IF NOT EXISTS idx_invoice_unit_mappings_account_number ON invoice_unit_mappings(supplier_account_number);
CREATE INDEX IF NOT EXISTS idx_invoice_unit_mappings_unit_id ON invoice_unit_mappings(unit_id);
CREATE INDEX IF NOT EXISTS idx_invoice_unit_mappings_active ON invoice_unit_mappings(tenant_id, is_active) WHERE is_active = TRUE;

COMMENT ON TABLE invoice_unit_mappings IS 'Custom mappings of supplier account numbers to units for invoice-to-unit matching';
COMMENT ON COLUMN invoice_unit_mappings.supplier_account_number IS 'The account number from the invoice (e.g., "1234 1234 1234")';
COMMENT ON COLUMN invoice_unit_mappings.unit_id IS 'The unit_id to map to (must exist in units table)';
COMMENT ON COLUMN invoice_unit_mappings.is_active IS 'Can disable mappings without deleting them';

