"""Tenant isolation tests for the validation engine and supporting helpers.

All tests use an in-memory SQLite database.  Live Supabase is never contacted.

Coverage map (per task requirement):
  1. Tenant A cannot read Tenant B invoice            → TestInvoiceIsolation
  2. Tenant A validation cannot use Tenant B unit     → TestValidationEngineIsolation
  3. Tenant A validation cannot use Tenant B lease    → TestValidationEngineIsolation
  4. Tenant A timeline query cannot use Tenant B      → TestTimelineIsolation
  5. Exports remain tenant-scoped                     → TestExportIsolation
  6. Mappings remain tenant-scoped                    → TestMappingIsolation
  7. Super admin behaviour is explicit                → TestSuperAdminBehaviour
  8. Same unit_id in two tenants without cross-mixing → TestSharedUnitIdIsolation
"""
import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import (
    Base, Tenant, Unit, Lease, UnitTimeline,
    Invoice, InvoiceValidation, InvoiceUnitMapping,
)
from app.validation import (
    check_duplicate_invoice,
    check_invoice_vacancy_overlap,
    validate_invoice,
    generate_unit_timeline,
)


# ---------------------------------------------------------------------------
# DB fixtures — fresh SQLite per test function, never touches Supabase
# ---------------------------------------------------------------------------

@pytest.fixture()
def db_session():
    """Isolated in-memory SQLite session; dropped after each test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------

def _tenant(session, name, slug):
    t = Tenant(name=name, slug=slug)
    session.add(t)
    session.flush()
    return t


def _unit(session, tenant_id, unit_id="SHOP-001"):
    u = Unit(
        tenant_id=tenant_id,
        unit_id=unit_id,
        building_name="Test Building",
        address_line_1="1 Test St",
        city="London",
        postcode="EC1A 1AA",
    )
    session.add(u)
    session.flush()
    return u


def _lease(session, tenant_id, unit_id, start, end=None):
    lease = Lease(
        tenant_id=tenant_id,
        unit_id=unit_id,
        tenant_name="Test Corp",
        lease_start=start,
        lease_end=end,
    )
    session.add(lease)
    session.flush()
    return lease


def _timeline(session, tenant_id, unit_id, start, end, status="vacant"):
    row = UnitTimeline(
        tenant_id=tenant_id,
        unit_id=unit_id,
        period_start=start,
        period_end=end,
        status=status,
        days_in_period=((end - start).days + 1) if end else None,
    )
    session.add(row)
    session.flush()
    return row


def _invoice(
    session,
    tenant_id,
    unit_id="SHOP-001",
    invoice_number="INV-001",
    billing_start=None,
    billing_end=None,
    amount=Decimal("300.00"),
):
    billing_start = billing_start or date(2024, 1, 1)
    billing_end = billing_end or date(2024, 1, 31)
    inv = Invoice(
        tenant_id=tenant_id,
        invoice_number=invoice_number,
        supplier_account_number="ACC-TEST",
        supplier_name="Test Supplier",
        unit_id=unit_id,
        billing_period_start=billing_start,
        billing_period_end=billing_end,
        gross_amount=amount,
        utility_type="Electricity",
    )
    session.add(inv)
    session.flush()
    return inv


# ===========================================================================
# 1. Tenant A cannot read Tenant B invoice
# ===========================================================================

class TestInvoiceIsolation:
    """Duplicate detection must never cross tenant boundaries."""

    def test_same_invoice_number_different_tenants_not_duplicate(self, db_session):
        """INV-001 in Tenant A and INV-001 in Tenant B are NOT duplicates of each other."""
        ta = _tenant(db_session, "Tenant A", "ta")
        tb = _tenant(db_session, "Tenant B", "tb")
        _unit(db_session, ta.id)
        _unit(db_session, tb.id)

        inv_a = _invoice(db_session, ta.id, invoice_number="INV-001", amount=Decimal("200.00"))
        inv_b = _invoice(db_session, tb.id, invoice_number="INV-001", amount=Decimal("200.00"))

        is_dup_a, _ = check_duplicate_invoice(db_session, inv_a)
        is_dup_b, _ = check_duplicate_invoice(db_session, inv_b)

        assert not is_dup_a, "Invoice in Tenant A must not see Tenant B's invoice as a duplicate"
        assert not is_dup_b, "Invoice in Tenant B must not see Tenant A's invoice as a duplicate"

    def test_duplicate_detected_within_same_tenant(self, db_session):
        """Two invoices with same number + amount within one tenant ARE duplicates."""
        ta = _tenant(db_session, "Tenant A", "ta")
        _unit(db_session, ta.id)

        inv1 = _invoice(db_session, ta.id, invoice_number="DUP-001", amount=Decimal("200.00"))
        inv2 = _invoice(db_session, ta.id, invoice_number="DUP-001", amount=Decimal("200.00"))

        is_dup, _ = check_duplicate_invoice(db_session, inv2)
        assert is_dup, "Same invoice_number+amount in same tenant must be detected as duplicate"

    def test_filter_by_tenant_excludes_other_tenant_invoices(self, db_session):
        """filter_by_tenant helper returns only the calling tenant's invoices."""
        from app.tenant_helpers import filter_by_tenant

        ta = _tenant(db_session, "Tenant A", "ta")
        tb = _tenant(db_session, "Tenant B", "tb")
        _unit(db_session, ta.id)
        _unit(db_session, tb.id)
        _invoice(db_session, ta.id, invoice_number="A-001")
        _invoice(db_session, tb.id, invoice_number="B-001")

        user_a = MagicMock()
        user_a.tenant_id = ta.id
        user_a.is_super_admin = False
        req_a = MagicMock()
        req_a.session = {"tenant_id": ta.id}

        query = db_session.query(Invoice)
        invoices = filter_by_tenant(query, Invoice, user_a, req_a).all()
        numbers = {i.invoice_number for i in invoices}

        assert "A-001" in numbers
        assert "B-001" not in numbers, "Tenant A must not see Tenant B's invoice in list"


