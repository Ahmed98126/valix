# Valix — Backlog

> Single source of truth for known work, defects, risks and proposals.
> Last reconciled: 2026-10-10 (documentation audit). Companion files: [ROADMAP.md](ROADMAP.md), [CURRENT_TASK.md](CURRENT_TASK.md).

## How to read this file

**Priority**

| Level | Meaning |
|---|---|
| P0 | Core workflow broken, or confirmed cross-tenant / data-integrity risk. Blocks further feature work. |
| P1 | Needed for a trustworthy, testable, secure MVP. Do next. |
| P2 | Important hardening / hygiene. Schedule after P0–P1. |
| P3 | Cleanup, product decisions, or unapproved proposals. |

**Evidence labels** (used on every item — nothing here is stated as fact without one)

- **CONFIRMED (code)** — verified by reading the current repository code in this audit.
- **CONFIRMED (run)** — reproduced by executing code/tests in this audit.
- **REPORTED** — found in an earlier audit in this project's history or in a document, but *not* re-verified in this pass.
- **UNVERIFIED** — a document claim or suspicion; no evidence found either way.
- **PROPOSED** — an idea from a document; never approved or implemented.

**Status values:** `Open` · `Approved` · `In progress` · `Blocked` · `Done (verified)` · `Proposed (not approved)`.
No item is `Approved` yet — see [CURRENT_TASK.md](CURRENT_TASK.md).

## Summary

| Priority | Count | IDs |
|---|---|---|
| P0 | 2 | VAL-001, VAL-002 |
| P1 | 10 | VAL-003 … VAL-012 |
| P2 | 8 | VAL-013 … VAL-020 |
| P3 | 6 | VAL-021 … VAL-026 |
| **Total** | **26** | |

---

## P0 — Blocks further work

### VAL-001 — Validation engine looks up units/leases/timelines without tenant filter
- **Priority:** P0 · **Status:** Done (verified) · **Component:** `app/validation.py`
- **Description:** `check_invoice_vacancy_overlap(session, invoice)` queries `Unit`, `UnitTimeline` and `Lease` by `unit_id` only (no `tenant_id`). `Unit.unit_id` is explicitly *not* globally unique (it is meant to repeat across tenants), so if two tenants both have e.g. `SHOP-001`, one tenant's invoice can be validated against the other tenant's vacancy/lease data and receive a wrong "OK TO PAY / DO NOT PAY". `validate_invoice` also calls `check_duplicate_invoice` (this one *is* tenant-filtered, but only `if invoice.tenant_id`). `calculate_vacancy_periods` (lines ~123, ~138) has the same unscoped `Unit` lookups.
- **Evidence:** CONFIRMED (code) — `app/validation.py` lines 234, 241–255, 257 (unscoped); 123, 138 (unscoped `Unit`). Contradicts [TENANT_ISOLATION_EXPLANATION.md](TENANT_ISOLATION_EXPLANATION.md) §3, which claims "every query filters by tenant_id". **Not confirmed:** whether any production tenants actually share unit IDs (data not inspected).
- **Recommended action:** Pass `tenant_id` into the validation helpers and filter every `Unit`/`Lease`/`UnitTimeline` lookup by it; add failing-first tests with two tenants sharing a `unit_id`. Do not change business rules. Decide whether to re-validate existing results afterward (needs approval).
- **Source:** [TENANT_ISOLATION_EXPLANATION.md](TENANT_ISOLATION_EXPLANATION.md), regression audit (this project).

### VAL-002 — CSV import passes invalid `errors='ignore'` to `pd.read_csv`
- **Priority:** P0 · **Status:** Open · **Component:** `main.py`
- **Description:** Four `pd.read_csv(..., encoding='utf-8', errors='ignore')` calls (units preview, units import, leases import, invoice processing). `read_csv` has no `errors` parameter (the correct one is `encoding_errors`), so CSV uploads raise `TypeError`. Excel paths use `read_excel` and are unaffected.
- **Evidence:** CONFIRMED (code) — `main.py` lines 1240, 1301, 1412, 1571. CONFIRMED (run) — `TypeError: read_csv() got an unexpected keyword argument 'errors'` reproduced with pandas 3.0.2 (local). **Unverified:** the pandas version running on Azure (`requirements.txt` only says `pandas>=2.0.0`) and whether a caller catches the error and falls back.
- **Recommended action:** Replace with `encoding_errors='ignore'` (or `'replace'`) at the four sites; add a regression test that uploads a CSV with a non-UTF-8 byte. Treat as a bug fix with its own approved task; re-run CSV workflow tests.
- **Source:** regression audit (this project).

