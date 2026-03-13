"""Tests for humcp auth module."""

from uuid import UUID

from src.humcp.auth import (
    _current_user_id,
    get_current_user_id,
    has_google_credentials,
    is_auth_enabled,
)


class TestIsAuthEnabled:
    """Tests for is_auth_enabled function."""

    def test_is_auth_enabled_true(self, monkeypatch):
        """AUTH_ENABLED=true should return True."""
        monkeypatch.setenv("AUTH_ENABLED", "true")
        assert is_auth_enabled() is True

    def test_is_auth_enabled_false(self, monkeypatch):
        """AUTH_ENABLED=false should return False."""
        monkeypatch.setenv("AUTH_ENABLED", "false")
        assert is_auth_enabled() is False

    def test_is_auth_enabled_default(self, monkeypatch):
        """No AUTH_ENABLED env var should default to True."""
        monkeypatch.delenv("AUTH_ENABLED", raising=False)
        assert is_auth_enabled() is True

    def test_is_auth_enabled_case_insensitive(self, monkeypatch):
        """AUTH_ENABLED=TRUE (uppercase) should return True."""
        monkeypatch.setenv("AUTH_ENABLED", "TRUE")
        assert is_auth_enabled() is True


class TestHasGoogleCredentials:
    """Tests for has_google_credentials function."""

    def test_has_google_credentials_missing(self, monkeypatch):
        """Returns False when credentials are not set."""
        monkeypatch.delenv("GOOGLE_OAUTH_CLIENT_ID", raising=False)
        monkeypatch.delenv("GOOGLE_OAUTH_CLIENT_SECRET", raising=False)
        assert has_google_credentials() is False

    def test_has_google_credentials_set(self, monkeypatch):
        """Returns True when both client ID and secret are set."""
        monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "test-client-id")
        monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "test-client-secret")
        assert has_google_credentials() is True


class TestGetCurrentUserId:
    """Tests for get_current_user_id function."""

    def test_get_current_user_id_none(self):
        """Returns None when no context is set."""
        token = _current_user_id.set(None)
        try:
            result = get_current_user_id()
            assert result is None
        finally:
            _current_user_id.reset(token)

    def test_get_current_user_id_from_contextvar(self):
        """Returns UUID from the ContextVar when set."""
        test_uuid = "12345678-1234-5678-1234-567812345678"
        token = _current_user_id.set(test_uuid)
        try:
            result = get_current_user_id()
            assert result == UUID(test_uuid)
            assert isinstance(result, UUID)
        finally:
            _current_user_id.reset(token)
