"""DuckDB database tools for querying and listing tables."""

from __future__ import annotations

import logging
from typing import Any

from src.humcp.decorator import tool
from src.humcp.permissions import require_auth
from src.tools.database.schemas import (
    DuckDbListTablesData,
    DuckDbListTablesResponse,
    DuckDbQueryData,
    DuckDbQueryResponse,
    DuckDbReadFileData,
    DuckDbReadFileResponse,
)

try:
    import duckdb
except ImportError as err:
    raise ImportError(
        "duckdb is required for DuckDB tools. Install with: pip install duckdb"
    ) from err

logger = logging.getLogger("humcp.tools.database.duckdb")


def _get_connection(database_path: str | None) -> duckdb.DuckDBPyConnection:
    """Create a DuckDB connection.

    Args:
        database_path: Path to the DuckDB database file, or None for in-memory.

    Returns:
        A DuckDB connection instance.
    """
    kwargs: dict[str, Any] = {}
    if database_path:
        kwargs["database"] = database_path
    return duckdb.connect(**kwargs)


@tool()
async def duckdb_query(
    query: str,
    database_path: str | None = None,
) -> DuckDbQueryResponse:
    """Execute a SQL query against a DuckDB database.

    Runs any SQL query (SELECT, INSERT, CREATE, etc.) and returns the results.
    For SELECT queries, returns rows as a list of dictionaries.
    For other queries, returns a success message.

    Args:
        query: The SQL query to execute.
        database_path: Path to the DuckDB database file. If not provided, uses an in-memory database.

    Returns:
        Query results or success message.
    """
    try:
        await require_auth()

        logger.info("Executing DuckDB query: %s", query)

        # Remove backticks and only run the first statement
        formatted_sql = query.replace("`", "")
        formatted_sql = formatted_sql.split(";")[0]

        conn = _get_connection(database_path)
        try:
            result = conn.sql(formatted_sql)

            if result is None:
                return DuckDbQueryResponse(
                    success=True,
                    data=DuckDbQueryData(
                        columns=[],
                        rows=[],
                        row_count=0,
                    ),
                )

            columns = result.columns
            raw_rows = result.fetchall()
            rows = [dict(zip(columns, row, strict=False)) for row in raw_rows]

            return DuckDbQueryResponse(
                success=True,
                data=DuckDbQueryData(
                    columns=columns,
                    rows=rows,
                    row_count=len(rows),
                ),
            )
        finally:
            conn.close()

    except duckdb.Error as e:
        logger.exception("DuckDB query failed")
        return DuckDbQueryResponse(success=False, error=f"DuckDB error: {e}")
    except Exception as e:
        logger.exception("DuckDB query failed")
        return DuckDbQueryResponse(success=False, error=str(e))


@tool()
async def duckdb_list_tables(
    database_path: str | None = None,
) -> DuckDbListTablesResponse:
    """List all tables in a DuckDB database.

    Args:
        database_path: Path to the DuckDB database file. If not provided, uses an in-memory database.

    Returns:
        List of table names in the database.
    """
    try:
        await require_auth()

        logger.info("Listing DuckDB tables for database: %s", database_path)

        conn = _get_connection(database_path)
        try:
            result = conn.sql("SHOW TABLES")
            tables: list[str] = []
            if result is not None:
                raw_rows = result.fetchall()
                tables = [str(row[0]) for row in raw_rows]

            return DuckDbListTablesResponse(
                success=True,
                data=DuckDbListTablesData(
                    tables=tables,
                    count=len(tables),
                    database_path=database_path,
                ),
            )
        finally:
            conn.close()

    except duckdb.Error as e:
        logger.exception("DuckDB list tables failed")
        return DuckDbListTablesResponse(success=False, error=f"DuckDB error: {e}")
    except Exception as e:
        logger.exception("DuckDB list tables failed")
        return DuckDbListTablesResponse(success=False, error=str(e))


@tool()
async def duckdb_read_file(
    file_path: str,
    limit: int = 100,
) -> DuckDbReadFileResponse:
    """Read data from a Parquet, CSV, or JSON file using DuckDB.

    DuckDB auto-detects the file format based on the extension. Supported
    formats include CSV, Parquet, JSON, and JSON Lines.

    Args:
        file_path: Path to the file to read (.csv, .parquet, .json, .jsonl).
        limit: Maximum number of rows to return. Default 100.

    Returns:
        Rows from the file with column names and row count.
    """
    try:
        await require_auth()

        logger.info("DuckDB reading file: %s limit=%d", file_path, limit)

        conn = _get_connection(None)
        try:
            safe_limit = max(1, min(limit, 10000))
            result = conn.sql(f"SELECT * FROM '{file_path}' LIMIT {safe_limit}")

            if result is None:
                return DuckDbReadFileResponse(
                    success=True,
                    data=DuckDbReadFileData(
                        file_path=file_path,
                        columns=[],
                        rows=[],
                        row_count=0,
                    ),
                )

            columns = result.columns
            raw_rows = result.fetchall()
            rows = [dict(zip(columns, row, strict=False)) for row in raw_rows]

            return DuckDbReadFileResponse(
                success=True,
                data=DuckDbReadFileData(
                    file_path=file_path,
                    columns=columns,
                    rows=rows,
                    row_count=len(rows),
                ),
            )
        finally:
            conn.close()

    except duckdb.Error as e:
        logger.exception("DuckDB read file failed")
        return DuckDbReadFileResponse(success=False, error=f"DuckDB error: {e}")
    except Exception as e:
        logger.exception("DuckDB read file failed")
        return DuckDbReadFileResponse(success=False, error=str(e))
