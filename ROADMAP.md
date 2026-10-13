# Valix — Roadmap

> Management document. Not a replacement for detailed docs. Companion files: [BACKLOG.md](BACKLOG.md), [CURRENT_TASK.md](CURRENT_TASK.md).
> Last reconciled: 2026-10-13 (documentation audit). Items are labelled **Confirmed**, **Assumed** or **Proposed**; evidence labels are defined in [BACKLOG.md](BACKLOG.md).

## 1. Objective

Valix is a multi-tenant SaaS that validates utility/supplier invoices for commercial property portfolios. It ingests invoices (CSV, Excel, PDF via Azure Document Intelligence), maps them to units and leases, checks duplicates and vacancy overlap, and produces a payment determination (e.g. OK TO PAY / DO NOT PAY / COT). Each client organisation (tenant) sees only its own data.

- Source: [README.md](README.md) (original description), [MVP_DEVELOPMENT_PLAN.md](MVP_DEVELOPMENT_PLAN.md) (goals), product-owner instructions in this project.
- Stack (Confirmed from code/config): FastAPI, SQLAlchemy, Supabase Postgres (`postgresql+psycopg2`), Azure App Service, Azure Document Intelligence, Resend email, GitHub → Azure CI/CD.

## 2. MVP scope

There is **no single owner-approved MVP definition** in the repository; many documents each claim a different completion percentage (90%, 95%, "100% complete"). The scope below is derived and needs owner confirmation (see [CURRENT_TASK.md](CURRENT_TASK.md) open questions).

| Capability | Status of scope | Notes |
|---|---|---|
| Multi-tenant accounts, login, email verification, password reset | **Confirmed** (built, in production use per owner) | |
| Units / leases import (Excel/CSV), per-tenant column mapping | **Confirmed** | CSV path currently broken — VAL-002 |
| Invoice upload (CSV/Excel) → validation → dashboard/export | **Confirmed** | |
| Invoice upload (PDF) → extraction → mapping → validation | **Confirmed** | Reliability unmeasured — VAL-007 |
| Manual review queue for low-confidence PDFs, with PDF viewing | **Confirmed** | |
| Strict tenant isolation | **Confirmed requirement**; implementation **incomplete** | VAL-001, VAL-003 |
| Source-document traceability for processed invoices | **Confirmed requirement** (owner) | VAL-004 |
| Line-item extraction | **Requirement raised**, scope **undefined** | VAL-008 |
| Stripe billing, Horizon sync, advanced reporting, notifications | **Proposed** — not approved | VAL-024 – VAL-026 |
| Monitoring / production hardening | **Assumed** needed before onboarding paying clients | VAL-006, VAL-016 |

## 3. Current phase

**Phase 2 — Security & correctness stabilisation** (owner-defined roadmap). Still open in this phase:

1. Commit and push the pending PDF security work (see §5; owner action).
2. Fix confirmed P0 defects (VAL-001 tenant scoping in validation, VAL-002 CSV import).
3. Make the test suite trustworthy (VAL-009) so later work can be verified.

No development task is currently approved — see [CURRENT_TASK.md](CURRENT_TASK.md).

## 4. Milestones

Phases 0–1 reflect work done in earlier sessions. Phases 3+ are **Proposed** sequencing, not commitments.

| # | Milestone | Status | Exit criteria |
|---|---|---|---|
| 0 | Repo baseline, credential sanitisation, secret rotation (DB/session/email) | Done (reported; see §5) | Baseline commit `153c8db`; secrets out of git |
| 1 | Infrastructure: Resend email, BASE_URL fix, psycopg2 dialect, GitHub→Azure CI/CD | Done (reported; commits listed in §5) | Production email verification worked (owner-reported) |
| 2 | **Security & correctness stabilisation** | **In progress** | PDF path/tenant security committed & pushed; VAL-001, VAL-002 fixed with tests; VAL-003 verification report; VAL-009 harness repaired |
| 3 | Regression baseline | Proposed | VAL-005 automated CSV/Excel/PDF + cross-tenant tests green in CI (VAL-010) |
| 4 | PDF quality & traceability | Proposed | VAL-007 accuracy baseline; VAL-004 durable source-PDF reference; VAL-008 scoped/built; VAL-012, VAL-013 fixed |
| 5 | Production hardening | Proposed | VAL-006 review actioned; VAL-011, VAL-015, VAL-016, VAL-018 resolved |
| 6 | Commercial features | Proposed (not approved) | VAL-024 (Stripe), VAL-025 (Horizon), VAL-026 |

