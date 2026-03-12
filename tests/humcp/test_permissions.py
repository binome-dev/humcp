"""Tests for humcp permissions module."""

import logging

import pytest
from fastapi import HTTPException

from src.humcp.permissions import check_permission, require_auth


class TestRequireAuth:
    """Tests for require_auth function."""

    @pytest.mark.asyncio
    async def test_require_auth_no_user_no_strict(self, monkeypatch):
        """Returns None in dev mode (TOOLSET_REQUIRE_AUTH not set)."""
        monkeypatch.setattr("src.humcp.permissions.TOOLSET_REQUIRE_AUTH", False)
        # Ensure no user is set
        monkeypatch.setattr(
            "src.humcp.permissions.get_current_user_id", lambda: None
        )
        result = await require_auth()
        assert result is None

    @pytest.mark.asyncio
    async def test_require_auth_no_user_strict(self, monkeypatch):
        """Raises HTTPException 401 when TOOLSET_REQUIRE_AUTH=true and no user."""
        monkeypatch.setattr("src.humcp.permissions.TOOLSET_REQUIRE_AUTH", True)
        monkeypatch.setattr(
            "src.humcp.permissions.get_current_user_id", lambda: None
        )
        with pytest.raises(HTTPException) as exc_info:
            await require_auth()
        assert exc_info.value.status_code == 401


class TestCheckPermission:
    """Tests for check_permission function."""

    @pytest.mark.asyncio
    async def test_check_permission_logs_warning(self, monkeypatch, caplog):
        """Verify warning is logged about stub permission check."""
        monkeypatch.setattr("src.humcp.permissions.STRICT_PERMISSIONS", False)
        monkeypatch.setattr("src.humcp.permissions.TOOLSET_REQUIRE_AUTH", False)
        monkeypatch.setattr(
            "src.humcp.permissions.get_current_user_id", lambda: None
        )

        with caplog.at_level(logging.WARNING, logger="src.humcp.permissions"):
            await check_permission("document", "doc-123", "viewer")

        assert any("Permission check stub" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_check_permission_strict_raises_403(self, monkeypatch):
        """Raises 403 when STRICT_PERMISSIONS=true."""
        monkeypatch.setattr("src.humcp.permissions.STRICT_PERMISSIONS", True)

        with pytest.raises(HTTPException) as exc_info:
            await check_permission("document", "doc-123", "viewer")
        assert exc_info.value.status_code == 403