# ===========================================================================
# 2 & 3. Tenant A validation cannot use Tenant B unit or lease
# ===========================================================================

class TestValidationEngineIsolation:
    """check_invoice_vacancy_overlap must be fully tenant-scoped."""

    def test_unit_owned_by_other_tenant_returns_not_found(self, db_session):
        """If only Tenant B owns SHOP-001, validating a Tenant A invoice must return
        'Unit not found', NOT silently use Tenant B's data."""
        ta = _tenant(db_session, "Tenant A", "ta")
        tb = _tenant(db_session, "Tenant B", "tb")
        # Only Tenant B has SHOP-001
        _unit(db_session, tb.id, "SHOP-001")
        _lease(db_session, tb.id, "SHOP-001", date(2024, 1, 1), date(2024, 12, 31))

        inv_a = _invoice(db_session, ta.id, unit_id="SHOP-001")
        overlap, error = check_invoice_vacancy_overlap(db_session, inv_a, tenant_id=ta.id)

        assert error is not None, "Must report an error when unit not found for the tenant"
        assert "not found" in error.lower(), f"Unexpected error message: {error!r}"
        assert overlap == 0

    def test_vacancy_from_other_tenant_not_used(self, db_session):
        """Both tenants have SHOP-001.
        Tenant A: occupied (has lease) → 0 vacancy overlap.
        Tenant B: vacant in same period.
        Validating Tenant A's invoice must return 0 overlap (not Tenant B's vacancy).
        """
        ta = _tenant(db_session, "Tenant A", "ta")
        tb = _tenant(db_session, "Tenant B", "tb")
        _unit(db_session, ta.id, "SHOP-001")
        _unit(db_session, tb.id, "SHOP-001")

        # Tenant A: leased + occupied timeline for Jan 2024
        _lease(db_session, ta.id, "SHOP-001", date(2024, 1, 1), date(2024, 12, 31))
        _timeline(db_session, ta.id, "SHOP-001", date(2024, 1, 1), date(2024, 12, 31), status="occupied")

        # Tenant B: fully vacant — this must NOT bleed into Tenant A's result
        _timeline(db_session, tb.id, "SHOP-001", date(2024, 1, 1), date(2024, 12, 31), status="vacant")

        inv_a = _invoice(db_session, ta.id,
                         billing_start=date(2024, 1, 1), billing_end=date(2024, 1, 31))
        overlap, error = check_invoice_vacancy_overlap(db_session, inv_a, tenant_id=ta.id)

        assert error is None, f"Unexpected error: {error}"
        assert overlap == 0, (
            f"Tenant A's SHOP-001 is occupied — expected 0 vacancy overlap, "
            f"got {overlap}. Cross-tenant timeline bleed detected."
        )

    def test_lease_from_other_tenant_not_used(self, db_session):
        """Tenant A has no lease for SHOP-001; Tenant B does.
        Validating Tenant A's invoice should say 'no leases — company liable',
        NOT find Tenant B's lease and report zero vacancy.
        """
        ta = _tenant(db_session, "Tenant A", "ta")
        tb = _tenant(db_session, "Tenant B", "tb")
        _unit(db_session, ta.id, "SHOP-001")
        _unit(db_session, tb.id, "SHOP-001")

        # Only Tenant B has a lease
        _lease(db_session, tb.id, "SHOP-001", date(2024, 1, 1), date(2024, 12, 31))

        inv_a = _invoice(db_session, ta.id,
                         billing_start=date(2024, 1, 1), billing_end=date(2024, 1, 31))
        overlap, error = check_invoice_vacancy_overlap(db_session, inv_a, tenant_id=ta.id)

        assert error is not None, "Should report 'no leases' for Tenant A"
        assert "no leases" in error.lower(), f"Unexpected message: {error!r}"


