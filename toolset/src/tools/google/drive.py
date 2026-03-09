"""Google Drive tools for listing, searching, and reading files."""

import asyncio
import io
import logging

from googleapiclient.http import MediaIoBaseDownload

from src.humcp.decorator import tool
from src.tools.google.auth import SCOPES, get_google_service
from src.tools.google.schemas import (
    DriveCreateFolderData,
    DriveCreateFolderResponse,
    DriveFile,
    DriveFileDetailed,
    DriveFileOwner,
    DriveGetFileResponse,
    DriveListData,
    DriveListResponse,
    DriveReadTextFileData,
    DriveReadTextFileResponse,
    DriveSearchData,
    DriveSearchResponse,
)

logger = logging.getLogger("humcp.tools.google.drive")

# Scopes required for Drive operations
DRIVE_READONLY_SCOPES = [SCOPES["drive_readonly"]]
DRIVE_FULL_SCOPES = [SCOPES["drive"]]


def _escape_drive_query(value: str) -> str:
    """Escape special characters in Google Drive query strings.

    Google Drive API query strings use single quotes for string values.
    Backslashes and single quotes need to be escaped.

    Args:
        value: The string value to escape.

    Returns:
        Escaped string safe for use in Drive queries.
    """
    # Escape backslashes first, then single quotes
    return value.replace("\\", "\\\\").replace("'", "\\'")


@tool()
async def google_drive_list(
    folder_id: str = "root",
    max_results: int = 50,
    file_type: str = "",
) -> DriveListResponse:
    """List files in a Google Drive folder.

    Returns files in the specified folder, optionally filtered by type.

    Args:
        folder_id: Folder ID to list (default: "root" for root folder).
        max_results: Maximum number of files to return (default: 50).
        file_type: Optional MIME type filter (e.g., "image", "document").

    Returns:
        List of files with id, name, mime_type, size, modified date, and web_link.
    """
    try:

        def _list():
            service = get_google_service("drive", "v3", DRIVE_READONLY_SCOPES)

            escaped_folder_id = _escape_drive_query(folder_id)
            query = f"'{escaped_folder_id}' in parents and trashed = false"
            if file_type:
                escaped_file_type = _escape_drive_query(file_type)
                query += f" and mimeType contains '{escaped_file_type}'"

            results = (
                service.files()
                .list(
                    q=query,
                    pageSize=max_results,
                    fields="files(id, name, mimeType, size, modifiedTime, webViewLink)",
                    orderBy="modifiedTime desc",
                )
                .execute()
            )

            files = results.get("files", [])
            return [
                DriveFile(
                    id=f["id"],
                    name=f["name"],
                    mime_type=f.get("mimeType", ""),
                    size=f.get("size", ""),
                    modified=f.get("modifiedTime", ""),
                    web_link=f.get("webViewLink", ""),
                )
                for f in files
            ]

        logger.info("drive_list folder_id=%s max_results=%s", folder_id, max_results)
        files = await asyncio.to_thread(_list)
        return DriveListResponse(
            success=True,
            data=DriveListData(files=files, total=len(files)),
        )
    except Exception as e:
        logger.exception("drive_list failed")
        return DriveListResponse(success=False, error=str(e))


@tool()
async def google_drive_search(query: str, max_results: int = 50) -> DriveSearchResponse:
    """Search for files in Google Drive.

    Performs a full-text search across all accessible files.

    Args:
        query: Search query to match against file contents and names.
        max_results: Maximum number of files to return (default: 50).

    Returns:
        List of matching files with metadata including owner information.
    """
    try:

        def _search():
            service = get_google_service("drive", "v3", DRIVE_READONLY_SCOPES)

            escaped_query = _escape_drive_query(query)
            drive_query = f"fullText contains '{escaped_query}' and trashed = false"

            results = (
                service.files()
                .list(
                    q=drive_query,
                    pageSize=max_results,
                    fields="files(id, name, mimeType, size, modifiedTime, webViewLink, owners)",
                    orderBy="modifiedTime desc",
                )
                .execute()
            )

            files = results.get("files", [])
            return [
                DriveFile(
                    id=f["id"],
                    name=f["name"],
                    mime_type=f.get("mimeType", ""),
                    size=f.get("size", ""),
                    modified=f.get("modifiedTime", ""),
                    web_link=f.get("webViewLink", ""),
                    owner=(
                        f.get("owners", [{}])[0].get("emailAddress", "")
                        if f.get("owners")
                        else None
                    ),
                )
                for f in files
            ]

        logger.info("drive_search query=%s", query)
        files = await asyncio.to_thread(_search)
        return DriveSearchResponse(
            success=True,
            data=DriveSearchData(files=files, total=len(files), query=query),
        )
    except Exception as e:
        logger.exception("drive_search failed")
        return DriveSearchResponse(success=False, error=str(e))