---

## P1 — Needed for a trustworthy MVP

### VAL-003 — Tenant isolation verification (whole application)
- **Priority:** P1 · **Status:** Open · **Component:** all routes, `app/tenant_helpers.py`, tests
- **Description:** Docs repeatedly state isolation is "verified"/"production-ready". The only cross-tenant test (`test_multi_tenant_isolation`) just inserts two rows and counts them — it exercises no query path or endpoint, and it builds `Tenant(name=...)` without the required `slug` (`models.py:24` is `nullable=False`), so it likely cannot pass as written. VAL-001 shows isolation is *not* universal. A systematic review of every query/route and real two-tenant tests are needed before the claim can be made.
- **Evidence:** CONFIRMED (code) for the weak test and the VAL-001 gap; UNVERIFIED for all other routes. Positive evidence exists for manual-review routes (all `get_queue_item*` calls filter `tenant_id`) and PDF viewing (see Done items in [ROADMAP.md](ROADMAP.md)).
- **Recommended action:** Enumerate all `session.query(...)` / raw SQL sites; classify tenant-scoped vs not; write two-tenant endpoint tests for invoices list/detail/export, units, leases, mappings, manual review, patterns, upload status. Record results here.
- **Source:** [TENANT_ISOLATION_EXPLANATION.md](TENANT_ISOLATION_EXPLANATION.md), [PRODUCTION_READY_CHECKLIST.md](PRODUCTION_READY_CHECKLIST.md), [E2E_TESTING_GAP_ANALYSIS.md](E2E_TESTING_GAP_ANALYSIS.md) (item 12 "SECURITY CRITICAL").

### VAL-004 — Durable source-PDF reference for processed invoices
- **Priority:** P1 · **Status:** Open · **Component:** `app/models.py` (Invoice), upload pipeline, storage
- **Description:** `Invoice` has `tenant_id` and `source_batch` but **no** durable reference to its source PDF (no path/filename/blob key). Only `ManualReviewQueue` stores `pdf_path`/`original_filename`. Uploaded files are saved as `UPLOAD_DIR/<batch_id>_<filename>`, so a processed invoice cannot be traced back to or re-opened from its source document, and users cannot audit extraction. Also unknown whether `UPLOAD_DIR` on Azure App Service is persistent across restarts/redeploys/scale-out.
- **Evidence:** CONFIRMED (code) — `models.py` shows `pdf_path` only on `ManualReviewQueue` (line ~280); `Invoice` has none. UNVERIFIED — Azure storage durability.
- **Recommended action:** Design (needs approval; schema change) a tenant-owned document record (e.g., object storage such as Azure Blob + a `documents`/`source_document_id` reference), then a tenant-checked download route modelled on `/manual-review/{queue_id}/pdf`. **Do not** repurpose `/pdf-viewer` / `/pdf-content` (they now return 410). Requires migration plan and backfill decision.
- **Owner-approved wording:** "Processed invoice source-document persistence: Invoice currently has tenant_id and source_batch but no durable source PDF reference. If processed invoices need source-document viewing later, introduce a proper persistent document reference and tenant-owned authorization model." The `Invoice` schema must not change as part of the PDF-authorization task.
- **Source:** Requirement stated in the PDF-authorization task; docstring in `app/routes/pdf_viewer.py`.

