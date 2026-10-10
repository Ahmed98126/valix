"""Security tests for the PDF path traversal fix in app/routes/pdf_viewer.py.

All tests exercise _safe_pdf_path() directly using a temporary directory as the
upload root. No live database, Supabase, or network calls are made.

Attack vectors covered
----------------------
* Legitimate access                  — must succeed (200-level)
* Absolute path outside upload root  — 403
* Relative traversal (../)           — 403
* .env access via traversal          — 403
* Symlink escape (if OS supports it) — 403
* Non-PDF extension inside root      — 403
* Missing file inside root           — 404
* Directory path instead of file     — 404
* .PDF uppercase extension           — must succeed (case-insensitive)
"""

import pytest
import sys
import os
from pathlib import Path
from fastapi import HTTPException

import app.routes.pdf_viewer as pdf_viewer_module


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def fake_upload_root(tmp_path, monkeypatch):
    """Create a temporary upload directory and point UPLOAD_ROOT at it.

    Using a *subdirectory* of tmp_path means the test can place files in
    ``tmp_path`` (the parent) that are genuinely outside UPLOAD_ROOT without
    any path arithmetic.
    """
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    monkeypatch.setattr(pdf_viewer_module, "UPLOAD_ROOT", upload_dir.resolve())
    return upload_dir  # the "safe" directory


def _make_pdf(directory: Path, name: str = "invoice.pdf") -> Path:
    """Write a minimal fake PDF into *directory* and return its path."""
    p = directory / name
    p.write_bytes(b"%PDF-1.4 fake content for test")
    return p


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------

