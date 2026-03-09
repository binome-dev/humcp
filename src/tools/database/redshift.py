"""Amazon Redshift database tools for query execution."""

from __future__ import annotations

import logging
import os
from typing import Any

from src.humcp.credentials import resolve_credential
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


def _get_connection(
    host: str,
    user: str,
    password: str,
    db: str,
) -> redshift_connector.Connection:
    """Create a Redshift connection with the provided credentials.

    Args:
        host: Redshift cluster host.
        user: Database username.
        password: Database password.
        db: Database name.

    Returns:
        A Redshift connection instance.
    """
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

        host = await resolve_credential("REDSHIFT_HOST")
        user = await resolve_credential("REDSHIFT_USER")
        password = await resolve_credential("REDSHIFT_PASSWORD")
        db = database or await resolve_credential("REDSHIFT_DATABASE")

        if not host:
            return RedshiftQueryResponse(
                success=False, error="REDSHIFT_HOST is required."
            )
        if not user:
            return RedshiftQueryResponse(
                success=False, error="REDSHIFT_USER is required."
            )
        if not password:
            return RedshiftQueryResponse(
                success=False, error="REDSHIFT_PASSWORD is required."
            )
        if not db:
            return RedshiftQueryResponse(
                success=False,
                error="Database name is required. Provide database parameter or set REDSHIFT_DATABASE.",
            )

        logger.info("Executing Redshift query: %s", query)

        conn = _get_connection(host, user, password, db)
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
