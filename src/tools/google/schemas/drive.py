"""Pydantic output schemas for Google Drive tools."""

from pydantic import BaseModel, Field

from src.humcp.schemas import ToolResponse


class DriveFile(BaseModel):
    """Information about a Google Drive file."""

    id: str = Field(..., description="File ID")
    name: str = Field(..., description="File name")
    mime_type: str = Field("", description="MIME type of the file")
    size: str = Field("", description="File size in bytes")
    modified: str = Field("", description="Last modified date")
    web_link: str = Field("", description="Web view link")
    owner: str | None = Field(None, description="Owner email address")


class DriveFileOwner(BaseModel):
    """Owner information for a file."""

    name: str | None = Field(None, description="Owner display name")
    email: str | None = Field(None, description="Owner email address")


class DriveFileDetailed(BaseModel):
    """Detailed file information from google_drive_get_file."""

    id: str = Field(..., description="File ID")
    name: str = Field(..., description="File name")
    mime_type: str = Field("", description="MIME type")
    size: str = Field("", description="File size")
    created: str = Field("", description="Creation date")
    modified: str = Field("", description="Last modified date")
    description: str = Field("", description="File description")
    web_link: str = Field("", description="Web view link")
    download_link: str = Field("", description="Direct download link")
    owners: list[DriveFileOwner] = Field(
        default_factory=list, description="File owners"
    )
    parent_folders: list[str] = Field(
        default_factory=list, description="Parent folder IDs"
    )


class DriveListData(BaseModel):
    """Output data for google_drive_list tool."""

    files: list[DriveFile] = Field(..., description="List of files")
    total: int = Field(..., description="Total number of files")


class DriveSearchData(BaseModel):
    """Output data for google_drive_search tool."""

    files: list[DriveFile] = Field(..., description="List of matching files")
    total: int = Field(..., description="Total number of results")
    query: str = Field(..., description="Search query used")


class DriveReadTextFileData(BaseModel):
    """Output data for google_drive_read_text_file tool."""

    name: str = Field(..., description="File name")
    mime_type: str = Field(..., description="MIME type")
    content: str = Field(..., description="File text content")
    length: int = Field(..., description="Content length in characters")


class DriveCreateFolderData(BaseModel):
    """Output data for google_drive_create_folder tool."""

    id: str = Field(..., description="Created folder ID")
    name: str = Field(..., description="Folder name")
    web_link: str = Field("", description="Web view link to the folder")
    parent_id: str = Field("", description="Parent folder ID")


# Drive Responses
class DriveListResponse(ToolResponse[DriveListData]):
    """Response for google_drive_list tool."""

    pass


class DriveSearchResponse(ToolResponse[DriveSearchData]):
    """Response for google_drive_search tool."""

    pass


class DriveGetFileResponse(ToolResponse[DriveFileDetailed]):
    """Response for google_drive_get_file tool."""

    pass


class DriveReadTextFileResponse(ToolResponse[DriveReadTextFileData]):
    """Response for google_drive_read_text_file tool."""

    pass


class DriveCreateFolderResponse(ToolResponse[DriveCreateFolderData]):
    """Response for google_drive_create_folder tool."""

    pass
