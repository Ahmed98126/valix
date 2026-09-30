-- Migration: Add tables for enhanced PDF extraction (Phase 2)
-- Created: 2026-03-11

-- Table 1: Supplier Extraction Patterns
CREATE TABLE IF NOT EXISTS supplier_extraction_patterns (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER REFERENCES tenants(id) ON DELETE CASCADE,
    supplier_name VARCHAR NOT NULL,
    field_name VARCHAR NOT NULL,
    pattern_type VARCHAR NOT NULL,
    pattern_value TEXT NOT NULL,
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    created_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    notes TEXT
);

-- Indexes for supplier_extraction_patterns
CREATE INDEX IF NOT EXISTS idx_supplier_extraction_patterns_tenant_id ON supplier_extraction_patterns(tenant_id);
CREATE INDEX IF NOT EXISTS idx_supplier_extraction_patterns_supplier_name ON supplier_extraction_patterns(supplier_name);
CREATE INDEX IF NOT EXISTS idx_supplier_extraction_patterns_field_name ON supplier_extraction_patterns(field_name);
CREATE INDEX IF NOT EXISTS idx_supplier_extraction_patterns_active ON supplier_extraction_patterns(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_supplier_extraction_patterns_tenant_active ON supplier_extraction_patterns(tenant_id, is_active) WHERE is_active = TRUE;

-- Table 2: Manual Review Queue
CREATE TABLE IF NOT EXISTS manual_review_queue (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    pdf_path VARCHAR NOT NULL,
    original_filename VARCHAR,
    extracted_data TEXT,
    raw_data TEXT,
    confidence_scores TEXT,
    status VARCHAR DEFAULT 'Pending' NOT NULL,
    reviewed_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    reviewed_at TIMESTAMP,
    notes TEXT
);

-- Indexes for manual_review_queue
CREATE INDEX IF NOT EXISTS idx_manual_review_queue_tenant_id ON manual_review_queue(tenant_id);
CREATE INDEX IF NOT EXISTS idx_manual_review_queue_status ON manual_review_queue(status);
CREATE INDEX IF NOT EXISTS idx_manual_review_queue_created_at ON manual_review_queue(created_at);
CREATE INDEX IF NOT EXISTS idx_manual_review_queue_tenant_status ON manual_review_queue(tenant_id, status);

-- Row-level security policies for tenant isolation
ALTER TABLE supplier_extraction_patterns ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS supplier_extraction_patterns_tenant_isolation ON supplier_extraction_patterns;
CREATE POLICY supplier_extraction_patterns_tenant_isolation ON supplier_extraction_patterns
    USING (tenant_id IS NULL OR tenant_id = current_setting('app.current_tenant_id')::INTEGER);

ALTER TABLE manual_review_queue ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS manual_review_queue_tenant_isolation ON manual_review_queue;
CREATE POLICY manual_review_queue_tenant_isolation ON manual_review_queue
    USING (tenant_id = current_setting('app.current_tenant_id')::INTEGER);

-- Comments
COMMENT ON TABLE supplier_extraction_patterns IS 'Extraction patterns for specific suppliers';
COMMENT ON COLUMN supplier_extraction_patterns.supplier_name IS 'Supplier name (e.g., "British Gas", "E.ON")';
COMMENT ON COLUMN supplier_extraction_patterns.field_name IS 'Field to extract (e.g., "supplier_account_number")';
COMMENT ON COLUMN supplier_extraction_patterns.pattern_type IS 'Type of pattern (e.g., "regex", "xpath", "table_cell")';
COMMENT ON COLUMN supplier_extraction_patterns.pattern_value IS 'The actual pattern (regex, xpath, etc.)';
COMMENT ON COLUMN supplier_extraction_patterns.priority IS 'Higher priority patterns are tried first';
COMMENT ON COLUMN supplier_extraction_patterns.tenant_id IS 'NULL for global patterns, tenant ID for tenant-specific patterns';

COMMENT ON TABLE manual_review_queue IS 'Queue for invoices needing manual review';
COMMENT ON COLUMN manual_review_queue.pdf_path IS 'Path to the PDF file';
COMMENT ON COLUMN manual_review_queue.extracted_data IS 'JSON string of extracted data';
COMMENT ON COLUMN manual_review_queue.raw_data IS 'JSON string of raw Azure extraction';
COMMENT ON COLUMN manual_review_queue.confidence_scores IS 'JSON string of confidence scores';
COMMENT ON COLUMN manual_review_queue.status IS 'Status: "Pending", "In Review", "Completed", "Failed"';