### VAL-005 — CSV / Excel / PDF regression and end-to-end coverage
- **Priority:** P1 · **Status:** Open · **Component:** `tests/`
- **Description:** No automated test exercises the full upload → parse → map → validate → display path for any of CSV, Excel or PDF. Docs claim "13 E2E tests ready", "70% of critical gaps fixed", "ready for production"; the repository evidence does not support these (see VAL-009, VAL-017). PDF tests cannot run without live Azure Document Intelligence (not mocked).
- **Evidence:** CONFIRMED (code/run) — regression audit: e2e file uncollectable, Playwright browsers not installed, `TestClient` broken (VAL-009). Doc claims in [PRODUCTION_READY_CHECKLIST.md](PRODUCTION_READY_CHECKLIST.md) / [FINAL_STATUS_REPORT.md](FINAL_STATUS_REPORT.md) are UNVERIFIED and in part contradicted.
- **Recommended action:** After VAL-002 and VAL-009: build fixture-based tests against an isolated test DB (never live Supabase) for CSV, Excel, PDF (Azure client mocked with recorded responses). Add the PDF-to-validation golden path and a negative cross-tenant path.
- **Source:** [E2E_TESTING_GAP_ANALYSIS.md](E2E_TESTING_GAP_ANALYSIS.md), [TESTING_AUDIT_REPORT.md](TESTING_AUDIT_REPORT.md), regression audit.

### VAL-006 — Authentication and production security review
- **Priority:** P1 · **Status:** Open · **Component:** `main.py`, `app/auth.py`, Azure config
- **Description:** Session middleware is configured with only a secret key. No evidence of: `https_only`/`same_site` cookie settings, CSRF protection on state-changing POST routes, login/reset rate limiting, security headers, audit logging, or upload content checks beyond extension/size. [PROJECT_ANALYSIS_AND_NEXT_PHASE.md](PROJECT_ANALYSIS_AND_NEXT_PHASE.md) lists "Security Hardening" as future work, which is consistent.
- **Evidence:** CONFIRMED (code) — `main.py:76` `SessionMiddleware(secret_key=SECRET_KEY)`; no `csrf`/`slowapi`/rate-limit matches in `main.py` or `app/`. These are *absences found by search*; actual exploitability is UNVERIFIED (Azure may add controls).
- **Recommended action:** Read-only review first (checklist: cookie flags, CSRF, rate limits, password policy, reset-token expiry, email-verification enforcement, file upload handling, super-admin paths, error leakage). Produce findings, then create specific backlog items.
- **Source:** [PROJECT_ANALYSIS_AND_NEXT_PHASE.md](PROJECT_ANALYSIS_AND_NEXT_PHASE.md), [END_USER_ISSUES_AUDIT.md](END_USER_ISSUES_AUDIT.md).

### VAL-007 — PDF extraction reliability
- **Priority:** P1 · **Status:** Open · **Component:** `app/pdf_processor.py`, `app/pdf_normalizer.py`, `app/enhanced_pdf_processor.py`
- **Description:** Accuracy and reliability of Azure extraction → normalisation is not measured. Docs record British Gas normalisation returning an empty result and Opus values containing newlines. Opus newline cleaning now appears implemented (`_clean_text`, `pdf_normalizer.py:59`); British Gas status is unknown. The regression audit also found a unit test/behaviour mismatch for the normalizer. No supplier-level accuracy figures exist.
- **Evidence:** [FIXES_NEEDED.md](FIXES_NEEDED.md) (REPORTED, Jan 2026); CONFIRMED (code) for the newline fix only; British Gas fix UNVERIFIED; normalizer test mismatch REPORTED.
- **Recommended action:** Build a small labelled set of real supplier PDFs (kept out of git — `*.pdf` is ignored), record expected fields, measure per-field accuracy and confidence calibration, and fix the normalizer/test mismatch. Define what accuracy sends an invoice to manual review.
- **Source:** [FIXES_NEEDED.md](FIXES_NEEDED.md), [PDF_TESTING_RESULTS_ANALYSIS.md](PDF_TESTING_RESULTS_ANALYSIS.md), [ENHANCED_PDF_EXTRACTION.md](ENHANCED_PDF_EXTRACTION.md).

