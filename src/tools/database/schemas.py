"""Pydantic output schemas for PostgreSQL database tools."""

from typing import Any

from pydantic import BaseModel, Field

from src.humcp.schemas import ToolResponse

# =============================================================================
# Column Information
# =============================================================================


class ColumnInfo(BaseModel):
    """Information about a table column."""

    name: str = Field(..., description="Column name")
    type: str = Field(..., description="Data type")
    nullable: bool = Field(..., description="Whether the column allows NULL values")
    default: str | None = Field(None, description="Default value expression")
    max_length: int | None = Field(None, description="Maximum character length")
    precision: int | None = Field(None, description="Numeric precision")
    scale: int | None = Field(None, description="Numeric scale")


# =============================================================================
# Tool Data Schemas
# =============================================================================


class ExecuteQuerySelectData(BaseModel):
    """Output data for execute_query tool (SELECT queries)."""

    rows: list[dict[str, Any]] = Field(..., description="Query result rows")
    row_count: int = Field(..., description="Number of rows returned")


class ExecuteQueryModifyData(BaseModel):
    """Output data for execute_query tool (INSERT/UPDATE/DELETE queries)."""

    affected_rows: int = Field(..., description="Number of rows affected")
    message: str = Field(..., description="Success message")
    table_contents: str | None = Field(
        default=None, description="Updated table contents as string"
    )


class ListTablesData(BaseModel):
    """Output data for list_tables tool."""

    schema_name: str = Field(
        ..., serialization_alias="schema", description="Database schema name"
    )
    tables: list[str] = Field(..., description="List of table names")
    count: int = Field(..., description="Number of tables")


class DescribeTableData(BaseModel):
    """Output data for describe_table tool."""

    schema_name: str = Field(
        ..., serialization_alias="schema", description="Database schema name"
    )
    table: str = Field(..., description="Table name")
    columns: list[ColumnInfo] = Field(..., description="Column definitions")
    column_count: int = Field(..., description="Number of columns")


# =============================================================================
# Response Wrappers (inheriting from ToolResponse[T])
# =============================================================================


class ExecuteQueryResponse(
    ToolResponse[ExecuteQuerySelectData | ExecuteQueryModifyData]
):
    """Response schema for execute_query tool.

    The data field structure depends on query type:
    - SELECT/WITH: Contains rows and row_count
    - INSERT/UPDATE/DELETE: Contains affected_rows, message, and optionally table_contents
    """

    pass


class ListTablesResponse(ToolResponse[ListTablesData]):
    """Response schema for list_tables tool."""

    pass


class DescribeTableResponse(ToolResponse[DescribeTableData]):
    """Response schema for describe_table tool."""

    pass


# =============================================================================
# DuckDB Schemas
# =============================================================================


class DuckDbQueryData(BaseModel):
    """Output data for duckdb_query tool."""

    columns: list[str] = Field(
        default_factory=list, description="Column names from the result"
    )
    rows: list[dict[str, Any]] = Field(..., description="Query result rows")
    row_count: int = Field(..., description="Number of rows returned")


class DuckDbListTablesData(BaseModel):
    """Output data for duckdb_list_tables tool."""

    tables: list[str] = Field(..., description="List of table names")
    count: int = Field(..., description="Number of tables")
    database_path: str | None = Field(
        None, description="Database file path (None for in-memory)"
    )


class DuckDbReadFileData(BaseModel):
    """Output data for duckdb_read_file tool."""

    file_path: str = Field(..., description="Path to the file that was read")
    columns: list[str] = Field(
        default_factory=list, description="Column names from the file"
    )
    rows: list[dict[str, Any]] = Field(..., description="Data rows from the file")
    row_count: int = Field(..., description="Number of rows returned")


# =============================================================================
# Neo4j Schemas
# =============================================================================


class Neo4jQueryData(BaseModel):
    """Output data for neo4j_query tool."""

    records: list[dict[str, Any]] = Field(..., description="Query result records")
    record_count: int = Field(..., description="Number of records returned")


class Neo4jSchemaData(BaseModel):
    """Output data for neo4j_get_schema tool."""

    labels: list[str] = Field(..., description="Node labels in the database")
    relationship_types: list[str] = Field(
        ..., description="Relationship types in the database"
    )
    schema_visualization: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Schema visualization data from db.schema.visualization()",
    )


# =============================================================================
# SQL (Generic SQLAlchemy) Schemas
# =============================================================================


class SqlQueryData(BaseModel):
    """Output data for sql_query tool."""

    rows: list[dict[str, Any]] = Field(
        default_factory=list, description="Query result rows"
    )
    row_count: int = Field(..., description="Number of rows returned")
    affected_rows: int | None = Field(
        None, description="Number of rows affected (for INSERT/UPDATE/DELETE)"
    )


# =============================================================================
# Redshift Schemas
# =============================================================================


class RedshiftQueryData(BaseModel):
    """Output data for redshift_query tool."""

    columns: list[str] = Field(
        default_factory=list, description="Column names from the result"
    )
    rows: list[dict[str, Any]] = Field(
        default_factory=list, description="Query result rows"
    )
    row_count: int = Field(..., description="Number of rows returned")
    message: str | None = Field(
        default=None, description="Status message for non-SELECT queries"
    )


# =============================================================================
# New Response Wrappers
# =============================================================================


class DuckDbQueryResponse(ToolResponse[DuckDbQueryData]):
    """Response schema for duckdb_query tool."""

    pass


class DuckDbListTablesResponse(ToolResponse[DuckDbListTablesData]):
    """Response schema for duckdb_list_tables tool."""

    pass


class DuckDbReadFileResponse(ToolResponse[DuckDbReadFileData]):
    """Response schema for duckdb_read_file tool."""

    pass


class Neo4jQueryResponse(ToolResponse[Neo4jQueryData]):
    """Response schema for neo4j_query tool."""

    pass


class Neo4jSchemaResponse(ToolResponse[Neo4jSchemaData]):
    """Response schema for neo4j_get_schema tool."""

    pass


class SqlQueryResponse(ToolResponse[SqlQueryData]):
    """Response schema for sql_query tool."""

    pass


class RedshiftQueryResponse(ToolResponse[RedshiftQueryData]):
    """Response schema for redshift_query tool."""

    pass