## 5. Completed features and evidence

"Done" means evidence exists *in the repository or reproducible now*. Owner-reported items from earlier sessions are marked as such because the repository cannot prove them.

| Feature | Evidence | Caveat |
|---|---|---|
| Multi-tenant schema (`tenant_id` on Unit, Lease, Invoice, UnitTimeline, InvoiceValidation, InvoiceUnitMapping, ManualReviewQueue) | `app/models.py` | Isolation in queries is **incomplete** — VAL-001/003; DB constraints undeclared — VAL-015 |
| Session auth with 401 → login redirect incl. expiry message | `main.py:137–149` | Cookie/CSRF/rate-limit hardening not present — VAL-006 |
| DB pool exhaustion fix ([CRITICAL_DATABASE_FIX.md](CRITICAL_DATABASE_FIX.md)) | `app/db.py:30–34` (`pool_size=3, max_overflow=7, pool_recycle=1800, pool_timeout=30`) match the doc; background tasks use `SessionLocal()` (`main.py:222, 1539, 1886`) | Production behaviour not re-observed |
| Resend email (SendGrid removed from code) | `requirements.txt` has `resend`; no SendGrid references in `main.py`/`app/` | Production delivery owner-reported |
| `postgresql+psycopg2` dialect forced | commit `7061d51` | |
| GitHub → Azure deployment pipeline | `.github/workflows/main_valix.yml`, commit `a8dbd4d` | Runs no tests — VAL-010 |
| Email provider switch, BASE_URL fix | commits `b9b706a`, `e2f1452` | |
| **PDF path-traversal fix** (`_safe_pdf_path`: resolve, confine to `UPLOAD_ROOT`, `.pdf` only) | commit `732f64b`; `tests/unit/test_pdf_path_traversal.py` (13 pass, 1 symlink test skipped on Windows) | **Commit made locally; push to GitHub not completed** — owner must push |
| **Dead PDF endpoints disabled**: `/pdf-viewer` and `/pdf-content` return HTTP 410 (still require login → 401 when anonymous) | `app/routes/pdf_viewer.py:107–130`; `tests/unit/test_pdf_tenant_auth.py` (`TestDeadEndpoints`) | **Uncommitted** working-tree change |
| **Manual-review PDF route hardened**: tenant ownership lookup (404 on mismatch) + `_safe_pdf_path()` defence-in-depth | `app/routes/manual_review.py:237–272`; `TestManualReviewPDFAuthorization` | **Uncommitted**; super admins get 404 (VAL-022) |
| PDF security test result | Re-run 2026-10-13 (isolated): `tests/unit/test_pdf_path_traversal.py` + `tests/unit/test_pdf_tenant_auth.py` → **27 passed, 1 skipped** | Holds **only when run in isolation**; `test_pdf_tenant_auth.py` fails in a full-suite run (event-loop conflict) — VAL-009 |
| No frontend dependency on removed endpoints | Search of `templates/`, `static/`, `main.py`, `app/`: only the dormant link in `templates/unmapped_invoices.html:90` (page fed by an always-empty in-memory queue) | Cleanup — VAL-021 |
| PDF processing pipeline exists (Azure DI → normalizer → mapper → invoice/validation; low confidence → manual review) | `app/pdf_processor.py`, `app/pdf_normalizer.py`, `app/enhanced_pdf_processor.py`, `app/pdf_workflow.py`, `app/manual_review.py` | Accuracy unmeasured — VAL-007 |

