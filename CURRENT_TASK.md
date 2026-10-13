# Valix — Current Task

> Read [ROADMAP.md](ROADMAP.md) (including the permanent development rules in §10) and [BACKLOG.md](BACKLOG.md) before any development.
> Last updated: 2026-10-13.

## Active task

**No task approved.**

Do not start development until the owner approves a task below (or another backlog item) and this file is updated with its details.

---

## Pre-requisite owner actions (not development tasks)

These are outstanding git operations that the agent was told not to perform automatically:

1. **Commit the uncommitted PDF security work.** Working tree currently has modified `app/routes/pdf_viewer.py`, modified `app/routes/manual_review.py`, and untracked `tests/unit/test_pdf_tenant_auth.py`. Suggested message: `fix(security): disable dead PDF endpoints and harden manual-review PDF route`.
2. **Push to GitHub** from your own terminal (commit `732f64b` and the commit above); the agent environment has no GitHub credentials. A push triggers the GitHub → Azure deployment.
3. Note: the new tests pass in isolation (27 passed, 1 skipped) but `test_pdf_tenant_auth.py` fails in a full-suite run (VAL-009). Consider that before relying on a future CI test gate.

---

## Recommended next task (PROPOSED — NOT APPROVED)

| Field | Value |
|---|---|
| **Task ID** | VAL-001 |
| **Objective** | Make invoice validation tenant-safe: every unit, lease and timeline lookup used by validation must be filtered by the invoice's `tenant_id`, so one tenant can never be validated against another tenant's data. |
| **Why this one** | Confirmed cross-tenant data-integrity defect (`app/validation.py`); matches the current "Phase 2 — security & correctness" phase; contradicts the documented isolation guarantee. |
| **In scope** | `check_invoice_vacancy_overlap`, `calculate_vacancy_periods` and any helper they call inside `app/validation.py`; passing `tenant_id` from `validate_invoice`; new tests using two tenants that share a `unit_id`. |
| **Out of scope** | Changing validation business rules or determinations; DB schema/constraints/RLS (VAL-015); re-validating existing production data (needs separate approval); other routes' isolation review (VAL-003); CSV bug (VAL-002); test-harness repair (VAL-009); any refactor. |
| **Expected files** | `app/validation.py` (modify); new test file under `tests/unit/` (e.g. `test_validation_tenant_scope.py`). No other application files expected. Any caller that must change to supply `tenant_id` will be listed and approved before editing. |
| **Acceptance criteria** | (1) With two tenants having the same `unit_id` but different leases/vacancy, each tenant's invoice is validated only against its own data (tests fail before the change, pass after). (2) Results for single-tenant data are identical to before (existing validation tests unchanged and passing). (3) No query in the validation path touching `Unit`, `Lease` or `UnitTimeline` lacks a `tenant_id` filter (checked by search, noted in the report). (4) Invoices with no `tenant_id` fail closed or retain documented behaviour — decision recorded. |
| **Required tests** | New two-tenant unit tests; `tests/unit/test_validation.py`; `tests/unit/test_pdf_path_traversal.py` and `tests/unit/test_pdf_tenant_auth.py` run in isolation (regression); no live Supabase or Azure. |
| **Status** | Done (verified) — pending owner commit/push |
| **Blockers** | None. Owner must commit and push (see pre-requisite actions). |

### Alternative if you prefer a functional fix first
VAL-002 (CSV import `errors='ignore'` → `encoding_errors`) is also P0, small, and restores a broken core workflow. It could be approved instead, or as the immediate follow-up.

---

## Open questions needing owner decision

1. Approve VAL-001 as the next task (or choose VAL-002 / another item)?
2. Confirm or amend the derived **MVP scope** in [ROADMAP.md](ROADMAP.md) §2 — especially: are CSV invoices used in production, and what does "line-item extraction" (VAL-008) need to produce?
3. Do any production tenants currently share `unit_id` values? (Determines urgency/impact of VAL-001.)
4. Has the Azure Document Intelligence key been rotated (VAL-011)?
5. Approve the documentation archive plan ([ROADMAP.md](ROADMAP.md) §8): move ~180 superseded docs into `docs/archive/` (git history preserved), rewrite `README.md`, correct `TENANT_ISOLATION_EXPLANATION.md`?
6. Should super admins be able to view manual-review PDFs (VAL-022)?
7. Where should source PDFs live long-term (Azure Blob vs App Service disk) for VAL-004?

---

## Template for the next approved task

```
Task ID:
Objective:
Scope:
Out of scope:
Expected files:
Acceptance criteria:
Required tests:
Status:        (Approved | In progress | Blocked | Done (verified))
Blockers:
```
