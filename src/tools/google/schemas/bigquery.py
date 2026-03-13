"""Pydantic output schemas for Google BigQuery tools."""

from typing import Any

from pydantic import BaseModel, Field

from src.humcp.schemas import ToolResponse

# =============================================================================
# BigQuery Query Schemas
# =============================================================================


class BigQueryQueryData(BaseModel):
    """Output data for google_bigquery_query tool."""

    rows: list[dict[str, Any]] = Field(
        default_factory=list, description="Query result rows"
    )
    row_count: int = Field(..., description="Number of rows returned")
    total_bytes_processed: int | None = Field(
        None, description="Total bytes processed by the query"
    )


# =============================================================================
# BigQuery List Datasets Schemas
# =============================================================================


class BigQueryDatasetInfo(BaseModel):
    """Information about a BigQuery dataset."""

    dataset_id: str = Field(..., description="Dataset ID")
    project: str = Field(..., description="Project ID")
    friendly_name: str | None = Field(None, description="Dataset display name")
    description: str | None = Field(None, description="Dataset description")


class BigQueryListDatasetsData(BaseModel):
    """Output data for google_bigquery_list_datasets tool."""

    datasets: list[BigQueryDatasetInfo] = Field(..., description="List of datasets")
    count: int = Field(..., description="Number of datasets")
    project_id: str = Field(..., description="Google Cloud project ID")


# =============================================================================
# BigQuery List Tables Schemas
# =============================================================================


class BigQueryTableInfo(BaseModel):
    """Information about a BigQuery table."""

    table_id: str = Field(..., description="Table ID")
    dataset_id: str = Field(..., description="Dataset ID")
    project: str = Field(..., description="Project ID")
    table_type: str = Field("", description="Table type (TABLE, VIEW, etc.)")


class BigQueryListTablesData(BaseModel):
    """Output data for google_bigquery_list_tables tool."""

    tables: list[BigQueryTableInfo] = Field(..., description="List of tables")
    count: int = Field(..., description="Number of tables")
    project_id: str = Field(..., description="Google Cloud project ID")
    dataset_id: str = Field(..., description="Dataset ID")


# =============================================================================
# BigQuery Table Schema Schemas
# =============================================================================


class BigQueryFieldInfo(BaseModel):
    """Information about a single column/field in a BigQuery table."""

    name: str = Field(..., description="Field name")
    field_type: str = Field(..., description="Field data type (STRING, INTEGER, etc.)")
    mode: str = Field(
        "NULLABLE", description="Field mode (NULLABLE, REQUIRED, REPEATED)"
    )
    description: str = Field("", description="Field description")
    fields: list["BigQueryFieldInfo"] = Field(
        default_factory=list, description="Nested fields for RECORD types"
    )


class BigQueryTableSchemaData(BaseModel):
    """Output data for google_bigquery_get_table_schema tool."""

    project_id: str = Field(..., description="Google Cloud project ID")
    dataset_id: str = Field(..., description="Dataset ID")
    table_id: str = Field(..., description="Table ID")
    fields: list[BigQueryFieldInfo] = Field(
        ..., description="List of table fields/columns"
    )
    total_fields: int = Field(..., description="Total number of top-level fields")
    num_rows: int | None = Field(None, description="Number of rows in the table")
    num_bytes: int | None = Field(None, description="Size of the table in bytes")
    table_type: str = Field("", description="Table type (TABLE, VIEW, etc.)")
    description: str = Field("", description="Table description")


# =============================================================================
# Response Wrappers
# =============================================================================


class BigQueryQueryResponse(ToolResponse[BigQueryQueryData]):
    """Response schema for google_bigquery_query tool."""

    pass


class BigQueryListDatasetsResponse(ToolResponse[BigQueryListDatasetsData]):
    """Response schema for google_bigquery_list_datasets tool."""

    pass


class BigQueryListTablesResponse(ToolResponse[BigQueryListTablesData]):
    """Response schema for google_bigquery_list_tables tool."""

    pass


class BigQueryTableSchemaResponse(ToolResponse[BigQueryTableSchemaData]):
    """Response schema for google_bigquery_get_table_schema tool."""

    pass