**Not claimed as done** (docs say so, evidence does not support it): "multi-tenant isolation verified" ([PRODUCTION_READY_CHECKLIST.md](PRODUCTION_READY_CHECKLIST.md)), "all critical tests passing", "13 E2E tests ready", "Ready for production" ([FINAL_STATUS_REPORT.md](FINAL_STATUS_REPORT.md)), "Validation engine matches Databricks SQL exactly" ([MVP_STATUS_AND_ROADMAP.md](MVP_STATUS_AND_ROADMAP.md) — not compared in this audit).

## 6. Upcoming work (priority order)

Detail, evidence and status live in [BACKLOG.md](BACKLOG.md). Summary:

1. **P0:** VAL-001 tenant scoping in validation; VAL-002 CSV import bug.
2. **P1:** VAL-009 repair test harness → VAL-003 isolation verification → VAL-005 regression coverage → VAL-010 CI gate → VAL-012 manual-review page → VAL-004 source-PDF reference → VAL-007 PDF reliability → VAL-008 line items (after scoping) → VAL-006 security review → VAL-011 key rotation (owner).
3. **P2/P3:** see backlog.

## 7. Dependencies and blockers

- **Owner actions (blocking Phase 2 closure):** commit the uncommitted PDF security changes; `git push` commit `732f64b` (and later commits) from a terminal with GitHub credentials — the agent environment could not authenticate.
- VAL-005 and VAL-010 depend on VAL-009 (working test harness) and on a mocked Azure Document Intelligence client.
- VAL-004 depends on a storage decision (Azure Blob vs local disk) and a schema/migration approval.
- VAL-008 depends on VAL-007 baseline and a requirements note.
- VAL-024/025 depend on go-to-market decisions and Horizon API access (external).
- Environment: use the `venv_new` / Python 3.14.5 interpreter; `venv` is broken (VAL-009).

## 8. Documentation structure proposal

No document has been moved, edited or deleted. Counts are from a filename-based classification of all 217 files; ~25 key documents were read in full.

| Category | Files | Recommendation (needs approval) |
|---|---|---|
| Deployment / infra / DB connection | 46 | Keep one consolidated deployment/runbook doc; archive per-incident `FIX_*`/`URGENT_*`. Review for project identifiers (VAL-011/019). |
| Testing / QA | 40 | Keep one testing guide + `tests/fixtures/README.md`; archive the many "COMPLETE/FINAL/SUMMARY" duplicates. |
| Progress / status / completion reports | 34 | Archive all — superseded by this `ROADMAP.md`. Several claims are contradicted by code. |
| Email provider (SendGrid/SMTP) | 25 | Archive — SendGrid replaced by Resend. Write one short Resend/email note. |
| Plans / roadmaps / next-steps | 19 | Archive after the three management files are accepted; keep [MVP_DEVELOPMENT_PLAN.md](MVP_DEVELOPMENT_PLAN.md) as history. |
| Domain / DNS / www troubleshooting | 18 | Archive — one-off. Keep one "custom domain setup" summary. |
| Architecture / features / guides / README | 35 | **Retain** (after verification): [COLUMN_MAPPING_EXPLANATION.md](COLUMN_MAPPING_EXPLANATION.md), [INVOICE_UNIT_MAPPING_STRATEGY.md](INVOICE_UNIT_MAPPING_STRATEGY.md), [PDF_WORKFLOW_COMPLETE_GUIDE.md](PDF_WORKFLOW_COMPLETE_GUIDE.md), [ENHANCED_PDF_EXTRACTION.md](ENHANCED_PDF_EXTRACTION.md), [EXCEL_VS_PDF_WORKFLOW.md](EXCEL_VS_PDF_WORKFLOW.md), [PASSWORD_RESET_FLOW_EXPLAINED.md](PASSWORD_RESET_FLOW_EXPLAINED.md). **Correct before keeping:** [TENANT_ISOLATION_EXPLANATION.md](TENANT_ISOLATION_EXPLANATION.md) (contradicted by code — VAL-001/015), `README.md` (stale). |

