"""Tests for PostgreSQL database tools using SQLAlchemy."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from src.tools.database import postgres
from src.tools.database.postgres import (
    describe_table,
    execute_query,
    list_tables,
)


@pytest.fixture(autouse=True)
def reset_engine():
    """Reset the engine before each test."""
    postgres._engine = None
    yield
    postgres._engine = None


@pytest.fixture
def mock_env_database_url():
    """Mock DATABASE_URL environment variable."""
    with patch.dict(
        os.environ, {"DATABASE_URL": "postgresql://test:test@localhost/test"}
    ):
        yield


@pytest.fixture
def mock_engine():
    """Create a mock SQLAlchemy async engine."""
    mock_conn = AsyncMock()
    mock_result = MagicMock()
    mock_conn.execute = AsyncMock(return_value=mock_result)
    mock_conn.commit = AsyncMock()

    # Create an async context manager mock for engine.connect()
    class MockConnectContext:
        async def __aenter__(self):
            return mock_conn

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    mock_engine_instance = MagicMock()
    mock_engine_instance.connect.return_value = MockConnectContext()

    with patch("src.tools.database.postgres.create_async_engine") as mock_create:
        mock_create.return_value = mock_engine_instance
        yield mock_conn, mock_result, mock_engine_instance


class TestExecuteQuery:
    @pytest.mark.asyncio
    async def test_select_query_success(self, mock_env_database_url, mock_engine):
        mock_conn, mock_result, _ = mock_engine

        # Mock row objects with _mapping attribute
        mock_row1 = MagicMock()
        mock_row1._mapping = {"id": 1, "name": "Alice"}
        mock_row2 = MagicMock()
        mock_row2._mapping = {"id": 2, "name": "Bob"}
        mock_result.fetchall.return_value = [mock_row1, mock_row2]

        result = await execute_query("SELECT * FROM users")

        assert result.success is True
        assert result.data.row_count == 2
        assert result.data.rows[0]["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_with_query_success(self, mock_env_database_url, mock_engine):
        mock_conn, mock_result, _ = mock_engine

        mock_row = MagicMock()
        mock_row._mapping = {"count": 5}
        mock_result.fetchall.return_value = [mock_row]

        result = await execute_query(
            "WITH cte AS (SELECT 1) SELECT count(*) as count FROM cte"
        )

        assert result.success is True
        assert result.data.rows[0]["count"] == 5

    @pytest.mark.asyncio
    async def test_insert_query_success(self, mock_env_database_url, mock_engine):
        mock_conn, mock_result, _ = mock_engine
        mock_result.rowcount = 1

        result = await execute_query("INSERT INTO users (name) VALUES ('Charlie')")

        assert result.success is True
        assert result.data.affected_rows == 1
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_query_success(self, mock_env_database_url, mock_engine):
        mock_conn, mock_result, _ = mock_engine
        mock_result.rowcount = 3

        result = await execute_query("UPDATE users SET active = true")

        assert result.success is True
        assert result.data.affected_rows == 3
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_query_success(self, mock_env_database_url, mock_engine):
        mock_conn, mock_result, _ = mock_engine
        mock_result.rowcount = 2

        result = await execute_query("DELETE FROM users WHERE active = false")

        assert result.success is True
        assert result.data.affected_rows == 2
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_missing_database_url(self):
        with patch.dict(os.environ, {}, clear=True):
            if "DATABASE_URL" in os.environ:
                del os.environ["DATABASE_URL"]

            result = await execute_query("SELECT 1")

            assert result.success is False
            assert "DATABASE_URL" in result.error

    @pytest.mark.asyncio
    async def test_database_error(self, mock_env_database_url, mock_engine):
        mock_conn, _, _ = mock_engine
        from sqlalchemy.exc import SQLAlchemyError

        mock_conn.execute.side_effect = SQLAlchemyError("syntax error")

        result = await execute_query("SELECT * FROM")

        assert result.success is False
        assert "Database error" in result.error


class TestListTables:
    @pytest.mark.asyncio
    async def test_list_tables_success(self, mock_env_database_url, mock_engine):
        mock_conn, mock_result, _ = mock_engine
        mock_result.fetchall.return_value = [
            ("users",),
            ("orders",),
            ("products",),
        ]

        result = await list_tables()

        assert result.success is True
        assert result.data.schema_name == "public"
        assert result.data.count == 3
        assert "users" in result.data.tables

    @pytest.mark.asyncio
    async def test_list_tables_custom_schema(self, mock_env_database_url, mock_engine):
        mock_conn, mock_result, _ = mock_engine
        mock_result.fetchall.return_value = [("events",)]

        result = await list_tables(schema="analytics")

        assert result.success is True
        assert result.data.schema_name == "analytics"
        assert result.data.tables == ["events"]

    @pytest.mark.asyncio
    async def test_list_tables_empty(self, mock_env_database_url, mock_engine):
        mock_conn, mock_result, _ = mock_engine
        mock_result.fetchall.return_value = []

        result = await list_tables()

        assert result.success is True
        assert result.data.tables == []
        assert result.data.count == 0

    @pytest.mark.asyncio
    async def test_list_tables_missing_database_url(self):
        with patch.dict(os.environ, {}, clear=True):
            if "DATABASE_URL" in os.environ:
                del os.environ["DATABASE_URL"]

            result = await list_tables()

            assert result.success is False
            assert "DATABASE_URL" in result.error


class TestDescribeTable:
    @pytest.mark.asyncio
    async def test_describe_table_success(self, mock_env_database_url, mock_engine):
        mock_conn, mock_result, _ = mock_engine
        mock_result.fetchall.return_value = [
            ("id", "integer", "NO", "nextval('users_id_seq'::regclass)", None, 32, 0),
            ("email", "character varying", "NO", None, 255, None, None),
            (
                "created_at",
                "timestamp with time zone",
                "YES",
                "now()",
                None,
                None,
                None,
            ),
        ]

        result = await describe_table("users")

        assert result.success is True
        assert result.data.table == "users"
        assert result.data.schema_name == "public"
        assert result.data.column_count == 3

        columns = result.data.columns
        assert columns[0].name == "id"
        assert columns[0].type == "integer"
        assert columns[0].nullable is False

        assert columns[1].name == "email"
        assert columns[1].max_length == 255

        assert columns[2].name == "created_at"
        assert columns[2].nullable is True

    @pytest.mark.asyncio
    async def test_describe_table_custom_schema(
        self, mock_env_database_url, mock_engine
    ):
        mock_conn, mock_result, _ = mock_engine
        mock_result.fetchall.return_value = [
            ("event_id", "uuid", "NO", None, None, None, None),
        ]

        result = await describe_table("events", schema="analytics")

        assert result.success is True
        assert result.data.schema_name == "analytics"
        assert result.data.table == "events"

    @pytest.mark.asyncio
    async def test_describe_table_not_found(self, mock_env_database_url, mock_engine):
        mock_conn, mock_result, _ = mock_engine
        mock_result.fetchall.return_value = []

        result = await describe_table("nonexistent_table")

        assert result.success is False
        assert "not found" in result.error

    @pytest.mark.asyncio
    async def test_describe_table_missing_database_url(self):
        with patch.dict(os.environ, {}, clear=True):
            if "DATABASE_URL" in os.environ:
                del os.environ["DATABASE_URL"]

            result = await describe_table("users")

            assert result.success is False
            assert "DATABASE_URL" in result.error
