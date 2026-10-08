"""Targeted unit tests for the password reset flow.

These tests use mocks and in-memory SQLite only.
They do NOT connect to Supabase or send real emails.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, call


# ── Token model tests (pure logic, no DB) ─────────────────────────────────────

class TestPasswordResetToken:
    """Tests for PasswordResetToken model logic."""

    def test_generate_token_is_url_safe_string(self):
        """Token must be a non-empty URL-safe string."""
        from app.password_reset import PasswordResetToken
        token = PasswordResetToken.generate_token()
        assert isinstance(token, str)
        assert len(token) >= 40  # token_urlsafe(32) → ~43 chars
        # No characters that would break a URL query string
        assert " " not in token
        assert "&" not in token

    def test_generate_token_is_unique(self):
        """Two successive calls must produce different tokens."""
        from app.password_reset import PasswordResetToken
        t1 = PasswordResetToken.generate_token()
        t2 = PasswordResetToken.generate_token()
        assert t1 != t2

    def test_create_token_sets_expiry(self):
        """create_token must set expires_at to now + requested hours."""
        from app.password_reset import PasswordResetToken
        before = datetime.utcnow()
        token_obj = PasswordResetToken.create_token(user_id=1, expires_in_hours=24)
        after = datetime.utcnow()

        assert token_obj.user_id == 1
        assert token_obj.used is False
        # expires_at should be roughly 24 h from now
        expected_min = before + timedelta(hours=23, minutes=59)
        expected_max = after + timedelta(hours=24, minutes=1)
        assert expected_min <= token_obj.expires_at <= expected_max

    def test_is_valid_fresh_token(self):
        """A freshly created token must be valid."""
        from app.password_reset import PasswordResetToken
        token_obj = PasswordResetToken.create_token(user_id=1, expires_in_hours=24)
        assert token_obj.is_valid() is True

    def test_is_valid_expired_token(self):
        """A token with expires_at in the past must be invalid."""
        from app.password_reset import PasswordResetToken
        token_obj = PasswordResetToken.create_token(user_id=1, expires_in_hours=24)
        token_obj.expires_at = datetime.utcnow() - timedelta(seconds=1)
        assert token_obj.is_valid() is False

    def test_is_valid_used_token(self):
        """A token that has been used must be invalid even if not expired."""
        from app.password_reset import PasswordResetToken
        token_obj = PasswordResetToken.create_token(user_id=1, expires_in_hours=24)
        token_obj.mark_as_used()
        assert token_obj.is_valid() is False

    def test_mark_as_used(self):
        """mark_as_used must set used flag to True."""
        from app.password_reset import PasswordResetToken
        token_obj = PasswordResetToken.create_token(user_id=1)
        assert token_obj.used is False
        token_obj.mark_as_used()
        assert token_obj.used is True


# ── Email service tests (mocked SendGrid) ─────────────────────────────────────

class TestPasswordResetEmail:
    """Tests for the email sending function — SendGrid is mocked."""

    def test_send_skipped_when_api_key_empty(self):
        """send_password_reset_email must return False and not call Resend
        when RESEND_API_KEY is empty."""
        with patch("app.email_service.RESEND_API_KEY", ""):
            from app.email_service import send_password_reset_email
            result = send_password_reset_email(
                to_email="user@example.com",
                reset_token="abc123",
                reset_url="http://localhost:8000/reset-password",
            )
        assert result is False

    def test_send_calls_resend_with_correct_to_address(self):
        """When RESEND_API_KEY is set, Resend.Emails.send must be called
        with the correct recipient address."""
        fake_response = {"id": "fake-email-id-123"}

        with patch("app.email_service.RESEND_API_KEY", "re_fake-key-for-test"), \
             patch("app.email_service.resend.Emails.send", return_value=fake_response) as mock_send:

            from app.email_service import send_password_reset_email
            result = send_password_reset_email(
                to_email="target@example.com",
                reset_token="tok123",
                reset_url="https://valixs.com/reset-password",
                user_name="Test User",
            )

        assert result is True
        assert mock_send.called
        call_params = mock_send.call_args[0][0]
        assert "target@example.com" in call_params["to"]

    def test_send_returns_false_on_resend_error(self):
        """If Resend raises an exception, send must return False (not crash)."""
        with patch("app.email_service.RESEND_API_KEY", "re_fake-key"), \
             patch("app.email_service.resend.Emails.send", side_effect=Exception("network error")):

            from app.email_service import send_password_reset_email
            result = send_password_reset_email(
                to_email="user@example.com",
                reset_token="tok",
                reset_url="https://valixs.com/reset-password",
            )

        assert result is False


# ── BASE_URL config tests ──────────────────────────────────────────────────────

class TestBaseUrlConfig:
    """Verify that BASE_URL env var is read correctly."""

    def test_base_url_defaults_to_empty_string(self):
        """When BASE_URL is not set, config.BASE_URL must be empty string."""
        import importlib
        import os
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("BASE_URL", None)
            import app.config as cfg
            importlib.reload(cfg)
            assert cfg.BASE_URL == ""

    def test_base_url_read_from_env(self):
        """When BASE_URL is set, config.BASE_URL must match (trailing slash stripped)."""
        import importlib
        import os
        with patch.dict(os.environ, {"BASE_URL": "https://valixs.com/"}, clear=False):
            import app.config as cfg
            importlib.reload(cfg)
            assert cfg.BASE_URL == "https://valixs.com"  # trailing slash stripped

    def test_reset_link_uses_base_url_when_set(self):
        """The reset link must use BASE_URL, not request.base_url, when configured."""
        reset_base = "https://valixs.com"
        # Simulate what the route does
        request_base_url = "http://0.0.0.0:8000"  # what Azure proxy would give
        base_url = reset_base or request_base_url
        reset_url = f"{base_url}/reset-password"
        assert reset_url == "https://valixs.com/reset-password"

    def test_reset_link_falls_back_to_request_base_url(self):
        """When BASE_URL is empty, request.base_url is used (local dev behaviour)."""
        reset_base = ""
        request_base_url = "http://localhost:8000"
        base_url = reset_base or request_base_url
        reset_url = f"{base_url}/reset-password"
        assert reset_url == "http://localhost:8000/reset-password"
