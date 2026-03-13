"""Pydantic output schemas for Google Sheets tools."""

from typing import Any

from pydantic import BaseModel, Field

from src.humcp.schemas import ToolResponse


class SpreadsheetInfo(BaseModel):
    """Basic spreadsheet information."""

    id: str = Field(..., description="Spreadsheet ID")
    name: str = Field(..., description="Spreadsheet name")
    modified: str = Field("", description="Last modified date")
    web_link: str = Field("", description="Web view link")


class SheetInfo(BaseModel):
    """Information about a sheet within a spreadsheet."""

    id: int = Field(..., description="Sheet ID")
    title: str = Field(..., description="Sheet title")
    index: int = Field(..., description="Sheet index")
    row_count: int = Field(0, description="Number of rows")
    column_count: int = Field(0, description="Number of columns")


class SheetsListData(BaseModel):
    """Output data for google_sheets_list_spreadsheets tool."""

    spreadsheets: list[SpreadsheetInfo] = Field(..., description="List of spreadsheets")
    total: int = Field(..., description="Total number of spreadsheets")


class SheetsGetInfoData(BaseModel):
    """Output data for google_sheets_get_info tool."""

    id: str = Field(..., description="Spreadsheet ID")
    title: str = Field(..., description="Spreadsheet title")
    locale: str = Field("", description="Spreadsheet locale")
    sheets: list[SheetInfo] = Field(..., description="List of sheets")
    web_link: str = Field("", description="Web view link")


class SheetsReadValuesData(BaseModel):
    """Output data for google_sheets_read_values tool."""

    range: str = Field(..., description="Range that was read")
    rows: list[list[Any]] = Field(..., description="2D array of cell values")
    row_count: int = Field(..., description="Number of rows")
    column_count: int = Field(..., description="Number of columns")


class SheetsWriteValuesData(BaseModel):
    """Output data for google_sheets_write_values tool."""

    updated_range: str = Field(..., description="Range that was updated")
    updated_rows: int = Field(0, description="Number of rows updated")
    updated_columns: int = Field(0, description="Number of columns updated")
    updated_cells: int = Field(0, description="Total cells updated")


class SheetsAppendValuesData(BaseModel):
    """Output data for google_sheets_append_values tool."""

    updated_range: str = Field(..., description="Range that was appended to")
    updated_rows: int = Field(0, description="Number of rows added")
    updated_cells: int = Field(0, description="Total cells added")


class SheetsCreateData(BaseModel):
    """Output data for google_sheets_create_spreadsheet tool."""

    id: str = Field(..., description="Created spreadsheet ID")
    title: str = Field(..., description="Spreadsheet title")
    sheets: list[str] = Field(..., description="Sheet names")
    web_link: str = Field("", description="Web view link")


class SheetsAddSheetData(BaseModel):
    """Output data for google_sheets_add_sheet tool."""

    sheet_id: int | None = Field(None, description="New sheet ID")
    title: str | None = Field(None, description="Sheet title")
    spreadsheet_id: str = Field(..., description="Parent spreadsheet ID")


class SheetsClearValuesData(BaseModel):
    """Output data for google_sheets_clear_values tool."""

    cleared_range: str = Field(..., description="Range that was cleared")
    spreadsheet_id: str = Field(..., description="Spreadsheet ID")


# Sheets Responses
class SheetsListResponse(ToolResponse[SheetsListData]):
    """Response for google_sheets_list_spreadsheets tool."""

    pass


class SheetsGetInfoResponse(ToolResponse[SheetsGetInfoData]):
    """Response for google_sheets_get_info tool."""

    pass


class SheetsReadValuesResponse(ToolResponse[SheetsReadValuesData]):
    """Response for google_sheets_read_values tool."""

    pass


class SheetsWriteValuesResponse(ToolResponse[SheetsWriteValuesData]):
    """Response for google_sheets_write_values tool."""

    pass


class SheetsAppendValuesResponse(ToolResponse[SheetsAppendValuesData]):
    """Response for google_sheets_append_values tool."""

    pass


class SheetsCreateResponse(ToolResponse[SheetsCreateData]):
    """Response for google_sheets_create_spreadsheet tool."""

    pass


class SheetsAddSheetResponse(ToolResponse[SheetsAddSheetData]):
    """Response for google_sheets_add_sheet tool."""

    pass


class SheetsClearValuesResponse(ToolResponse[SheetsClearValuesData]):
    """Response for google_sheets_clear_values tool."""

    pass
