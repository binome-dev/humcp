from unittest.mock import MagicMock, patch

import pytest

from src.tools.google.drive import get_file, list_files, read_text_file, search


@pytest.fixture
def mock_drive_service():
    with patch("src.tools.google.drive.get_google_service") as mock:
        service = MagicMock()
        mock.return_value = service
        yield service


class TestListFiles:
    @pytest.mark.asyncio
    async def test_list_files_success(self, mock_drive_service):
        mock_drive_service.files().list().execute.return_value = {
            "files": [
                {
                    "id": "file1",
                    "name": "Document.txt",
                    "mimeType": "text/plain",
                    "size": "1024",
                    "modifiedTime": "2024-01-01T00:00:00Z",
                    "webViewLink": "https://drive.google.com/file1",
                }
            ]
        }

        result = await list_files()
        assert result["success"] is True
        assert result["data"]["total"] == 1
        assert result["data"]["files"][0]["id"] == "file1"
        assert result["data"]["files"][0]["name"] == "Document.txt"

    @pytest.mark.asyncio
    async def test_list_files_empty(self, mock_drive_service):
        mock_drive_service.files().list().execute.return_value = {"files": []}

        result = await list_files()
        assert result["success"] is True
        assert result["data"]["total"] == 0
        assert result["data"]["files"] == []

    @pytest.mark.asyncio
    async def test_list_files_with_folder_id(self, mock_drive_service):
        mock_drive_service.files().list().execute.return_value = {"files": []}

        result = await list_files(folder_id="folder123")
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_list_files_with_file_type(self, mock_drive_service):
        mock_drive_service.files().list().execute.return_value = {"files": []}

        result = await list_files(file_type="image")
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_list_files_error(self, mock_drive_service):
        mock_drive_service.files().list().execute.side_effect = Exception("API error")

        result = await list_files()
        assert result["success"] is False
        assert "API error" in result["error"]


class TestSearch:
    @pytest.mark.asyncio
    async def test_search_success(self, mock_drive_service):
        mock_drive_service.files().list().execute.return_value = {
            "files": [
                {
                    "id": "file1",
                    "name": "Report.docx",
                    "mimeType": "application/vnd.google-apps.document",
                    "modifiedTime": "2024-01-01T00:00:00Z",
                    "webViewLink": "https://docs.google.com/file1",
                    "owners": [{"emailAddress": "user@example.com"}],
                }
            ]
        }

        result = await search("report")
        assert result["success"] is True
        assert result["data"]["total"] == 1
        assert result["data"]["query"] == "report"
        assert result["data"]["files"][0]["name"] == "Report.docx"

    @pytest.mark.asyncio
    async def test_search_no_results(self, mock_drive_service):
        mock_drive_service.files().list().execute.return_value = {"files": []}

        result = await search("nonexistent")
        assert result["success"] is True
        assert result["data"]["total"] == 0

    @pytest.mark.asyncio
    async def test_search_error(self, mock_drive_service):
        mock_drive_service.files().list().execute.side_effect = Exception(
            "Search failed"
        )

        result = await search("test")
        assert result["success"] is False
        assert "Search failed" in result["error"]


class TestGetFile:
    @pytest.mark.asyncio
    async def test_get_file_success(self, mock_drive_service):
        mock_drive_service.files().get().execute.return_value = {
            "id": "file123",
            "name": "Important.pdf",
            "mimeType": "application/pdf",
            "size": "2048",
            "createdTime": "2024-01-01T00:00:00Z",
            "modifiedTime": "2024-01-02T00:00:00Z",
            "webViewLink": "https://drive.google.com/file123",
            "owners": [{"displayName": "John Doe", "emailAddress": "john@example.com"}],
            "parents": ["folder1"],
        }

        result = await get_file("file123")
        assert result["success"] is True
        assert result["data"]["id"] == "file123"
        assert result["data"]["name"] == "Important.pdf"
        assert result["data"]["owners"][0]["name"] == "John Doe"

    @pytest.mark.asyncio
    async def test_get_file_not_found(self, mock_drive_service):
        mock_drive_service.files().get().execute.side_effect = Exception(
            "File not found"
        )

        result = await get_file("nonexistent")
        assert result["success"] is False
        assert "not found" in result["error"].lower()


class TestReadTextFile:
    @pytest.mark.asyncio
    async def test_read_text_file_success(self, mock_drive_service):
        mock_drive_service.files().get().execute.return_value = {
            "name": "notes.txt",
            "mimeType": "text/plain",
        }

        # Mock the media download
        with patch("src.tools.google.drive.MediaIoBaseDownload") as mock_download:
            mock_downloader = MagicMock()
            mock_downloader.next_chunk.return_value = (None, True)
            mock_download.return_value = mock_downloader

            # Need to patch BytesIO to return our content
            with patch("src.tools.google.drive.io.BytesIO") as mock_bytesio:
                mock_buffer = MagicMock()
                mock_buffer.getvalue.return_value = b"Hello, World!"
                mock_bytesio.return_value = mock_buffer

                result = await read_text_file("file123")
                assert result["success"] is True
                assert result["data"]["name"] == "notes.txt"
                assert result["data"]["content"] == "Hello, World!"

    @pytest.mark.asyncio
    async def test_read_text_file_google_doc(self, mock_drive_service):
        mock_drive_service.files().get().execute.return_value = {
            "name": "My Document",
            "mimeType": "application/vnd.google-apps.document",
        }

        with patch("src.tools.google.drive.MediaIoBaseDownload") as mock_download:
            mock_downloader = MagicMock()
            mock_downloader.next_chunk.return_value = (None, True)
            mock_download.return_value = mock_downloader

            with patch("src.tools.google.drive.io.BytesIO") as mock_bytesio:
                mock_buffer = MagicMock()
                mock_buffer.getvalue.return_value = b"Document content"
                mock_bytesio.return_value = mock_buffer

                result = await read_text_file("doc123")
                assert result["success"] is True

    @pytest.mark.asyncio
    async def test_read_text_file_error(self, mock_drive_service):
        mock_drive_service.files().get().execute.side_effect = Exception(
            "Access denied"
        )

        result = await read_text_file("file123")
        assert result["success"] is False
        assert "Access denied" in result["error"]