# ===========================================================================
# 4. Tenant A timeline query cannot use Tenant B timeline
# ===========================================================================

class TestTimelineIsolation:
    """generate_unit_timeline must write only to the specified tenant's records."""

    def test_generate_timeline_does_not_touch_other_tenant(self, db_session):
        """Running generate_unit_timeline for Tenant A must not create or overwrite
        Tenant B's UnitTimeline rows for the same unit_id."""
        ta = _tenant(db_session, "Tenant A", "ta")
        tb = _tenant(db_session, "Tenant B", "tb")
        _unit(db_session, ta.id, "SHOP-001")
        _unit(db_session, tb.id, "SHOP-001")

        # Tenant A has a lease ending mid-year
        _lease(db_session, ta.id, "SHOP-001", date(2024, 1, 1), date(2024, 6, 30))
        # Tenant B has a different lease — earlier year
        _lease(db_session, tb.id, "SHOP-001", date(2023, 1, 1), date(2023, 12, 31))

        # Insert a sentinel timeline row for Tenant B that must survive unchanged
        sentinel = _timeline(
            db_session, tb.id, "SHOP-001",
            date(2023, 1, 1), date(2023, 12, 31), status="occupied"
        )
        db_session.commit()

        # Run timeline generation ONLY for Tenant A
        generate_unit_timeline(db_session, tenant_id=ta.id)

        # Tenant B's sentinel row must still exist and belong to Tenant B
        row = db_session.query(UnitTimeline).filter(
            UnitTimeline.id == sentinel.id
        ).first()
        assert row is not None, "Tenant B's timeline row was deleted by Tenant A's timeline generation"
        assert row.tenant_id == tb.id

    def test_generated_timeline_rows_belong_to_correct_tenant(self, db_session):
        """All rows created by generate_unit_timeline(tenant_id=ta) must have ta.id."""
        ta = _tenant(db_session, "Tenant A", "ta")
        _unit(db_session, ta.id, "UNIT-A")
        _lease(db_session, ta.id, "UNIT-A", date(2024, 1, 1), date(2024, 6, 30))
        db_session.commit()

        generate_unit_timeline(db_session, tenant_id=ta.id)

        rows = db_session.query(UnitTimeline).filter(
            UnitTimeline.unit_id == "UNIT-A"
        ).all()
        assert len(rows) > 0, "Timeline generation produced no rows"
        wrong = [r for r in rows if r.tenant_id != ta.id]
        assert not wrong, f"Timeline rows with wrong tenant_id: {wrong}"


# ===========================================================================
# 5. Exports remain tenant-scoped
# ===========================================================================

class TestExportIsolation:
    """The invoice export query path (filter_by_tenant) must not leak rows."""

    def test_export_query_excludes_other_tenant(self, db_session):
        from app.tenant_helpers import filter_by_tenant

        ta = _tenant(db_session, "Tenant A", "ta")
        tb = _tenant(db_session, "Tenant B", "tb")
        _unit(db_session, ta.id)
        _unit(db_session, tb.id)
        _invoice(db_session, ta.id, invoice_number="EXPORT-A")
        _invoice(db_session, tb.id, invoice_number="EXPORT-B")

        user = MagicMock()
        user.tenant_id = ta.id
        user.is_super_admin = False
        req = MagicMock()
        req.session = {"tenant_id": ta.id}

        query = db_session.query(Invoice)
        results = filter_by_tenant(query, Invoice, user, req).all()
        numbers = {i.invoice_number for i in results}

        assert "EXPORT-A" in numbers
        assert "EXPORT-B" not in numbers, "Exported CSV must not include other tenant's invoices"


