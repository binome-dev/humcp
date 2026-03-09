"""PostgreSQL database tools using SQLAlchemy async."""

from __future__ import annotations

import logging
import os
import re

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from src.humcp.decorator import tool
from src.humcp.permissions import require_auth
from src.tools.database.schemas import (
    ColumnInfo,
    DescribeTableData,
    DescribeTableResponse,
    ExecuteQueryModifyData,
    ExecuteQueryResponse,
    ExecuteQuerySelectData,
    ListTablesData,
    ListTablesResponse,
)

# Engine (lazy initialized)
_engine: AsyncEngine | None = None

logger = logging.getLogger("humcp.tools.database.postgres")


# Pattern for valid SQL identifiers (alphanumeric and underscore, cannot start with digit)
_VALID_IDENTIFIER_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


def _is_valid_identifier(name: str) -> bool:
    """Check if a string is a valid SQL identifier.

    Args:
        name: The identifier to validate.

    Returns:
        True if valid, False otherwise.
    """
    return bool(_VALID_IDENTIFIER_PATTERN.match(name)) and len(name) <= 128


def _extract_table_name(query_upper: str) -> str | None:
    """Extract table name from INSERT, UPDATE, or DELETE queries.

    Args:
        query_upper: The uppercase SQL query string.

    Returns:
        The table name or None if not found or invalid.
    """
    parts = query_upper.split()
    if len(parts) < 2:
        return None

    table_name = None
    if parts[0] == "UPDATE":
        # UPDATE table_name SET ...
        table_name = parts[1]
    elif parts[0] == "INSERT" and len(parts) >= 3 and parts[1] == "INTO":
        # INSERT INTO table_name ...
        table_name = parts[2]
    elif parts[0] == "DELETE" and len(parts) >= 3 and parts[1] == "FROM":
        # DELETE FROM table_name ...
        table_name = parts[2]

    # Validate table name to prevent SQL injection
    if table_name and _is_valid_identifier(table_name):
        return table_name

    return None


def _get_engine() -> AsyncEngine:
    """Get or create the SQLAlchemy async engine."""
    global _engine
    if _engine is None:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is not set")
        # Convert postgresql:// to postgresql+asyncpg:// for async support
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )

        # Log sanitized URL (hide credentials)
        sanitized_url = database_url.split("@")[-1] if "@" in database_url else "***"
        logger.info(
            "Creating database engine for postgresql+asyncpg://***@%s", sanitized_url
        )
        _engine = create_async_engine(database_url, pool_size=5, max_overflow=10)
    return _engine


@tool()
async def execute_query(query: str) -> ExecuteQueryResponse:
    """Execute a SQL query against the PostgreSQL database. Read and write to database

    Executes any SQL query (SELECT, INSERT, UPDATE, DELETE, DDL) and returns
    the results. For SELECT queries, returns rows as a list of dictionaries.
    For other queries, returns the number of affected rows.

    Args:
        query: The SQL query to execute.

    Returns:
        Query results or affected row count.
    """
    try:
        await require_auth()

        engine = _get_engine()
        async with engine.connect() as conn:
            logger.info("Executing query: %s", query)
            result = await conn.execute(text(query))

            # Check if it's a SELECT query (returns rows)
            query_upper = query.strip().upper()
            if query_upper.startswith("SELECT") or query_upper.startswith("WITH"):
                rows = [dict(row._mapping) for row in result.fetchall()]
                return ExecuteQueryResponse(
                    success=True,
                    data=ExecuteQuerySelectData(rows=rows, row_count=len(rows)),
                )
            else:
                # For INSERT/UPDATE/DELETE/DDL, commit and return rowcount
                await conn.commit()
                affected_rows = result.rowcount

                # Extract table name and fetch updated table contents
                table_name = _extract_table_name(query_upper)
                if table_name:
                    select_result = await conn.execute(
                        text(f"SELECT * FROM {table_name}")
                    )
                    rows = [dict(row._mapping) for row in select_result.fetchall()]
                    # Convert rows to string representation
                    rows_str = "\n".join(str(row) for row in rows)
                    return ExecuteQueryResponse(
                        success=True,
                        data=ExecuteQueryModifyData(
                            affected_rows=affected_rows,
                            message="Query executed successfully",
                            table_contents=rows_str,
                        ),
                    )

                return ExecuteQueryResponse(
                    success=True,
                    data=ExecuteQueryModifyData(
                        affected_rows=affected_rows,
                        message="Query executed successfully",
                    ),
                )

    except SQLAlchemyError as e:
        return ExecuteQueryResponse(success=False, error=f"Database error: {e}")
    except ValueError as e:
        return ExecuteQueryResponse(success=False, error=str(e))
    except Exception as e:
        return ExecuteQueryResponse(success=False, error=f"Error: {e}")


@tool()
async def list_tables(schema: str = "public") -> ListTablesResponse:
    """List all tables in the specified schema.

    Args:
        schema: The database schema to list tables from (default: "public").

    Returns:
        List of table names in the schema.
    """
    try:
        await require_auth()

        engine = _get_engine()
        async with engine.connect() as conn:
            result = await conn.execute(
                text("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = :schema
                      AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """),
                {"schema": schema},
            )
            tables = [row[0] for row in result.fetchall()]
            return ListTablesResponse(
                success=True,
                data=ListTablesData(
                    schema_name=schema,
                    tables=tables,
                    count=len(tables),
                ),
            )
    except SQLAlchemyError as e:
        return ListTablesResponse(success=False, error=f"Database error: {e}")
    except ValueError as e:
        return ListTablesResponse(success=False, error=str(e))
    except Exception as e:
        return ListTablesResponse(success=False, error=f"Error: {e}")


@tool()
async def describe_table(
    table_name: str, schema: str = "public"
) -> DescribeTableResponse:
    """Get column information for a table.

    Returns column names, data types, nullability, and default values
    for all columns in the specified table.

    Args:
        table_name: The name of the table to describe.
        schema: The database schema containing the table (default: "public").

    Returns:
        Column definitions for the table.
    """
    try:
        await require_auth()

        engine = _get_engine()
        async with engine.connect() as conn:
            result = await conn.execute(
                text("""
                    SELECT
                        column_name,
                        data_type,
                        is_nullable,
                        column_default,
                        character_maximum_length,
                        numeric_precision,
                        numeric_scale
                    FROM information_schema.columns
                    WHERE table_schema = :schema
                      AND table_name = :table_name
                    ORDER BY ordinal_position
                """),
                {"schema": schema, "table_name": table_name},
            )
            rows = result.fetchall()

            if not rows:
                return DescribeTableResponse(
                    success=False, error=f"Table '{schema}.{table_name}' not found"
                )

            columns = [
                ColumnInfo(
                    name=row[0],
                    type=row[1],
                    nullable=row[2] == "YES",
                    default=row[3],
                    max_length=row[4],
                    precision=row[5],
                    scale=row[6],
                )
                for row in rows
            ]

            return DescribeTableResponse(
                success=True,
                data=DescribeTableData(
                    schema_name=schema,
                    table=table_name,
                    columns=columns,
                    column_count=len(columns),
                ),
            )
    except SQLAlchemyError as e:
        return DescribeTableResponse(success=False, error=f"Database error: {e}")
    except ValueError as e:
        return DescribeTableResponse(success=False, error=str(e))
    except Exception as e:
        return DescribeTableResponse(success=False, error=f"Error: {e}")
