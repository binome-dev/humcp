"""Tests for toolset auth helpers."""

from unittest.mock import MagicMock, patch
from uuid import UUID

from src.humcp.auth import _current_user_id, get_current_user_id

# Patch target: the function is imported lazily inside get_current_user_id
FASTMCP_GET_TOKEN = "fastmcp.server.dependencies.get_access_token"


class TestGetCurrentUserId:
    """Tests for get_current_user_id()."""

    def setup_method(self):
        _current_user_id.set(None)

    def test_returns_none_when_no_auth_context(self):
        with patch(FASTMCP_GET_TOKEN, return_value=None):
            assert get_current_user_id() is None

    def test_returns_uuid_from_fastmcp_token(self):
        user_uuid = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        mock_token = MagicMock()
        mock_token.client_id = user_uuid
        mock_token.claims = {"sub": user_uuid}

        with patch(FASTMCP_GET_TOKEN, return_value=mock_token):
            result = get_current_user_id()
            assert result == UUID(user_uuid)

    def test_falls_back_to_context_var(self):
        user_uuid = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        _current_user_id.set(user_uuid)

        with patch(FASTMCP_GET_TOKEN, side_effect=RuntimeError):
            result = get_current_user_id()
            assert result == UUID(user_uuid)

    def test_returns_none_for_invalid_context_var(self):
        _current_user_id.set("not-a-uuid")

        with patch(FASTMCP_GET_TOKEN, side_effect=RuntimeError):
            assert get_current_user_id() is None

    def test_returns_none_when_context_var_is_none(self):
        _current_user_id.set(None)

        with patch(FASTMCP_GET_TOKEN, side_effect=RuntimeError):
            assert get_current_user_id() is None

    def test_prefers_fastmcp_over_context_var(self):
        fastmcp_uuid = "11111111-1111-1111-1111-111111111111"
        contextvar_uuid = "22222222-2222-2222-2222-222222222222"
        _current_user_id.set(contextvar_uuid)

        mock_token = MagicMock()
        mock_token.client_id = fastmcp_uuid
        mock_token.claims = {"sub": fastmcp_uuid}

        with patch(FASTMCP_GET_TOKEN, return_value=mock_token):
            result = get_current_user_id()
            assert result == UUID(fastmcp_uuid)
