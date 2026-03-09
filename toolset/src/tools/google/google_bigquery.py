"""Google BigQuery tools for querying and listing datasets and tables."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from src.humcp.decorator import tool
from src.tools.google.schemas.bigquery import (
    BigQueryDatasetInfo,
    BigQueryListDatasetsData,
    BigQueryListDatasetsResponse,
    BigQueryListTablesData,
    BigQueryListTablesResponse,
    BigQueryQueryData,
    BigQueryQueryResponse,
    BigQueryTableInfo,
)

try:
    from google.cloud import bigquery
except ImportError as err:
    raise ImportError(
        "google-cloud-bigquery is required for BigQuery tools. "
        "Install with: pip install google-cloud-bigquery"
    ) from err

logger = logging.getLogger("humcp.tools.google.bigquery")


def _get_client(project_id: str | None = None) -> bigquery.Client:
    """Create a BigQuery client.

    Uses GOOGLE_APPLICATION_CREDENTIALS environment variable for authentication.

    Args:
        project_id: Optional Google Cloud project ID override.

    Returns:
        An authenticated BigQuery client.
    """
    resolved_project = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
    return bigquery.Client(project=resolved_project)


def _clean_sql(sql: str) -> str:
    """Clean SQL query by normalizing whitespace.

    Replaces newlines with spaces to prevent line comments from swallowing
    subsequent SQL statements.

    Args:
        sql: The SQL query to clean.

    Returns:
        Cleaned SQL query string.
    """
    return sql.replace("\\n", " ").replace("\n", " ")


@tool()
async def google_bigquery_query(
    query: str,
    project_id: str | None = None,
) -> BigQueryQueryResponse:
    """Execute a SQL query against Google BigQuery.

    Runs a BigQuery SQL query and returns the results as a list of dictionaries.

    Args:
        query: The BigQuery SQL query to execute.
        project_id: Optional Google Cloud project ID. Falls back to GOOGLE_CLOUD_PROJECT env var.

    Returns:
        Query results with rows and metadata.
    """
    try:
        logger.info("Executing BigQuery query: %s", query)

        def _execute() -> dict[str, Any]:
            client = _get_client(project_id)
            cleaned_query = _clean_sql(query)
            query_job = client.query(cleaned_query)
            results = query_job.result()

            rows = [dict(row) for row in results]
            return {
                "rows": rows,
                "row_count": len(rows),
                "total_bytes_processed": query_job.total_bytes_processed,
            }

        result = await asyncio.to_thread(_execute)

        return BigQueryQueryResponse(
            success=True,
            data=BigQueryQueryData(
                rows=result["rows"],
                row_count=result["row_count"],
                total_bytes_processed=result["total_bytes_processed"],
            ),
        )
    except Exception as e:
        logger.exception("BigQuery query failed")
        return BigQueryQueryResponse(success=False, error=f"BigQuery error: {e}")


@tool()
async def google_bigquery_list_datasets(
    project_id: str | None = None,
) -> BigQueryListDatasetsResponse:
    """List all datasets in a Google BigQuery project.

    Args:
        project_id: Optional Google Cloud project ID. Falls back to GOOGLE_CLOUD_PROJECT env var.

    Returns:
        List of datasets in the project.
    """
    try:
        logger.info("Listing BigQuery datasets for project: %s", project_id)

        def _list() -> dict[str, Any]:
            client = _get_client(project_id)
            datasets = list(client.list_datasets())
            resolved = client.project
            return {
                "datasets": [
                    {
                        "dataset_id": ds.dataset_id,
                        "project": ds.project,
                        "friendly_name": ds.friendly_name,
                        "description": ds.description,
                    }
                    for ds in datasets
                ],
                "project_id": resolved,
            }

        result = await asyncio.to_thread(_list)

        datasets = [
            BigQueryDatasetInfo(
                dataset_id=ds["dataset_id"],
                project=ds["project"],
                friendly_name=ds["friendly_name"],
                description=ds["description"],
            )
            for ds in result["datasets"]
        ]

        return BigQueryListDatasetsResponse(
            success=True,
            data=BigQueryListDatasetsData(
                datasets=datasets,
                count=len(datasets),
                project_id=result["project_id"],
            ),
        )
    except Exception as e:
        logger.exception("BigQuery list datasets failed")
        return BigQueryListDatasetsResponse(success=False, error=f"BigQuery error: {e}")


@tool()
async def google_bigquery_list_tables(
    dataset_id: str,
    project_id: str | None = None,
) -> BigQueryListTablesResponse:
    """List all tables in a Google BigQuery dataset.

    Args:
        dataset_id: The ID of the dataset to list tables from.
        project_id: Optional Google Cloud project ID. Falls back to GOOGLE_CLOUD_PROJECT env var.

    Returns:
        List of tables in the dataset.
    """
    try:
        logger.info(
            "Listing BigQuery tables for dataset: %s project: %s",
            dataset_id,
            project_id,
        )

        def _list() -> dict[str, Any]:
            client = _get_client(project_id)
            tables = list(client.list_tables(dataset_id))
            resolved = client.project
            return {
                "tables": [
                    {
                        "table_id": t.table_id,
                        "dataset_id": t.dataset_id,
                        "project": t.project,
                        "table_type": t.table_type or "",
                    }
                    for t in tables
                ],
                "project_id": resolved,
            }

        result = await asyncio.to_thread(_list)

        tables = [
            BigQueryTableInfo(
                table_id=t["table_id"],
                dataset_id=t["dataset_id"],
                project=t["project"],
                table_type=t["table_type"],
            )
            for t in result["tables"]
        ]

        return BigQueryListTablesResponse(
            success=True,
            data=BigQueryListTablesData(
                tables=tables,
                count=len(tables),
                project_id=result["project_id"],
                dataset_id=dataset_id,
            ),
        )
    except Exception as e:
        logger.exception("BigQuery list tables failed")
        return BigQueryListTablesResponse(success=False, error=f"BigQuery error: {e}")
