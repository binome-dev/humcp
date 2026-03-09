"""Generic SQL database tools using SQLAlchemy."""

from __future__ import annotations

import logging
import os
from typing import Any

from src.humcp.decorator import tool
from src.humcp.permissions import require_auth
from src.tools.database.schemas import (
    SqlQueryData,
    SqlQueryResponse,
)

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import SQLAlchemyError
except ImportError as err:
    raise ImportError(
        "sqlalchemy is required for SQL tools. Install with: pip install sqlalchemy"
    ) from err

logger = logging.getLogger("humcp.tools.database.sql")


@tool()
async def sql_query(
    query: str,
    connection_string: str | None = None,
    params: dict[str, Any] | None = None,
) -> SqlQueryResponse:
    """Execute a SQL query against any SQLAlchemy-supported database.

    Supports any database with a SQLAlchemy dialect (PostgreSQL, MySQL, SQLite,
    Oracle, MSSQL, etc.). For SELECT queries, returns rows as a list of
    dictionaries. For modification queries, returns the number of affected rows.

    Args:
        query: The SQL query to execute.
        connection_string: SQLAlchemy connection URL (e.g., "sqlite:///mydb.db",
            "mysql://user:pass@host/db"). Falls back to SQL_CONNECTION_STRING env var.
        params: Optional dictionary of query parameters for parameterized queries.

    Returns:
        Query results or affected row count.
    """
    try:
        await require_auth()

        resolved_connection = connection_string or os.getenv("SQL_CONNECTION_STRING")
        if not resolved_connection:
            return SqlQueryResponse(
                success=False,
                error="No connection string provided. Pass connection_string or set SQL_CONNECTION_STRING env var.",
            )

        logger.info("Executing SQL query: %s", query)

        engine = create_engine(resolved_connection)
        try:
            with engine.connect() as conn:
                result = conn.execute(text(query), params or {})

                query_upper = query.strip().upper()
                is_select = query_upper.startswith("SELECT") or query_upper.startswith(
                    "WITH"
                )

                if is_select:
                    rows = [dict(row._mapping) for row in result.fetchall()]
                    return SqlQueryResponse(
                        success=True,
                        data=SqlQueryData(
                            rows=rows,
                            row_count=len(rows),
                            affected_rows=None,
                        ),
                    )
                else:
                    conn.commit()
                    affected = result.rowcount
                    return SqlQueryResponse(
                        success=True,
                        data=SqlQueryData(
                            rows=[],
                            row_count=0,
                            affected_rows=affected,
                        ),
                    )
        finally:
            engine.dispose()

    except SQLAlchemyError as e:
        logger.exception("SQL query failed")
        return SqlQueryResponse(success=False, error=f"Database error: {e}")
    except Exception as e:
        logger.exception("SQL query failed")
        return SqlQueryResponse(success=False, error=str(e))
