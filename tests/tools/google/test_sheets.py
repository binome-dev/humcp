from unittest.mock import MagicMock, patch

import pytest

from src.tools.google.sheets import (
    add_sheet,
    append_sheet_values,
    clear_sheet_values,
    create_spreadsheet,
    get_spreadsheet_info,
    list_spreadsheets,
    read_sheet_values,
    write_sheet_values,
)


@pytest.fixture
def mock_sheets_service():
    with patch("src.tools.google.sheets.get_google_service") as mock:
        service = MagicMock()
        mock.return_value = service
        yield service


class TestListSpreadsheets:
    @pytest.mark.asyncio
    async def test_list_spreadsheets_success(self, mock_sheets_service):
        mock_sheets_service.files().list().execute.return_value = {
            "files": [
                {
                    "id": "sheet1",
                    "name": "Budget 2024",
                    "modifiedTime": "2024-01-01T00:00:00Z",
                    "webViewLink": "https://docs.google.com/spreadsheets/d/sheet1",
                }
            ]
        }

        result = await list_spreadsheets()
        assert result["success"] is True
        assert result["data"]["total"] == 1
        assert result["data"]["spreadsheets"][0]["id"] == "sheet1"
        assert result["data"]["spreadsheets"][0]["name"] == "Budget 2024"

    @pytest.mark.asyncio
    async def test_list_spreadsheets_empty(self, mock_sheets_service):
        mock_sheets_service.files().list().execute.return_value = {"files": []}

        result = await list_spreadsheets()
        assert result["success"] is True
        assert result["data"]["total"] == 0

    @pytest.mark.asyncio
    async def test_list_spreadsheets_error(self, mock_sheets_service):
        mock_sheets_service.files().list().execute.side_effect = Exception("API error")

        result = await list_spreadsheets()
        assert result["success"] is False
        assert "API error" in result["error"]


class TestGetSpreadsheetInfo:
    @pytest.mark.asyncio
    async def test_get_spreadsheet_info_success(self, mock_sheets_service):
        mock_sheets_service.spreadsheets().get().execute.return_value = {
            "spreadsheetId": "sheet1",
            "properties": {"title": "My Spreadsheet", "locale": "en_US"},
            "spreadsheetUrl": "https://docs.google.com/spreadsheets/d/sheet1",
            "sheets": [
                {
                    "properties": {
                        "sheetId": 0,
                        "title": "Sheet1",
                        "index": 0,
                        "gridProperties": {"rowCount": 1000, "columnCount": 26},
                    }
                }
            ],
        }

        result = await get_spreadsheet_info("sheet1")
        assert result["success"] is True
        assert result["data"]["id"] == "sheet1"
        assert result["data"]["title"] == "My Spreadsheet"
        assert len(result["data"]["sheets"]) == 1
        assert result["data"]["sheets"][0]["title"] == "Sheet1"

    @pytest.mark.asyncio
    async def test_get_spreadsheet_info_error(self, mock_sheets_service):
        mock_sheets_service.spreadsheets().get().execute.side_effect = Exception(
            "Not found"
        )

        result = await get_spreadsheet_info("nonexistent")
        assert result["success"] is False


class TestReadSheetValues:
    @pytest.mark.asyncio
    async def test_read_sheet_values_success(self, mock_sheets_service):
        mock_sheets_service.spreadsheets().values().get().execute.return_value = {
            "range": "Sheet1!A1:C3",
            "values": [
                ["Name", "Age", "City"],
                ["Alice", "30", "NYC"],
                ["Bob", "25", "LA"],
            ],
        }

        result = await read_sheet_values("sheet1", "Sheet1!A1:C3")
        assert result["success"] is True
        assert result["data"]["row_count"] == 3
        assert result["data"]["column_count"] == 3
        assert result["data"]["rows"][0] == ["Name", "Age", "City"]

    @pytest.mark.asyncio
    async def test_read_sheet_values_empty(self, mock_sheets_service):
        mock_sheets_service.spreadsheets().values().get().execute.return_value = {
            "range": "Sheet1",
            "values": [],
        }

        result = await read_sheet_values("sheet1")
        assert result["success"] is True
        assert result["data"]["row_count"] == 0

    @pytest.mark.asyncio
    async def test_read_sheet_values_error(self, mock_sheets_service):
        mock_sheets_service.spreadsheets().values().get().execute.side_effect = (
            Exception("Invalid range")
        )

        result = await read_sheet_values("sheet1", "Invalid!")
        assert result["success"] is False


