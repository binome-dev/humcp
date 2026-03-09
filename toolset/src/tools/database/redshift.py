"""Amazon Redshift database tools for query execution."""

from __future__ import annotations

import logging
import os
from typing import Any

from src.humcp.decorator import tool
from src.humcp.permissions import require_auth
from src.tools.database.schemas import (
    RedshiftQueryData,
    RedshiftQueryResponse,
)

try:
    import redshift_connector
except ImportError as err:
    raise ImportError(
        "redshift_connector is required for Redshift tools. "
        "Install with: pip install redshift-connector"
    ) from err

logger = logging.getLogger("humcp.tools.database.redshift")


def _get_connection(database: str | None = None) -> redshift_connector.Connection:
    """Create a Redshift connection from environment variables.

    Args:
        database: Optional database name override. Falls back to REDSHIFT_DATABASE env var.

    Returns:
        A Redshift connection instance.

    Raises:
        ValueError: If required environment variables are not set.
    """
    host = os.getenv("REDSHIFT_HOST")
    user = os.getenv("REDSHIFT_USER")
    password = os.getenv("REDSHIFT_PASSWORD")
    db = database or os.getenv("REDSHIFT_DATABASE")

    if not host:
        raise ValueError("REDSHIFT_HOST environment variable is required")
    if not user:
        raise ValueError("REDSHIFT_USER environment variable is required")
    if not password:
        raise ValueError("REDSHIFT_PASSWORD environment variable is required")
    if not db:
        raise ValueError(
            "Database name is required. Provide database parameter or set REDSHIFT_DATABASE env var."
        )

    return redshift_connector.connect(
        host=host,
        port=int(os.getenv("REDSHIFT_PORT", "5439")),
        database=db,
        user=user,
        password=password,
        ssl=True,
    )


@tool()
async def redshift_query(
    query: str,
    database: str | None = None,
) -> RedshiftQueryResponse:
    """Execute a SQL query against an Amazon Redshift database.

    Runs any SQL query and returns the results. For SELECT queries, returns
    rows as a list of dictionaries. For modification queries, returns a
    success message.

    Args:
        query: The SQL query to execute.
        database: Optional database name. Falls back to REDSHIFT_DATABASE env var.

    Returns:
        Query results with columns and rows.
    """
    try:
        await require_auth()

        logger.info("Executing Redshift query: %s", query)

        conn = _get_connection(database)
        try:
            with conn.cursor() as cursor:
                cursor.execute(query)

                if cursor.description is None:
                    return RedshiftQueryResponse(
                        success=True,
                        data=RedshiftQueryData(
                            columns=[],
                            rows=[],
                            row_count=0,
                            message="Query executed successfully.",
                        ),
                    )

                columns = [desc[0] for desc in cursor.description]
                raw_rows = cursor.fetchall()
                rows: list[dict[str, Any]] = [
                    dict(zip(columns, row, strict=False)) for row in raw_rows
                ]

                return RedshiftQueryResponse(
                    success=True,
                    data=RedshiftQueryData(
                        columns=columns,
                        rows=rows,
                        row_count=len(rows),
                    ),
                )
        finally:
            conn.close()

    except ValueError as e:
        return RedshiftQueryResponse(success=False, error=str(e))
    except redshift_connector.Error as e:
        logger.exception("Redshift query failed")
        return RedshiftQueryResponse(success=False, error=f"Redshift error: {e}")
    except Exception as e:
        logger.exception("Redshift query failed")
        return RedshiftQueryResponse(success=False, error=str(e))