### VAL-008 — Line-item extraction accuracy
- **Priority:** P1 · **Status:** Open (scope to be confirmed) · **Component:** PDF pipeline, data model
- **Description:** Requirement raised by the product owner. No line-item support was found in the application: there is no line-item model, field, or extraction code. Current extraction covers header-level fields (account number, supplier, dates, amounts). It is undefined what "line items" must produce and how they feed validation.
- **Evidence:** CONFIRMED (code) — case-insensitive search for `line item/line_item/LineItem` in `app/` returned no matches. Requirements UNCONFIRMED.
- **Recommended action:** Needs a short requirements note first (which line-level fields, which suppliers, what validation uses them). Depends on VAL-007 baseline. Do not start until scoped.
- **Source:** Product-owner requirement for this documentation task.

### VAL-009 — Test harness is broken in the current environment
- **Priority:** P1 · **Status:** Open · **Component:** `tests/conftest.py`, `requirements.txt`
- **Description:** (a) `tests/conftest.py` `client` fixture uses `starlette.testclient.TestClient`, which fails with `Client.__init__() got an unexpected keyword argument 'app'` (Starlette 0.26.1 vs httpx 0.28.1) — any test using it errors. (b) `tests/unit/test_pdf_tenant_auth.py` passes when run alone but fails in a full-suite run (`Runner.run() cannot be called from a running event loop`, pytest-asyncio auto mode). (c) The `venv` interpreter points to a missing Python 3.11; the working environment is `venv_new` (Python 3.14.5).
- **Evidence:** CONFIRMED (run) for (a) and (b) in the earlier regression audit; (c) CONFIRMED (run) in this audit (`venv\Scripts\python.exe` → "No Python at …Python311"). Isolated run of the two PDF test files today: 27 passed, 1 skipped.
- **Recommended action:** Choose one approach: pin `httpx<0.28` *or* move to `httpx.ASGITransport` in the fixture; fix event-loop scope/ordering for the async tests; document the one supported interpreter. Test-infrastructure change only.
- **Source:** regression audit (this project).

### VAL-010 — CI/CD deploys without running tests
- **Priority:** P1 · **Status:** Open · **Component:** `.github/workflows/main_valix.yml`
- **Description:** The GitHub → Azure workflow builds and deploys; no `pytest` step was found, so a failing or insecure change can reach production.
- **Evidence:** CONFIRMED (code) — no `pytest`/test step in the workflow file (search). Depends on VAL-009 to make a test gate meaningful.
- **Recommended action:** After VAL-009, add a test job gating deploy (unit tests only, no live DB/Azure). Deployment config change — needs explicit approval.
- **Source:** CI setup earlier in this project.

### VAL-011 — Azure Document Intelligence key rotation / secrets hygiene
- **Priority:** P1 · **Status:** Open (unverified) · **Component:** Azure config, secrets
- **Description:** Earlier credential work rotated database, email and session secrets; Azure Document Intelligence API key rotation was noted as outstanding. Cannot be verified from the repository. Documents contain no real secrets (scan: only placeholders), but ~8 deployment/Supabase docs expose the Supabase project host name.
- **Evidence:** REPORTED (earlier session) for the pending rotation; CONFIRMED (run) for the doc scan (regex scan of all 217 `.md` files, no live credentials found).
- **Recommended action:** Owner to confirm rotation status in Azure Portal; if the key ever appeared in git history, rotate and record. Decide whether to scrub project identifiers from docs (part of VAL-019).
- **Source:** earlier credential-sanitisation work; doc scan in this audit.

### VAL-012 — Manual review item page returns a dict instead of a template
- **Priority:** P1 · **Status:** Open · **Component:** `app/routes/manual_review.py`
- **Description:** `GET /manual-review/{queue_id}` ends with `return { "request": request, "queue_item": ..., ... }` instead of a `TemplateResponse`. FastAPI will try to JSON-encode the `Request` and ORM objects, so the review UI page cannot render as intended. The manual-review list and the PDF route are separate and unaffected.
- **Evidence:** CONFIRMED (code) — `manual_review.py` lines ~100–141. Runtime failure REPORTED by regression audit; not re-run here.
- **Recommended action:** Render the existing review template with `templates.TemplateResponse`, add a test; verify the template exists first.
- **Source:** regression audit.