@tool()
async def google_drive_get_file(file_id: str) -> DriveGetFileResponse:
    """Get detailed metadata for a file.

    Retrieves comprehensive information about a specific file.

    Args:
        file_id: ID of the file to get metadata for.

    Returns:
        Detailed file metadata including owners, parents, and download link.
    """
    try:

        def _get():
            service = get_google_service("drive", "v3", DRIVE_READONLY_SCOPES)

            file = (
                service.files()
                .get(
                    fileId=file_id,
                    fields="id, name, mimeType, size, createdTime, modifiedTime, "
                    "webViewLink, webContentLink, owners, parents, description",
                )
                .execute()
            )

            return DriveFileDetailed(
                id=file["id"],
                name=file["name"],
                mime_type=file.get("mimeType", ""),
                size=file.get("size", ""),
                created=file.get("createdTime", ""),
                modified=file.get("modifiedTime", ""),
                description=file.get("description", ""),
                web_link=file.get("webViewLink", ""),
                download_link=file.get("webContentLink", ""),
                owners=[
                    DriveFileOwner(
                        name=o.get("displayName"), email=o.get("emailAddress")
                    )
                    for o in file.get("owners", [])
                ],
                parent_folders=file.get("parents", []),
            )

        logger.info("drive_get_file file_id=%s", file_id)
        result = await asyncio.to_thread(_get)
        return DriveGetFileResponse(success=True, data=result)
    except Exception as e:
        logger.exception("drive_get_file failed")
        return DriveGetFileResponse(success=False, error=str(e))


@tool()
async def google_drive_read_text_file(file_id: str) -> DriveReadTextFileResponse:
    """Read the content of a text-based file from Google Drive.

    Supports Google Docs (exported as plain text), Google Sheets (exported as CSV),
    and regular text files.

    Args:
        file_id: ID of the file to read.

    Returns:
        File content with name, mime_type, content text, and length.
    """
    try:

        def _read():
            service = get_google_service("drive", "v3", DRIVE_READONLY_SCOPES)

            file = (
                service.files().get(fileId=file_id, fields="name, mimeType").execute()
            )

            mime_type = file.get("mimeType", "")
            content = ""

            # Handle Google Docs - export as plain text
            if mime_type == "application/vnd.google-apps.document":
                request = service.files().export_media(
                    fileId=file_id, mimeType="text/plain"
                )
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()
                content = fh.getvalue().decode("utf-8")

            # Handle Google Sheets - export as CSV
            elif mime_type == "application/vnd.google-apps.spreadsheet":
                request = service.files().export_media(
                    fileId=file_id, mimeType="text/csv"
                )
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()
                content = fh.getvalue().decode("utf-8")

            # Handle regular files
            else:
                request = service.files().get_media(fileId=file_id)
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()
                try:
                    content = fh.getvalue().decode("utf-8")
                except UnicodeDecodeError:
                    raise ValueError(
                        f"File '{file['name']}' is not a text file"
                    ) from None

            return DriveReadTextFileData(
                name=file["name"],
                mime_type=mime_type,
                content=content,
                length=len(content),
            )

        logger.info("drive_read_text_file file_id=%s", file_id)
        result = await asyncio.to_thread(_read)
        return DriveReadTextFileResponse(success=True, data=result)
    except Exception as e:
        logger.exception("drive_read_text_file failed")
        return DriveReadTextFileResponse(success=False, error=str(e))


@tool()
async def google_drive_create_folder(
    name: str,
    parent_id: str = "root",
) -> DriveCreateFolderResponse:
    """Create a new folder in Google Drive.

    Creates a folder with the specified name under the given parent folder.

    Args:
        name: Name for the new folder.
        parent_id: Parent folder ID (default: "root" for root folder).

    Returns:
        Created folder details including id, name, web_link, and parent_id.
    """
    try:

        def _create():
            service = get_google_service("drive", "v3", DRIVE_FULL_SCOPES)

            file_metadata = {
                "name": name,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [parent_id],
            }

            folder = (
                service.files()
                .create(
                    body=file_metadata,
                    fields="id, name, webViewLink",
                )
                .execute()
            )

            return DriveCreateFolderData(
                id=folder["id"],
                name=folder["name"],
                web_link=folder.get("webViewLink", ""),
                parent_id=parent_id,
            )

        logger.info("drive_create_folder name=%s parent_id=%s", name, parent_id)
        result = await asyncio.to_thread(_create)
        return DriveCreateFolderResponse(success=True, data=result)
    except Exception as e:
        logger.exception("drive_create_folder failed")
        return DriveCreateFolderResponse(success=False, error=str(e))
