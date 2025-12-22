import asyncio
import logging

from fastmcp import FastMCP

from src.tools.google.auth import SCOPES, get_google_service

logger = logging.getLogger("humcp.tools.google.sheets")

SHEETS_READONLY_SCOPES = [SCOPES["sheets_readonly"], SCOPES["drive_readonly"]]
SHEETS_FULL_SCOPES = [SCOPES["sheets"], SCOPES["drive"]]


async def list_spreadsheets(max_results: int = 25) -> dict:
    """List Google Spreadsheets accessible to the user."""
    try:

        def _list():
            service = get_google_service("drive", "v3", SHEETS_READONLY_SCOPES)
            query = (
                "mimeType='application/vnd.google-apps.spreadsheet' and trashed=false"
            )
            results = (
                service.files()
                .list(
                    q=query,
                    pageSize=max_results,
                    fields="files(id, name, modifiedTime, webViewLink)",
                    orderBy="modifiedTime desc",
                )
                .execute()
            )
            files = results.get("files", [])
            return {
                "spreadsheets": [
                    {
                        "id": f["id"],
                        "name": f["name"],
                        "modified": f.get("modifiedTime", ""),
                        "web_link": f.get("webViewLink", ""),
                    }
                    for f in files
                ],
                "total": len(files),
            }

        logger.info("sheets_list_spreadsheets")
        result = await asyncio.to_thread(_list)
        return {"success": True, "data": result}
    except Exception as e:
        logger.exception("sheets_list_spreadsheets failed")
        return {"success": False, "error": str(e)}


async def get_spreadsheet_info(spreadsheet_id: str) -> dict:
    """Get metadata about a spreadsheet."""
    try:

        def _get():
            service = get_google_service("sheets", "v4", SHEETS_READONLY_SCOPES)
            spreadsheet = (
                service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            )
            sheets = spreadsheet.get("sheets", [])
            return {
                "id": spreadsheet["spreadsheetId"],
                "title": spreadsheet.get("properties", {}).get("title", ""),
                "locale": spreadsheet.get("properties", {}).get("locale", ""),
                "sheets": [
                    {
                        "id": s["properties"]["sheetId"],
                        "title": s["properties"]["title"],
                        "index": s["properties"]["index"],
                        "row_count": s["properties"]
                        .get("gridProperties", {})
                        .get("rowCount", 0),
                        "column_count": s["properties"]
                        .get("gridProperties", {})
                        .get("columnCount", 0),
                    }
                    for s in sheets
                ],
                "web_link": spreadsheet.get("spreadsheetUrl", ""),
            }

        logger.info("sheets_get_info id=%s", spreadsheet_id)
        result = await asyncio.to_thread(_get)
        return {"success": True, "data": result}
    except Exception as e:
        logger.exception("sheets_get_info failed")
        return {"success": False, "error": str(e)}


async def read_sheet_values(
    spreadsheet_id: str, range_notation: str = "Sheet1"
) -> dict:
    """Read values from a spreadsheet range."""
    try:

        def _read():
            service = get_google_service("sheets", "v4", SHEETS_READONLY_SCOPES)
            result = (
                service.spreadsheets()
                .values()
                .get(spreadsheetId=spreadsheet_id, range=range_notation)
                .execute()
            )
            values = result.get("values", [])
            return {
                "range": result.get("range", ""),
                "rows": values,
                "row_count": len(values),
                "column_count": max(len(row) for row in values) if values else 0,
            }

        logger.info("sheets_read_values id=%s range=%s", spreadsheet_id, range_notation)
        result = await asyncio.to_thread(_read)
        return {"success": True, "data": result}
    except Exception as e:
        logger.exception("sheets_read_values failed")
        return {"success": False, "error": str(e)}


async def write_sheet_values(
    spreadsheet_id: str,
    range_notation: str,
    values: list,
    input_option: str = "USER_ENTERED",
) -> dict:
    """Write values to a spreadsheet range."""
    try:

        def _write():
            service = get_google_service("sheets", "v4", SHEETS_FULL_SCOPES)
            body = {"values": values}
            result = (
                service.spreadsheets()
                .values()
                .update(
                    spreadsheetId=spreadsheet_id,
                    range=range_notation,
                    valueInputOption=input_option,
                    body=body,
                )
                .execute()
            )
            return {
                "updated_range": result.get("updatedRange", ""),
                "updated_rows": result.get("updatedRows", 0),
                "updated_columns": result.get("updatedColumns", 0),
                "updated_cells": result.get("updatedCells", 0),
            }

        logger.info("sheets_write_values id=%s range=%s", spreadsheet_id, range_notation)
        result = await asyncio.to_thread(_write)
        return {"success": True, "data": result}
    except Exception as e:
        logger.exception("sheets_write_values failed")
        return {"success": False, "error": str(e)}