class TestWriteSheetValues:
    @pytest.mark.asyncio
    async def test_write_sheet_values_success(self, mock_sheets_service):
        mock_sheets_service.spreadsheets().values().update().execute.return_value = {
            "updatedRange": "Sheet1!A1:B2",
            "updatedRows": 2,
            "updatedColumns": 2,
            "updatedCells": 4,
        }

        result = await write_sheet_values(
            "sheet1", "Sheet1!A1:B2", [["A", "B"], ["C", "D"]]
        )
        assert result["success"] is True
        assert result["data"]["updated_cells"] == 4
        assert result["data"]["updated_rows"] == 2

    @pytest.mark.asyncio
    async def test_write_sheet_values_error(self, mock_sheets_service):
        mock_sheets_service.spreadsheets().values().update().execute.side_effect = (
            Exception("Permission denied")
        )

        result = await write_sheet_values("sheet1", "Sheet1!A1", [["data"]])
        assert result["success"] is False


class TestAppendSheetValues:
    @pytest.mark.asyncio
    async def test_append_sheet_values_success(self, mock_sheets_service):
        mock_sheets_service.spreadsheets().values().append().execute.return_value = {
            "updates": {
                "updatedRange": "Sheet1!A4:B4",
                "updatedRows": 1,
                "updatedCells": 2,
            }
        }

        result = await append_sheet_values("sheet1", "Sheet1", [["New", "Row"]])
        assert result["success"] is True
        assert result["data"]["updated_rows"] == 1

    @pytest.mark.asyncio
    async def test_append_sheet_values_error(self, mock_sheets_service):
        mock_sheets_service.spreadsheets().values().append().execute.side_effect = (
            Exception("Quota exceeded")
        )

        result = await append_sheet_values("sheet1", "Sheet1", [["data"]])
        assert result["success"] is False


class TestCreateSpreadsheet:
    @pytest.mark.asyncio
    async def test_create_spreadsheet_success(self, mock_sheets_service):
        mock_sheets_service.spreadsheets().create().execute.return_value = {
            "spreadsheetId": "new_sheet",
            "properties": {"title": "New Spreadsheet"},
            "spreadsheetUrl": "https://docs.google.com/spreadsheets/d/new_sheet",
            "sheets": [{"properties": {"title": "Sheet1"}}],
        }

        result = await create_spreadsheet("New Spreadsheet")
        assert result["success"] is True
        assert result["data"]["id"] == "new_sheet"
        assert result["data"]["title"] == "New Spreadsheet"

    @pytest.mark.asyncio
    async def test_create_spreadsheet_with_sheets(self, mock_sheets_service):
        mock_sheets_service.spreadsheets().create().execute.return_value = {
            "spreadsheetId": "new_sheet",
            "properties": {"title": "Multi Sheet"},
            "spreadsheetUrl": "https://docs.google.com/spreadsheets/d/new_sheet",
            "sheets": [
                {"properties": {"title": "Data"}},
                {"properties": {"title": "Summary"}},
            ],
        }

        result = await create_spreadsheet("Multi Sheet", sheet_names=["Data", "Summary"])
        assert result["success"] is True
        assert len(result["data"]["sheets"]) == 2

    @pytest.mark.asyncio
    async def test_create_spreadsheet_error(self, mock_sheets_service):
        mock_sheets_service.spreadsheets().create().execute.side_effect = Exception(
            "Creation failed"
        )

        result = await create_spreadsheet("Test")
        assert result["success"] is False


class TestAddSheet:
    @pytest.mark.asyncio
    async def test_add_sheet_success(self, mock_sheets_service):
        mock_sheets_service.spreadsheets().batchUpdate().execute.return_value = {
            "replies": [{"addSheet": {"properties": {"sheetId": 123, "title": "New Tab"}}}]
        }

        result = await add_sheet("sheet1", "New Tab")
        assert result["success"] is True
        assert result["data"]["sheet_id"] == 123
        assert result["data"]["title"] == "New Tab"

    @pytest.mark.asyncio
    async def test_add_sheet_error(self, mock_sheets_service):
        mock_sheets_service.spreadsheets().batchUpdate().execute.side_effect = (
            Exception("Duplicate name")
        )

        result = await add_sheet("sheet1", "Sheet1")
        assert result["success"] is False


class TestClearSheetValues:
    @pytest.mark.asyncio
    async def test_clear_sheet_values_success(self, mock_sheets_service):
        mock_sheets_service.spreadsheets().values().clear().execute.return_value = {
            "clearedRange": "Sheet1!A1:Z100"
        }

        result = await clear_sheet_values("sheet1", "Sheet1!A1:Z100")
        assert result["success"] is True
        assert result["data"]["cleared_range"] == "Sheet1!A1:Z100"

    @pytest.mark.asyncio
    async def test_clear_sheet_values_error(self, mock_sheets_service):
        mock_sheets_service.spreadsheets().values().clear().execute.side_effect = (
            Exception("Invalid range")
        )

        result = await clear_sheet_values("sheet1", "Invalid!")
        assert result["success"] is False