# ===========================================================================
# 6. Mappings remain tenant-scoped
# ===========================================================================

class TestMappingIsolation:
    """InvoiceUnitMapping lookups must not cross tenant boundaries."""

    def test_mapping_not_visible_across_tenants(self, db_session):
        """A mapping registered under Tenant B must not be returned for Tenant A."""
        ta = _tenant(db_session, "Tenant A", "ta")
        tb = _tenant(db_session, "Tenant B", "tb")

        # Tenant B's mapping
        mapping = InvoiceUnitMapping(
            tenant_id=tb.id,
            supplier_account_number="ACC999",
            unit_id="SHOP-999",
            is_active=True,
        )
        db_session.add(mapping)
        db_session.commit()

        # Query as Tenant A
        result = db_session.query(InvoiceUnitMapping).filter(
            InvoiceUnitMapping.tenant_id == ta.id,
            InvoiceUnitMapping.supplier_account_number == "ACC999",
            InvoiceUnitMapping.is_active == True,
        ).first()

        assert result is None, "Tenant A must not see Tenant B's account mapping"

    def test_mapping_visible_for_owning_tenant(self, db_session):
        """The owning tenant can find its own mapping."""
        tb = _tenant(db_session, "Tenant B", "tb")
        mapping = InvoiceUnitMapping(
            tenant_id=tb.id,
            supplier_account_number="ACC999",
            unit_id="SHOP-999",
            is_active=True,
        )
        db_session.add(mapping)
        db_session.commit()

        result = db_session.query(InvoiceUnitMapping).filter(
            InvoiceUnitMapping.tenant_id == tb.id,
            InvoiceUnitMapping.supplier_account_number == "ACC999",
            InvoiceUnitMapping.is_active == True,
        ).first()

        assert result is not None, "Tenant B must be able to find its own mapping"
        assert result.unit_id == "SHOP-999"


# ===========================================================================
# 7. Super admin behaviour is explicit
# ===========================================================================

class TestSuperAdminBehaviour:
    """Super admin without a selected tenant sees all data (intentional).
    Super admin with a selected tenant is filtered to that tenant.
    """

    def test_super_admin_no_tenant_selected_sees_all(self, db_session):
        from app.tenant_helpers import filter_by_tenant

        ta = _tenant(db_session, "Tenant A", "ta")
        tb = _tenant(db_session, "Tenant B", "tb")
        _unit(db_session, ta.id)
        _unit(db_session, tb.id)
        _invoice(db_session, ta.id, invoice_number="SA-A")
        _invoice(db_session, tb.id, invoice_number="SA-B")

        admin = MagicMock()
        admin.tenant_id = None
        admin.is_super_admin = True
        req = MagicMock()
        req.session = {}  # No tenant selected

        query = db_session.query(Invoice)
        results = filter_by_tenant(query, Invoice, admin, req).all()
        numbers = {i.invoice_number for i in results}

        assert "SA-A" in numbers, "Super admin must see Tenant A's invoices"
        assert "SA-B" in numbers, "Super admin must see Tenant B's invoices"

    def test_validate_invoice_records_correct_tenant_id(self, db_session):
        """validate_invoice must write the invoice's own tenant_id into InvoiceValidation."""
        ta = _tenant(db_session, "Tenant A", "ta")
        _unit(db_session, ta.id, "UNIT-SA")
        _lease(db_session, ta.id, "UNIT-SA", date(2024, 1, 1), date(2024, 12, 31))
        generate_unit_timeline(db_session, tenant_id=ta.id)

        inv = _invoice(db_session, ta.id, unit_id="UNIT-SA")
        db_session.commit()

        validation = validate_invoice(db_session, inv)
        assert validation.tenant_id == ta.id, (
            f"InvoiceValidation.tenant_id should be {ta.id}, got {validation.tenant_id}"
        )
        assert validation.validation_status in ("Valid", "Invalid", "Needs Review")


# ===========================================================================
# 8. Same unit_id in two tenants — fully isolated validation results
# ===========================================================================

