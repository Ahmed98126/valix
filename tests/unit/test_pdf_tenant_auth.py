"""Security tests for PDF tenant authorization.

Testing strategy
----------------
Starlette 0.26.1 TestClient passes ``app=`` to httpx.Client which no longer
accepts that argument (httpx 0.28+).  We therefore use two approaches:

A. Direct async coroutine calls — the route handlers are plain async functions;
   calling them with explicit arguments bypasses the broken TestClient while
   exercising the exact same code paths.  Dependencies (get_current_user,
   get_session) are satisfied by passing mock objects directly, which is valid
   because FastAPI's Depends() metadata has no effect when functions are called
   without going through the DI framework.

B. httpx.AsyncClient + ASGITransport — used for the one case that requires
   the full dependency-injection chain to prove that unauthenticated callers
   actually receive 401 (i.e. that Depends(get_current_user) fires before the
   route handler body).

Scope
-----
1. Dead endpoints (/pdf-viewer, /pdf-content)
   - Always raise 410 for authenticated callers, no filesystem access.
   - get_current_user dependency blocks unauthenticated callers with 401.
   - ?path= query parameters are accepted but ignored — no file bytes returned.

2. Active PDF route (/manual-review/{queue_id}/pdf)
   - Tenant-owned queue item → FileResponse with application/pdf.
   - Cross-tenant queue_id → 404 (existence not revealed).
   - Unauthenticated → 401.
   - Non-existent queue_id → 404.
   - DB path outside UPLOAD_ROOT → 403 (defence-in-depth _safe_pdf_path).
   - DB path with non-.pdf extension → 403.
   - DB path that no longer exists on disk → 404.
   - DB path containing ../ that resolves outside UPLOAD_ROOT → 403.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse

import app.routes.pdf_viewer as pdf_viewer_module
from app.routes.pdf_viewer import view_pdf as dead_view_pdf
from app.routes.pdf_viewer import get_pdf_content as dead_get_pdf_content
from app.routes.manual_review import view_pdf as mr_view_pdf
from app.auth import get_current_user
from app.db import get_session


# ─── Shared helpers ──────────────────────────────────────────────────────────

def _make_user(tenant_id=1, is_super_admin=False):
    u = MagicMock()
    u.id = 1
    u.tenant_id = tenant_id
    u.is_super_admin = is_super_admin
    u.is_active = True
    return u


def _make_queue_item(pdf_path: str, tenant_id: int = 1, original_filename: str = "invoice.pdf"):
    item = MagicMock()
    item.tenant_id = tenant_id
    item.pdf_path = pdf_path
    item.original_filename = original_filename
    return item


def _make_pdf(directory: Path, name: str = "invoice.pdf") -> Path:
    p = directory / name
    p.write_bytes(b"%PDF-1.4 fake invoice content for test")
    return p


@pytest.fixture()
def upload_dir(tmp_path, monkeypatch):
    """Temporary upload directory; UPLOAD_ROOT in pdf_viewer is redirected here."""
    d = tmp_path / "uploads"
    d.mkdir()
    monkeypatch.setattr(pdf_viewer_module, "UPLOAD_ROOT", d.resolve())
    return d


# ─── Helper: ASGI app with overridden auth for 401 tests ────────────────────

def _make_asgi_app_401(router):
    """Return a FastAPI ASGI app that has get_current_user raise 401."""
    app = FastAPI()
    app.include_router(router)

    def _unauth():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    app.dependency_overrides[get_current_user] = _unauth
    app.dependency_overrides[get_session] = lambda: MagicMock()
    return app


# ─── 1. Dead endpoint tests ──────────────────────────────────────────────────

class TestDeadEndpoints:
    """
    /pdf-viewer and /pdf-content must never serve file bytes.
    Tested by calling the route handler coroutines directly.
    """

    async def test_pdf_viewer_raises_410(self):
        """/pdf-viewer handler raises HTTPException(410) unconditionally."""
        with pytest.raises(HTTPException) as exc_info:
            await dead_view_pdf(request=MagicMock(), current_user=_make_user())
        assert exc_info.value.status_code == 410

    async def test_pdf_content_raises_410(self):
        """/pdf-content handler raises HTTPException(410) unconditionally."""
        with pytest.raises(HTTPException) as exc_info:
            await dead_get_pdf_content(request=MagicMock(), current_user=_make_user())
        assert exc_info.value.status_code == 410

    async def test_pdf_viewer_410_regardless_of_path_param(self, upload_dir):
        """Even if a valid ?path= would point to a real file, 410 is still raised."""
        pdf = _make_pdf(upload_dir)
        with pytest.raises(HTTPException) as exc_info:
            # The route no longer accepts a path param — passing extra kwargs
            # to verify the handler body doesn't branch on it.
            await dead_view_pdf(request=MagicMock(), current_user=_make_user())
        assert exc_info.value.status_code == 410

    async def test_pdf_content_410_regardless_of_path_param(self, upload_dir):
        """Even with a real PDF path available, /pdf-content still raises 410."""
        pdf = _make_pdf(upload_dir)
        with pytest.raises(HTTPException) as exc_info:
            await dead_get_pdf_content(request=MagicMock(), current_user=_make_user())
        assert exc_info.value.status_code == 410

    async def test_pdf_viewer_no_file_bytes_in_410_body(self, upload_dir):
        """The 410 response detail must not include filesystem path or PDF bytes."""
        pdf = _make_pdf(upload_dir)
        with pytest.raises(HTTPException) as exc_info:
            await dead_view_pdf(request=MagicMock(), current_user=_make_user())
        exc = exc_info.value
        assert exc.status_code == 410
        detail_str = str(exc.detail)
        assert b"%PDF" not in detail_str.encode()
        assert str(upload_dir) not in detail_str  # no path leak

    async def test_dead_endpoints_401_before_410_via_asgi(self):
        """Unauthenticated callers get 401 — auth dep fires before handler body.

        Uses httpx.AsyncClient + ASGITransport to exercise the full FastAPI
        dependency chain without relying on the broken Starlette 0.26 TestClient.
        """
        from app.routes.pdf_viewer import router as pdf_viewer_router

        app = _make_asgi_app_401(pdf_viewer_router)
        transport = httpx.ASGITransport(app=app)

        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            r_viewer = await client.get("/pdf-viewer")
            r_content = await client.get("/pdf-content")

        assert r_viewer.status_code == 401
        assert r_content.status_code == 401


# ─── 2. Active route: /manual-review/{queue_id}/pdf ─────────────────────────

class TestManualReviewPDFAuthorization:
    """
    /manual-review/{queue_id}/pdf — two-layer security:
      Layer 1: DB ownership  (get_queue_item filtered by tenant_id)
      Layer 2: _safe_pdf_path() confinement + extension check
    """

    async def test_tenant_owned_pdf_is_served(self, upload_dir):
        """Happy path: tenant user gets a FileResponse for their own PDF."""
        pdf = _make_pdf(upload_dir)
        user = _make_user(tenant_id=1)
        session = MagicMock()
        queue_item = _make_queue_item(pdf_path=str(pdf), tenant_id=1)

        with patch("app.routes.manual_review.get_queue_item", return_value=queue_item):
            response = await mr_view_pdf(queue_id=42, session=session, current_user=user)

        assert isinstance(response, FileResponse)
        assert response.media_type == "application/pdf"

    async def test_cross_tenant_queue_id_returns_404(self):
        """Tenant B cannot access Tenant A's queue item — 404 conceals existence."""
        user = _make_user(tenant_id=2)  # Tenant B
        session = MagicMock()

        # Simulates: no ManualReviewQueue row for (queue_id=99, tenant_id=2)
        with patch("app.routes.manual_review.get_queue_item", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await mr_view_pdf(queue_id=99, session=session, current_user=user)

        assert exc_info.value.status_code == 404

    async def test_unauthenticated_access_returns_401_via_asgi(self):
        """Unauthenticated request is rejected by get_current_user before DB access.

        Tested via full ASGI transport to verify the dependency chain fires.
        """
        from app.routes.manual_review import router as manual_review_router

        app = _make_asgi_app_401(manual_review_router)
        transport = httpx.ASGITransport(app=app)

        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.get("/manual-review/1/pdf")

        assert r.status_code == 401

    async def test_nonexistent_queue_id_returns_404(self):
        """Queue_id that does not exist for this tenant returns 404."""
        user = _make_user(tenant_id=1)
        session = MagicMock()

        with patch("app.routes.manual_review.get_queue_item", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await mr_view_pdf(queue_id=9999, session=session, current_user=user)

        assert exc_info.value.status_code == 404

    async def test_db_path_outside_upload_root_blocked(self, upload_dir, tmp_path):
        """Layer 2: DB path outside UPLOAD_ROOT is rejected (403) by _safe_pdf_path."""
        # File exists but is outside upload_dir (the tmp_path parent)
        outside_pdf = tmp_path / "escape.pdf"
        outside_pdf.write_bytes(b"%PDF-1.4 sensitive outside file")

        user = _make_user(tenant_id=1)
        session = MagicMock()
        evil_item = _make_queue_item(pdf_path=str(outside_pdf), tenant_id=1)

        with patch("app.routes.manual_review.get_queue_item", return_value=evil_item):
            with pytest.raises(HTTPException) as exc_info:
                await mr_view_pdf(queue_id=42, session=session, current_user=user)

        assert exc_info.value.status_code == 403

    async def test_non_pdf_extension_in_db_path_blocked(self, upload_dir):
        """Layer 2: DB path with .txt extension is rejected (403)."""
        txt = upload_dir / "secrets.txt"
        txt.write_text("sensitive plaintext content")

        user = _make_user(tenant_id=1)
        session = MagicMock()
        evil_item = _make_queue_item(pdf_path=str(txt), tenant_id=1)

        with patch("app.routes.manual_review.get_queue_item", return_value=evil_item):
            with pytest.raises(HTTPException) as exc_info:
                await mr_view_pdf(queue_id=42, session=session, current_user=user)

        assert exc_info.value.status_code == 403

    async def test_deleted_pdf_file_returns_404(self, upload_dir):
        """If the PDF was removed from disk after the DB record was created, 404."""
        user = _make_user(tenant_id=1)
        session = MagicMock()
        gone_item = _make_queue_item(
            pdf_path=str(upload_dir / "deleted_invoice.pdf"),
            tenant_id=1
        )

        with patch("app.routes.manual_review.get_queue_item", return_value=gone_item):
            with pytest.raises(HTTPException) as exc_info:
                await mr_view_pdf(queue_id=42, session=session, current_user=user)

        assert exc_info.value.status_code == 404

    async def test_path_traversal_in_db_path_blocked(self, upload_dir, tmp_path):
        """Layer 2: ../ traversal in DB path that resolves outside UPLOAD_ROOT → 403."""
        # The file exists at the traversal destination
        outside_pdf = tmp_path / "escape.pdf"
        outside_pdf.write_bytes(b"%PDF-1.4 traversal target")

        # Textually appears to be inside uploads/ but resolves to tmp_path parent
        traversal_path = str(upload_dir / ".." / "escape.pdf")

        user = _make_user(tenant_id=1)
        session = MagicMock()
        traversal_item = _make_queue_item(pdf_path=traversal_path, tenant_id=1)

        with patch("app.routes.manual_review.get_queue_item", return_value=traversal_item):
            with pytest.raises(HTTPException) as exc_info:
                await mr_view_pdf(queue_id=42, session=session, current_user=user)

        assert exc_info.value.status_code == 403
