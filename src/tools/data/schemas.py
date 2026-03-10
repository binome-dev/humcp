"""Pydantic output schemas for CSV and pandas data tools."""

from typing import Any

from pydantic import BaseModel, Field

from src.humcp.schemas import ToolResponse

# =============================================================================
# CSV Tool Data Schemas
# =============================================================================


class ListCSVFilesData(BaseModel):
    """Output data for list_csv_files tool."""

    files: list[str] = Field(..., description="List of available CSV file names")
    count: int = Field(..., description="Number of available CSV files")


class ReadCSVFileData(BaseModel):
    """Output data for read_csv_file tool."""

    rows: list[dict[str, Any]] = Field(..., description="CSV rows as dictionaries")
    row_count: int = Field(..., description="Number of rows returned")


class GetCSVColumnsData(BaseModel):
    """Output data for get_csv_columns tool."""

    columns: list[str] = Field(..., description="List of column names")
    column_count: int = Field(..., description="Number of columns")


class QueryCSVFileData(BaseModel):
    """Output data for query_csv_file tool."""

    rows: list[dict[str, Any]] = Field(..., description="Query result rows")
    row_count: int = Field(..., description="Number of rows returned")
    columns: list[str] = Field(..., description="Column names in result")


class DescribeCSVFileData(BaseModel):
    """Output data for describe_csv_file tool."""

    file_name: str = Field(..., description="Name of the CSV file")
    file_size_bytes: int = Field(..., description="File size in bytes")
    columns: list[str] = Field(..., description="List of column names")
    column_count: int = Field(..., description="Number of columns")
    row_count: int = Field(..., description="Approximate number of rows (up to 1000)")
    sample_rows: list[dict[str, Any]] = Field(..., description="First 5 sample rows")


class AddCSVFileData(BaseModel):
    """Output data for add_csv_file tool."""

    message: str = Field(..., description="Success message")
    file_name: str = Field(..., description="Name of the added file (stem)")


class RemoveCSVFileData(BaseModel):
    """Output data for remove_csv_file tool."""

    message: str = Field(..., description="Success message")


# =============================================================================
# CSV Response Wrappers
# =============================================================================


class ListCSVFilesResponse(ToolResponse[ListCSVFilesData]):
    """Response schema for list_csv_files tool."""

    pass


class ReadCSVFileResponse(ToolResponse[ReadCSVFileData]):
    """Response schema for read_csv_file tool."""

    pass


class GetCSVColumnsResponse(ToolResponse[GetCSVColumnsData]):
    """Response schema for get_csv_columns tool."""

    pass


class QueryCSVFileResponse(ToolResponse[QueryCSVFileData]):
    """Response schema for query_csv_file tool."""

    pass


class DescribeCSVFileResponse(ToolResponse[DescribeCSVFileData]):
    """Response schema for describe_csv_file tool."""

    pass


class AddCSVFileResponse(ToolResponse[AddCSVFileData]):
    """Response schema for add_csv_file tool."""

    pass


class RemoveCSVFileResponse(ToolResponse[RemoveCSVFileData]):
    """Response schema for remove_csv_file tool."""

    pass


# =============================================================================
# Pandas DataFrame Tool Data Schemas
# =============================================================================


class CreateDataFrameData(BaseModel):
    """Output data for create_pandas_dataframe tool."""

    name: str = Field(..., description="Name assigned to the DataFrame")
    shape: tuple[int, int] = Field(..., description="DataFrame shape (rows, columns)")
    columns: list[str] = Field(..., description="List of column names")
    dtypes: dict[str, str] = Field(..., description="Column data types")
    memory_usage: int = Field(..., description="Memory usage in bytes")


class DataFrameOperationData(BaseModel):
    """Output data for run_dataframe_operation tool."""

    operation: str = Field(..., description="Operation that was performed")
    dataframe: str = Field(..., description="Name of the DataFrame")
    result: str = Field(..., description="Operation result as string")


class DataFrameInfo(BaseModel):
    """Information about a stored DataFrame."""

    name: str = Field(..., description="DataFrame name")
    shape: tuple[int, int] = Field(..., description="DataFrame shape")
    columns: list[str] = Field(..., description="Column names")
    memory_usage_bytes: int = Field(..., description="Memory usage in bytes")


class DataFrameDetailedInfo(BaseModel):
    """Detailed information about a DataFrame."""

    name: str = Field(..., description="DataFrame name")
    shape: tuple[int, int] = Field(..., description="DataFrame shape")
    columns: list[str] = Field(..., description="Column names")
    dtypes: dict[str, str] = Field(..., description="Column data types")
    memory_usage_bytes: int = Field(..., description="Memory usage in bytes")
    null_counts: dict[str, int] = Field(..., description="Null counts per column")
    sample_data: list[dict[str, Any]] = Field(..., description="Sample rows")


class DeleteDataFrameData(BaseModel):
    """Output data for delete_dataframe tool."""

    message: str = Field(..., description="Success message")


class ExportDataFrameData(BaseModel):
    """Output data for export_dataframe tool."""

    message: str = Field(..., description="Success message")
    output: str = Field(..., description="Output path or location")
    function: str = Field(..., description="Export function used")


# =============================================================================
# Pandas Response Wrappers
# =============================================================================


class CreateDataFrameResponse(ToolResponse[CreateDataFrameData]):
    """Response schema for create_pandas_dataframe tool."""

    pass


class DataFrameOperationResponse(ToolResponse[DataFrameOperationData]):
    """Response schema for run_dataframe_operation tool."""

    pass


class ListDataFramesResponse(ToolResponse[list[DataFrameInfo]]):
    """Response schema for list_dataframes tool."""

    pass


class GetDataFrameInfoResponse(ToolResponse[DataFrameDetailedInfo]):
    """Response schema for get_dataframe_info tool."""

    pass


class DeleteDataFrameResponse(ToolResponse[DeleteDataFrameData]):
    """Response schema for delete_dataframe tool."""

    pass


class ExportDataFrameResponse(ToolResponse[ExportDataFrameData]):
    """Response schema for export_dataframe tool."""

    pass
