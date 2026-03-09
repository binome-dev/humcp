"""Tests for toolset permission checking service."""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
from fastapi import HTTPException
from src.humcp.permissions import check_permission, has_permission, require_auth

USER_ID = UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")
ORG_ID = "org-001"


def _make_mock_engine(execute_results):
    """Create a mock async engine with conn.execute returning results in order."""
    call_index = {"i": 0}

    async def mock_execute(*args, **kwargs):
        idx = call_index["i"]
        call_index["i"] += 1
        mock_result = MagicMock()
        if idx < len(execute_results):
            mock_result.first.return_value = execute_results[idx].get("first")
            mock_result.fetchall.return_value = execute_results[idx].get("fetchall", [])
        else:
            mock_result.first.return_value = None
            mock_result.fetchall.return_value = []
        return mock_result

    mock_conn = MagicMock()
    mock_conn.execute = mock_execute

    @asynccontextmanager
    async def mock_connect():
        yield mock_conn

    mock_engine = MagicMock()
    mock_engine.connect = mock_connect
    return mock_engine


class TestHasPermission:
    """Tests for has_permission()."""

    @pytest.mark.asyncio
    async def test_no_tuples_allows_viewer(self):
        """Resource with no IAM tuples → allow viewer (read-only)."""
        engine = _make_mock_engine([{"first": None}])  # step 0: no tuples
        with patch("src.humcp.permissions._get_engine", return_value=engine):
            result = await has_permission(
                USER_ID, "storage_bucket", "my-bucket", "viewer"
            )
            assert result is True

    @pytest.mark.asyncio
    async def test_no_tuples_denies_editor(self):
        """Resource with no IAM tuples → deny editor (write)."""
        engine = _make_mock_engine([{"first": None}])  # step 0: no tuples
        with patch("src.humcp.permissions._get_engine", return_value=engine):
            result = await has_permission(
                USER_ID, "storage_bucket", "my-bucket", "editor"
            )
            assert result is False

    @pytest.mark.asyncio
    async def test_no_tuples_denies_owner(self):
        """Resource with no IAM tuples → deny owner."""
        engine = _make_mock_engine([{"first": None}])  # step 0: no tuples
        with patch("src.humcp.permissions._get_engine", return_value=engine):
            result = await has_permission(
                USER_ID, "storage_bucket", "my-bucket", "owner"
            )
            assert result is False

    @pytest.mark.asyncio
    async def test_direct_match_returns_true(self):
        engine = _make_mock_engine(
            [
                {"first": (1,)},  # step 0: tuples exist
                {"first": (1,)},  # step 1: direct match
            ]
        )
        with patch("src.humcp.permissions._get_engine", return_value=engine):
            result = await has_permission(
                USER_ID, "storage_bucket", "my-bucket", "viewer"
            )
            assert result is True

    @pytest.mark.asyncio
    async def test_no_match_returns_false(self):
        engine = _make_mock_engine(
            [
                {"first": (1,)},  # step 0: tuples exist
                {"first": None},  # step 1: no direct match
                {"fetchall": []},  # step 2: no org memberships
            ]
        )
        with patch("src.humcp.permissions._get_engine", return_value=engine):
            result = await has_permission(
                USER_ID, "storage_bucket", "my-bucket", "viewer"
            )
            assert result is False

    @pytest.mark.asyncio
    async def test_org_based_match_returns_true(self):
        engine = _make_mock_engine(
            [
                {"first": (1,)},  # step 0: tuples exist
                {"first": None},  # step 1: no direct match
                {"fetchall": [(ORG_ID,)]},  # step 2: actor is in org
                {"first": (1,)},  # step 3: org has relation on object
            ]
        )
        with patch("src.humcp.permissions._get_engine", return_value=engine):
            result = await has_permission(
                USER_ID, "storage_bucket", "my-bucket", "viewer"
            )
            assert result is True


class TestCheckPermission:
    """Tests for check_permission()."""

    @pytest.mark.asyncio
    async def test_returns_none_when_no_user(self):
        with patch("src.humcp.permissions.get_current_user_id", return_value=None):
            with patch("src.humcp.permissions.TOOLSET_REQUIRE_AUTH", False):
                result = await check_permission("storage_bucket", "my-bucket", "viewer")
                assert result is None

    @pytest.mark.asyncio
    async def test_raises_401_when_require_auth_true_and_no_user(self):
        with patch("src.humcp.permissions.get_current_user_id", return_value=None):
            with patch("src.humcp.permissions.TOOLSET_REQUIRE_AUTH", True):
                with pytest.raises(HTTPException) as exc_info:
                    await check_permission("storage_bucket", "my-bucket", "viewer")
                assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_raises_403_when_user_lacks_permission(self):
        with patch("src.humcp.permissions.get_current_user_id", return_value=USER_ID):
            with patch(
                "src.humcp.permissions.has_permission",
                new_callable=AsyncMock,
                return_value=False,
            ):
                with pytest.raises(HTTPException) as exc_info:
                    await check_permission("storage_bucket", "my-bucket", "viewer")
                assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_returns_user_id_when_authorized(self):
        with patch("src.humcp.permissions.get_current_user_id", return_value=USER_ID):
            with patch(
                "src.humcp.permissions.has_permission",
                new_callable=AsyncMock,
                return_value=True,
            ):
                result = await check_permission("storage_bucket", "my-bucket", "viewer")
                assert result == USER_ID


class TestRequireAuth:
    """Tests for require_auth()."""

    @pytest.mark.asyncio
    async def test_returns_user_id_when_authenticated(self):
        with patch("src.humcp.permissions.get_current_user_id", return_value=USER_ID):
            result = await require_auth()
            assert result == USER_ID

    @pytest.mark.asyncio
    async def test_returns_none_when_no_user_and_not_required(self):
        with patch("src.humcp.permissions.get_current_user_id", return_value=None):
            with patch("src.humcp.permissions.TOOLSET_REQUIRE_AUTH", False):
                result = await require_auth()
                assert result is None

    @pytest.mark.asyncio
    async def test_raises_401_when_no_user_and_required(self):
        with patch("src.humcp.permissions.get_current_user_id", return_value=None):
            with patch("src.humcp.permissions.TOOLSET_REQUIRE_AUTH", True):
                with pytest.raises(HTTPException) as exc_info:
                    await require_auth()
                assert exc_info.value.status_code == 401