---

## P2 — Hardening and hygiene

### VAL-013 — `account_mapping.py` calls `.replace()` on SQLAlchemy columns
- **Priority:** P2 · **Status:** Open · **Component:** `app/account_mapping.py`
- **Description:** Lines 62 and 132 do `InvoiceUnitMapping.supplier_account_number.replace(" ", "").replace("-", "")` on a column attribute, which is not a SQL expression; the lookup will fail or misbehave when reached. Line 25 (a plain string) is fine.
- **Evidence:** CONFIRMED (code). Runtime effect REPORTED, not re-run. May affect PDF → unit mapping (links to VAL-007).
- **Recommended action:** Use SQL functions (`func.replace(...)`) or normalise at write time; add tests for account numbers with spaces/hyphens.
- **Source:** regression audit; [INVOICE_UNIT_MAPPING_STRATEGY.md](INVOICE_UNIT_MAPPING_STRATEGY.md).

### VAL-014 — `logger` used before it is defined at import time
- **Priority:** P2 · **Status:** Open · **Component:** `main.py`
- **Description:** In the optional-import fallback (`except ImportError`, line 51) `logger.warning(...)` runs before `logger` is created (line 66), so if the Azure packages are missing the app dies with `NameError` instead of degrading gracefully. Latent in production because the packages are in `requirements.txt`.
- **Evidence:** CONFIRMED (code) — `main.py` lines 44–66.
- **Recommended action:** Define `logger` before the optional import block.
- **Source:** earlier regression audit.

### VAL-015 — Database-level tenant constraints not declared; RLS unused by the app
- **Priority:** P2 · **Status:** Open · **Component:** `app/models.py`, `migrations/`, Supabase
- **Description:** `Unit` has a comment promising `UNIQUE(tenant_id, unit_id)` but `__table_args__` declares none (only `sqlite_autoincrement`); [TENANT_ISOLATION_EXPLANATION.md](TENANT_ISOLATION_EXPLANATION.md) also claims composite foreign keys that are not declared. The RLS policies in `migrations/add_enhanced_pdf_extraction_tables.sql` use `current_setting('app.current_tenant_id')`, but nothing in the app sets that setting, so (if applied, and if the app role is subject to RLS) the policies would either error or be bypassed. Whether the Supabase DB actually has these constraints/policies is unknown.
- **Evidence:** CONFIRMED (code) for the missing declarations and for no `set_config`/`app.current_tenant_id` use in `main.py`, `app/`, `scripts/`. UNVERIFIED — actual production schema.
- **Recommended action:** Inspect production schema read-only; decide on constraints/RLS strategy; any change needs a migration plan and approval.
- **Source:** [PHASE_2_IMPLEMENTATION_SUMMARY.md](PHASE_2_IMPLEMENTATION_SUMMARY.md), [TENANT_ISOLATION_EXPLANATION.md](TENANT_ISOLATION_EXPLANATION.md).

### VAL-016 — No monitoring / error tracking
- **Priority:** P2 · **Status:** Open · **Component:** deployment
- **Description:** Docs list Sentry / uptime / APM as outstanding. No monitoring SDK is present in code or `requirements.txt`. Azure-platform logging may exist outside the repo.
- **Evidence:** CONFIRMED (code) — no `sentry`/`applicationinsights` matches in `main.py`, `app/`, `requirements.txt`. Azure-side monitoring UNVERIFIED.
- **Recommended action:** Decide tool (Azure Application Insights is the natural fit); define alerts for 5xx, login failures, extraction failures.
- **Source:** [PRE_PHASE_2_ASSESSMENT.md](PRE_PHASE_2_ASSESSMENT.md), [PROJECT_ANALYSIS_AND_NEXT_PHASE.md](PROJECT_ANALYSIS_AND_NEXT_PHASE.md).