Simpler target structure: root keeps `README.md`, `ROADMAP.md`, `BACKLOG.md`, `CURRENT_TASK.md`; `docs/` holds ~10–15 curated references (architecture, tenant model, PDF workflow, mapping, testing, deployment runbook); `docs/archive/` holds everything else (moved, not deleted, with git history preserved). Subfolder READMEs (`migrations/`, `test_data/`, `test_pdfs/`, `tests/fixtures/`) stay in place.

## 9. Known document conflicts (verified against code)

| Claim | Document | Finding |
|---|---|---|
| "Every query filters by `tenant_id`" | [TENANT_ISOLATION_EXPLANATION.md](TENANT_ISOLATION_EXPLANATION.md) | **False** — `app/validation.py` unscoped lookups (VAL-001) |
| `UNIQUE(tenant_id, unit_id)` and composite FKs | same | **Not declared** in `app/models.py` (VAL-015); production DB unverified |
| RLS policies enforce tenant isolation | [PHASE_2_IMPLEMENTATION_SUMMARY.md](PHASE_2_IMPLEMENTATION_SUMMARY.md) | Policies exist in SQL migration, but the app never sets `app.current_tenant_id` (VAL-015) |
| Email via SendGrid | [PROJECT_ANALYSIS_AND_NEXT_PHASE.md](PROJECT_ANALYSIS_AND_NEXT_PHASE.md), `SENDGRID_*` | **Obsolete** — Resend in code |
| Database is SQLite; no auth/multi-tenancy; PDF is "future" | [README.md](README.md) | **Stale** |
| "~95% complete", "ready for production", "not deployed yet (0%)" | MVP docs (inconsistent with each other) | Conflicting; superseded by this file |
| "Multi-tenant isolation verified"; tests passing | [PRODUCTION_READY_CHECKLIST.md](PRODUCTION_READY_CHECKLIST.md), [FINAL_STATUS_REPORT.md](FINAL_STATUS_REPORT.md) | Not supported (VAL-003, VAL-005, VAL-009) |
| Unauthenticated users get JSON instead of login redirect | [END_USER_ISSUES_AUDIT.md](END_USER_ISSUES_AUDIT.md) #1 | **Resolved** in `main.py:137–149` |
| Connection pool exhaustion | [CRITICAL_DATABASE_FIX.md](CRITICAL_DATABASE_FIX.md) | Code matches the described fix |
| Opus newline cleaning needed | [FIXES_NEEDED.md](FIXES_NEEDED.md) | Newline handling present (`pdf_normalizer.py:59`); British Gas fix unverified |

## 10. Permanent development rules

These apply to every future session (human or AI). Do not duplicate them in other planning files.

1. **Read first.** Before any development, read `ROADMAP.md`, `BACKLOG.md` and `CURRENT_TASK.md`.
2. **Only the approved task.** Work only on the task recorded in `CURRENT_TASK.md`. If it says "no task approved", do not develop — propose a task and wait.
3. **Log, don't fix, unrelated findings.** Add unrelated discoveries to `BACKLOG.md` (ID, priority, evidence label) instead of fixing them.
4. **Flag critical issues immediately.** Security or data-loss risks must be reported to the owner at once, even if out of scope — then logged as P0.
5. **No scope expansion.** No new features or behaviour changes beyond the approved task's scope; no unnecessary refactoring.
6. **Test before "done".** Run the tests relevant to the change (and say which, and which could not be run) before declaring completion. Never run tests against live Supabase.
7. **Update after verified completion.** Update status in `CURRENT_TASK.md`, `BACKLOG.md` and `ROADMAP.md` only once completion is verified with evidence.
8. **Recommend, don't start.** After finishing, recommend the next task; do not begin it without approval.
9. **Evidence for every claim.** Never state a feature works, or a bug exists, without evidence (code reference, test run, or reproduction). Label the rest UNVERIFIED.
10. **No new planning documents.** Information that belongs in the management files goes there; do not create further `*_STATUS.md` / `*_SUMMARY.md` / `NEXT_STEPS*.md` files.
11. **Approval gates.** Database schema changes, migrations, dependency changes, deployment/CI config changes, secret rotation, deleting or archiving documents, `git commit` and `git push` require explicit owner approval.