class TestSafePdfPath:

    # ------------------------------------------------------------------
    # Legitimate access
    # ------------------------------------------------------------------

    def test_legitimate_pdf_is_accepted(self, fake_upload_root):
        """A real .pdf file directly inside UPLOAD_ROOT must be returned."""
        pdf = _make_pdf(fake_upload_root)
        result = pdf_viewer_module._safe_pdf_path(str(pdf))
        assert result == pdf.resolve()

    def test_pdf_in_subdirectory_accepted(self, fake_upload_root):
        """A .pdf inside a subdirectory of UPLOAD_ROOT must also be accepted."""
        sub = fake_upload_root / "tenant_1"
        sub.mkdir()
        pdf = _make_pdf(sub, "invoice_sub.pdf")
        result = pdf_viewer_module._safe_pdf_path(str(pdf))
        assert result == pdf.resolve()

    def test_pdf_uppercase_extension_accepted(self, fake_upload_root):
        """.PDF (uppercase) must be treated the same as .pdf."""
        pdf = fake_upload_root / "INVOICE.PDF"
        pdf.write_bytes(b"%PDF-1.4")
        result = pdf_viewer_module._safe_pdf_path(str(pdf))
        assert result == pdf.resolve()

    # ------------------------------------------------------------------
    # Path-confinement violations → 403
    # ------------------------------------------------------------------

    def test_absolute_path_outside_upload_root_rejected(self, fake_upload_root, tmp_path):
        """Absolute path to a .pdf outside UPLOAD_ROOT must raise 403.

        The file does NOT need to exist — the confinement check fires first
        so we never reveal whether files outside UPLOAD_ROOT exist.
        """
        outside = tmp_path / "secret.pdf"           # parent of fake_upload_root
        with pytest.raises(HTTPException) as exc_info:
            pdf_viewer_module._safe_pdf_path(str(outside))
        assert exc_info.value.status_code == 403

    def test_relative_traversal_rejected(self, fake_upload_root, tmp_path):
        """A path containing ../ that resolves outside UPLOAD_ROOT must raise 403."""
        # Construct a traversal path that points to tmp_path (parent of uploads/)
        traversal = str(fake_upload_root / ".." / "escape.pdf")
        with pytest.raises(HTTPException) as exc_info:
            pdf_viewer_module._safe_pdf_path(traversal)
        assert exc_info.value.status_code == 403

    def test_dotenv_traversal_rejected(self, fake_upload_root):
        """.env access via deep traversal must raise 403."""
        # Go up several levels — wherever we end up it is outside UPLOAD_ROOT
        dotenv_path = str(fake_upload_root / ".." / ".." / ".." / ".env")
        with pytest.raises(HTTPException) as exc_info:
            pdf_viewer_module._safe_pdf_path(dotenv_path)
        assert exc_info.value.status_code == 403

    def test_double_slash_absolute_path_rejected(self, fake_upload_root):
        """Absolute path with double-slash prefix must be rejected."""
        # Path("//etc/passwd").resolve() → "/etc/passwd" on POSIX
        outside = "//etc/passwd"
        with pytest.raises(HTTPException) as exc_info:
            pdf_viewer_module._safe_pdf_path(outside)
        assert exc_info.value.status_code == 403

    @pytest.mark.skipif(sys.platform == "win32", reason="Symlinks require elevated privileges on Windows")
    def test_symlink_escape_rejected(self, fake_upload_root, tmp_path):
        """A symlink inside UPLOAD_ROOT pointing to a file outside must raise 403.

        Path.resolve() follows all symlinks, so the resolved path is the real
        target — which is outside UPLOAD_ROOT — and the confinement check fails.
        """
        # Place the real file in the parent (outside UPLOAD_ROOT)
        outside_target = tmp_path / "sensitive_target.pdf"
        outside_target.write_bytes(b"sensitive data")

        symlink_inside = fake_upload_root / "innocent_link.pdf"
        symlink_inside.symlink_to(outside_target)

        with pytest.raises(HTTPException) as exc_info:
            pdf_viewer_module._safe_pdf_path(str(symlink_inside))
        assert exc_info.value.status_code == 403

    # ------------------------------------------------------------------
    # Wrong file type → 403
    # ------------------------------------------------------------------

    def test_txt_file_inside_root_rejected(self, fake_upload_root):
        """.txt file inside UPLOAD_ROOT must still raise 403."""
        txt = fake_upload_root / "data.txt"
        txt.write_text("not a pdf")
        with pytest.raises(HTTPException) as exc_info:
            pdf_viewer_module._safe_pdf_path(str(txt))
        assert exc_info.value.status_code == 403

    def test_sqlite_db_inside_root_rejected(self, fake_upload_root):
        """.db file inside UPLOAD_ROOT must raise 403."""
        db = fake_upload_root / "app.db"
        db.write_bytes(b"SQLite format 3")
        with pytest.raises(HTTPException) as exc_info:
            pdf_viewer_module._safe_pdf_path(str(db))
        assert exc_info.value.status_code == 403

    def test_py_file_inside_root_rejected(self, fake_upload_root):
        """.py source file inside UPLOAD_ROOT must raise 403."""
        py = fake_upload_root / "exploit.py"
        py.write_text("import os; os.system('id')")
        with pytest.raises(HTTPException) as exc_info:
            pdf_viewer_module._safe_pdf_path(str(py))
        assert exc_info.value.status_code == 403

    def test_env_file_inside_root_rejected(self, fake_upload_root):
        """.env file inside UPLOAD_ROOT (no extension suffix trick) must raise 403."""
        env = fake_upload_root / ".env"
        env.write_text("SECRET_KEY=supersecret")
        with pytest.raises(HTTPException) as exc_info:
            pdf_viewer_module._safe_pdf_path(str(env))
        assert exc_info.value.status_code == 403

    # ------------------------------------------------------------------
    # Missing / non-file paths → 404
    # ------------------------------------------------------------------

    def test_missing_file_returns_404(self, fake_upload_root):
        """A path inside UPLOAD_ROOT that does not exist must raise 404."""
        missing = str(fake_upload_root / "missing.pdf")
        with pytest.raises(HTTPException) as exc_info:
            pdf_viewer_module._safe_pdf_path(missing)
        assert exc_info.value.status_code == 404

    def test_directory_path_returns_404(self, fake_upload_root):
        """Pointing at a directory (not a file) inside UPLOAD_ROOT must raise 404."""
        subdir = fake_upload_root / "subdir"
        subdir.mkdir()
        with pytest.raises(HTTPException) as exc_info:
            pdf_viewer_module._safe_pdf_path(str(subdir))
        assert exc_info.value.status_code == 404