### VAL-017 — E2E tests unusable (syntax error, no browsers installed)
- **Priority:** P2 · **Status:** Open · **Component:** `tests/e2e/`
- **Description:** `tests/e2e/test_user_workflow.py` fails collection (a JS regex literal inside Python, ~line 74); Playwright browsers are not installed in the working environment; docs claim "13 E2E tests ready".
- **Evidence:** REPORTED (regression audit, CONFIRMED (run) then). Not re-run in this pass.
- **Recommended action:** Repair after VAL-009; decide if Playwright E2E is in scope for MVP or deferred.
- **Source:** regression audit; [E2E_TESTING_RECOMMENDATIONS.md](E2E_TESTING_RECOMMENDATIONS.md).

### VAL-018 — Dependency and runtime hygiene
- **Priority:** P2 · **Status:** Open · **Component:** `requirements.txt`, environments
- **Description:** Core stack is pinned to old versions (`fastapi==0.95.1`, `starlette==0.26.1`, `jinja2==3.0.3`, `pydantic<2`) while most others are floating `>=` — resolution drifts over time (VAL-002 and VAL-009 are symptoms). Test libraries share the production requirements file. Python runtime on Azure vs local 3.14.5 not confirmed.
- **Evidence:** CONFIRMED (code) — `requirements.txt`. Azure runtime version UNVERIFIED. [README.md](README.md)/[TROUBLESHOOTING.md](TROUBLESHOOTING.md) explain the pins (template rendering error with newer versions — REPORTED).
- **Recommended action:** Freeze a lockfile from the known-good environment; split `requirements-dev.txt`; plan upgrade as its own task. No change without approval.
- **Source:** [README.md](README.md), [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

### VAL-019 — Documentation consolidation (217 Markdown files)
- **Priority:** P2 · **Status:** Open · **Component:** repository root
- **Description:** 217 Markdown files (209 in the repo root, 8 in `migrations/`, `test_data/`, `test_pdfs/`, `tests/fixtures/`). Many are one-off troubleshooting notes, superseded provider guides (SendGrid → Resend), duplicated status reports, and unverifiable "100% complete" claims. `README.md` is stale (SQLite, "Phase 5: PDF ingestion" as future, no auth/multi-tenant). See the Phase 3 proposal in [ROADMAP.md](ROADMAP.md#documentation-structure-proposal).
- **Evidence:** CONFIRMED (run) — inventory and rule-based categorisation in this audit (only ~25 files were read in full; the rest were categorised by title).
- **Recommended action:** Owner approval of archive/consolidation plan; then move (not delete) obsolete docs under `docs/archive/`, rewrite `README.md`. Nothing has been moved or edited.
- **Source:** this audit.

### VAL-020 — Mapping template header casing mismatch
- **Priority:** P2 · **Status:** Open (details unverified) · **Component:** `static/templates/*.xlsx`, column mapping
- **Description:** Regression audit noted a header-casing mismatch between a downloadable mapping template and the mapper's expectations. Not re-verified in this pass.
- **Evidence:** REPORTED.
- **Recommended action:** Re-verify first; if confirmed, make header matching case-insensitive (see `map_columns`) and add a test.
- **Source:** regression audit; [COLUMN_MAPPING_EXPLANATION.md](COLUMN_MAPPING_EXPLANATION.md).

---

## P3 — Cleanup, decisions, proposals

### VAL-021 — Remove dead PDF-viewing remnants
- **Priority:** P3 · **Status:** Open · **Component:** `templates/unmapped_invoices.html`, `app/routes/unmapped_invoices.py`, `app/routes/pdf_viewer.py`, `app/routes/manual_review.py`
- **Description:** `unmapped_invoices.html:90` still links to `/pdf-viewer?path=…` (now returns 410); `templates/pdf_viewer.html` is unused; `UNMAPPED_QUEUE` is an in-memory list whose `add_to_unmapped_queue` is never called; `manual_review.py` keeps an unused `import os`.
- **Evidence:** CONFIRMED (code). The page is dormant (queue always empty), so no user-visible failure today.
- **Recommended action:** Remove after confirming the unmapped-invoices page is not planned. Never let this block P0/P1.
- **Source:** PDF-authorization task; regression audit.

### VAL-022 — Super-admin cannot view manual-review PDFs (product decision)
- **Priority:** P3 · **Status:** Open (decision needed) · **Component:** `app/routes/manual_review.py`
- **Description:** `get_queue_item` filters `tenant_id == current_user.tenant_id`; super admins have `tenant_id=None`, so the PDF route returns 404 for them. This is fail-closed (safe) but may not be the desired support workflow.
- **Evidence:** CONFIRMED (code) by reading `get_queue_item`; runtime not exercised.
- **Recommended action:** Owner decides whether super admins need cross-tenant support access (with audit logging).
- **Source:** this audit.

### VAL-023 — Reconcile end-user UX audit items
- **Priority:** P3 · **Status:** Open · **Component:** templates, `main.py`
- **Description:** [END_USER_ISSUES_AUDIT.md](END_USER_ISSUES_AUDIT.md) lists 18 UX issues (loading states, password-strength meter, delete confirmations, session-expiry messaging, etc.) and marks them all as the "recommended fix order"; completion is not recorded. Issue #1 (401 → login redirect) **is implemented** (`main.py:137–149`, includes expiry message). The remaining 17 are UNVERIFIED.
- **Evidence:** CONFIRMED (code) for #1 only.
- **Recommended action:** Spot-check each in the UI and close or re-file as individual items.
- **Source:** [END_USER_ISSUES_AUDIT.md](END_USER_ISSUES_AUDIT.md), [UX_FIXES_COMPLETE.md](UX_FIXES_COMPLETE.md).

### VAL-024 — Stripe subscriptions and usage limits
- **Priority:** P3 · **Status:** Proposed (not approved) · **Component:** new
- **Description:** Proposed in [PROJECT_ANALYSIS_AND_NEXT_PHASE.md](PROJECT_ANALYSIS_AND_NEXT_PHASE.md) and [STRIPE_INTEGRATION_GUIDE.md](STRIPE_INTEGRATION_GUIDE.md) (example tiers £49/£149/custom). No Stripe code or dependency exists.
- **Evidence:** CONFIRMED (code) — no matches in code or `requirements.txt`; pricing is a document suggestion, not a decision.
- **Recommended action:** Revisit only after P0–P1 and a go-to-market decision.
- **Source:** the two docs above.

### VAL-025 — Horizon PMS integration
- **Priority:** P3 · **Status:** Proposed (not approved) · **Component:** `app/horizon_connector.py`
- **Description:** A connector module exists (scaffold) but the docs say integration is waiting on API access. No evidence of a working sync.
- **Evidence:** CONFIRMED (code) the file exists; behaviour UNVERIFIED.
- **Recommended action:** Park until API access is confirmed.
- **Source:** [HORIZON_INTEGRATION_GUIDE.md](HORIZON_INTEGRATION_GUIDE.md), [HORIZON_INTEGRATION_EXPLANATION.md](HORIZON_INTEGRATION_EXPLANATION.md).

### VAL-026 — Other never-implemented proposals
- **Priority:** P3 · **Status:** Proposed (not approved) · **Component:** various
- **Description:** Validation-completion/summary emails, advanced reporting and PDF export, Redis caching, Celery job queue, multi-region, AI explanations ("Phase 3" in README), dark mode, onboarding tour, bulk validation, search autocomplete, keyboard shortcuts.
- **Evidence:** PROPOSED in [PROJECT_ANALYSIS_AND_NEXT_PHASE.md](PROJECT_ANALYSIS_AND_NEXT_PHASE.md), [README.md](README.md), [END_USER_ISSUES_AUDIT.md](END_USER_ISSUES_AUDIT.md); not searched individually.
- **Recommended action:** Keep as a parking lot; promote individual items only with an owner request.
- **Source:** documents above.

---

## Done and verified (reference only)

Completed work is tracked with evidence in [ROADMAP.md](ROADMAP.md#completed-features-and-evidence) — not duplicated here.