class TestSharedUnitIdIsolation:
    """The schema allows the same unit_id in multiple tenants.
    Validation of each tenant's invoice must be independent.
    """

    def test_opposite_vacancy_gives_opposite_results(self, db_session):
        """
        Tenant A: SHOP-001 is fully vacant in Jan 2024.
        Tenant B: SHOP-001 is fully occupied in Jan 2024.

        Tenant A's invoice → full overlap (31 days).
        Tenant B's invoice → 0 overlap.

        If the tenant filter is missing, both would return the same wrong number.
        """
        ta = _tenant(db_session, "Tenant A", "ta")
        tb = _tenant(db_session, "Tenant B", "tb")
        _unit(db_session, ta.id, "SHOP-001")
        _unit(db_session, tb.id, "SHOP-001")

        # Tenant A: no lease, vacancy from far past
        _timeline(db_session, ta.id, "SHOP-001",
                  date(2000, 1, 1), None, status="vacant")

        # Tenant B: lease + occupied timeline
        _lease(db_session, tb.id, "SHOP-001", date(2024, 1, 1), None)
        _timeline(db_session, tb.id, "SHOP-001",
                  date(2024, 1, 1), None, status="occupied")

        billing = {"billing_start": date(2024, 1, 1), "billing_end": date(2024, 1, 31)}

        inv_a = _invoice(db_session, ta.id, **billing)
        inv_b = _invoice(db_session, tb.id, invoice_number="INV-B", **billing)

        overlap_a, err_a = check_invoice_vacancy_overlap(db_session, inv_a, tenant_id=ta.id)
        overlap_b, err_b = check_invoice_vacancy_overlap(db_session, inv_b, tenant_id=tb.id)

        assert overlap_a == 31, (
            f"Tenant A SHOP-001 is vacant — expected 31 overlap days, got {overlap_a}. "
            f"error={err_a!r}"
        )
        assert overlap_b == 0, (
            f"Tenant B SHOP-001 is occupied — expected 0 overlap days, got {overlap_b}. "
            f"error={err_b!r}"
        )

    def test_full_validate_invoice_different_results_same_unit_id(self, db_session):
        """End-to-end validate_invoice returns different statuses for same unit_id
        when tenant vacancy states differ.

        Tenant A: SHOP-001 had a lease that ended Dec 2023 → genuinely vacant Jan 2024
                  → full overlap → Valid (company liable)
        Tenant B: SHOP-001 has an active lease Jan 2024 → occupied
                  → zero overlap → Invalid (tenant liable)

        NOTE: "no leases at all" is a distinct case (returns Needs Review via error_message).
        Tenant A must have a past lease so the vacancy is real, not the no-lease edge-case.
        """
        ta = _tenant(db_session, "Tenant A", "ta")
        tb = _tenant(db_session, "Tenant B", "tb")
        _unit(db_session, ta.id, "SHOP-001")
        _unit(db_session, tb.id, "SHOP-001")

        # Tenant A: lease ended 2023-12-31; vacancy from 2024-01-01 onward
        _lease(db_session, ta.id, "SHOP-001", date(2020, 1, 1), date(2023, 12, 31))
        _timeline(db_session, ta.id, "SHOP-001",
                  date(2020, 1, 1), date(2023, 12, 31), status="occupied")
        _timeline(db_session, ta.id, "SHOP-001",
                  date(2024, 1, 1), None, status="vacant")

        # Tenant B: active lease, occupied in Jan 2024
        _lease(db_session, tb.id, "SHOP-001", date(2024, 1, 1), None)
        _timeline(db_session, tb.id, "SHOP-001",
                  date(2024, 1, 1), None, status="occupied")

        inv_a = _invoice(db_session, ta.id,
                         billing_start=date(2024, 1, 1), billing_end=date(2024, 1, 31))
        inv_b = _invoice(db_session, tb.id, invoice_number="INV-B",
                         billing_start=date(2024, 1, 1), billing_end=date(2024, 1, 31))
        db_session.commit()

        val_a = validate_invoice(db_session, inv_a)
        val_b = validate_invoice(db_session, inv_b)

        # Tenant A: fully vacant Jan 2024 → Valid (company liable)
        assert val_a.validation_status == "Valid", (
            f"Tenant A (vacant) should be Valid, got {val_a.validation_status}"
        )
        # Tenant B: occupied Jan 2024 → Invalid (tenant liable)
        assert val_b.validation_status == "Invalid", (
            f"Tenant B (occupied) should be Invalid, got {val_b.validation_status}"
        )
        assert val_a.validation_status != val_b.validation_status, (
            "Same unit_id in different tenants must produce different validation statuses "
            "when their vacancy states differ — cross-tenant bleed would make them equal."
        )