async def append_sheet_values(
    spreadsheet_id: str,
    range_notation: str,
    values: list,
    input_option: str = "USER_ENTERED",
) -> dict:
    """Append values to a spreadsheet (adds rows after existing data)."""
    try:

        def _append():
            service = get_google_service("sheets", "v4", SHEETS_FULL_SCOPES)
            body = {"values": values}
            result = (
                service.spreadsheets()
                .values()
                .append(
                    spreadsheetId=spreadsheet_id,
                    range=range_notation,
                    valueInputOption=input_option,
                    insertDataOption="INSERT_ROWS",
                    body=body,
                )
                .execute()
            )
            updates = result.get("updates", {})
            return {
                "updated_range": updates.get("updatedRange", ""),
                "updated_rows": updates.get("updatedRows", 0),
                "updated_cells": updates.get("updatedCells", 0),
            }

        logger.info("sheets_append_values id=%s range=%s", spreadsheet_id, range_notation)
        result = await asyncio.to_thread(_append)
        return {"success": True, "data": result}
    except Exception as e:
        logger.exception("sheets_append_values failed")
        return {"success": False, "error": str(e)}


async def create_spreadsheet(title: str, sheet_names: list = None) -> dict:
    """Create a new Google Spreadsheet."""
    try:

        def _create():
            service = get_google_service("sheets", "v4", SHEETS_FULL_SCOPES)

            body = {"properties": {"title": title}}

            if sheet_names:
                body["sheets"] = [
                    {"properties": {"title": name}} for name in sheet_names
                ]

            spreadsheet = service.spreadsheets().create(body=body).execute()

            return {
                "id": spreadsheet["spreadsheetId"],
                "title": spreadsheet.get("properties", {}).get("title", ""),
                "sheets": [
                    s["properties"]["title"] for s in spreadsheet.get("sheets", [])
                ],
                "web_link": spreadsheet.get("spreadsheetUrl", ""),
            }

        logger.info("sheets_create_spreadsheet title=%s", title)
        result = await asyncio.to_thread(_create)
        return {"success": True, "data": result}
    except Exception as e:
        logger.exception("sheets_create_spreadsheet failed")
        return {"success": False, "error": str(e)}


async def add_sheet(spreadsheet_id: str, sheet_title: str) -> dict:
    """Add a new sheet to an existing spreadsheet."""
    try:

        def _add():
            service = get_google_service("sheets", "v4", SHEETS_FULL_SCOPES)
            request = {"addSheet": {"properties": {"title": sheet_title}}}
            result = (
                service.spreadsheets()
                .batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": [request]})
                .execute()
            )
            new_sheet = result.get("replies", [{}])[0].get("addSheet", {})
            return {
                "sheet_id": new_sheet.get("properties", {}).get("sheetId"),
                "title": new_sheet.get("properties", {}).get("title"),
                "spreadsheet_id": spreadsheet_id,
            }

        logger.info("sheets_add_sheet id=%s title=%s", spreadsheet_id, sheet_title)
        result = await asyncio.to_thread(_add)
        return {"success": True, "data": result}
    except Exception as e:
        logger.exception("sheets_add_sheet failed")
        return {"success": False, "error": str(e)}


async def clear_sheet_values(spreadsheet_id: str, range_notation: str) -> dict:
    """Clear values from a spreadsheet range."""
    try:

        def _clear():
            service = get_google_service("sheets", "v4", SHEETS_FULL_SCOPES)
            result = (
                service.spreadsheets()
                .values()
                .clear(spreadsheetId=spreadsheet_id, range=range_notation, body={})
                .execute()
            )
            return {
                "cleared_range": result.get("clearedRange", ""),
                "spreadsheet_id": spreadsheet_id,
            }

        logger.info("sheets_clear_values id=%s range=%s", spreadsheet_id, range_notation)
        result = await asyncio.to_thread(_clear)
        return {"success": True, "data": result}
    except Exception as e:
        logger.exception("sheets_clear_values failed")
        return {"success": False, "error": str(e)}


def register_tools(mcp: FastMCP) -> None:
    """Register all Google Sheets tools with the MCP server."""
    mcp.tool(name="sheets_list_spreadsheets")(list_spreadsheets)
    mcp.tool(name="sheets_get_info")(get_spreadsheet_info)
    mcp.tool(name="sheets_read_values")(read_sheet_values)
    mcp.tool(name="sheets_write_values")(write_sheet_values)
    mcp.tool(name="sheets_append_values")(append_sheet_values)
    mcp.tool(name="sheets_create_spreadsheet")(create_spreadsheet)
    mcp.tool(name="sheets_add_sheet")(add_sheet)
    mcp.tool(name="sheets_clear_values")(clear_sheet_values)
