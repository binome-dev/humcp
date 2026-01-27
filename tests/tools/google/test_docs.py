from unittest.mock import MagicMock, patch

import pytest

from src.tools.google.docs import (
    google_docs_append_text,
    google_docs_create,
    google_docs_find_replace,
    google_docs_get_content,
    google_docs_list_in_folder,
    google_docs_search,
)


@pytest.fixture
def mock_docs_service():
    with patch("src.tools.google.docs.get_google_service") as mock:
        service = MagicMock()
        mock.return_value = service
        yield service


class TestSearchDocs:
    @pytest.mark.asyncio
    async def test_search_docs_success(self, mock_docs_service):
        mock_docs_service.files().list().execute.return_value = {
            "files": [
                {
                    "id": "doc1",
                    "name": "Project Report",
                    "modifiedTime": "2024-01-01T00:00:00Z",
                    "webViewLink": "https://docs.google.com/document/d/doc1",
                }
            ]
        }

        result = await google_docs_search("report")
        assert result["success"] is True
        assert result["data"]["total"] == 1
        assert result["data"]["documents"][0]["name"] == "Project Report"

    @pytest.mark.asyncio
    async def test_search_docs_no_results(self, mock_docs_service):
        mock_docs_service.files().list().execute.return_value = {"files": []}

        result = await google_docs_search("nonexistent")
        assert result["success"] is True
        assert result["data"]["total"] == 0

    @pytest.mark.asyncio
    async def test_search_docs_error(self, mock_docs_service):
        mock_docs_service.files().list().execute.side_effect = Exception(
            "Search failed"
        )

        result = await google_docs_search("test")
        assert result["success"] is False


class TestGetDocContent:
    @pytest.mark.asyncio
    async def test_get_doc_content_success(self, mock_docs_service):
        mock_docs_service.documents().get().execute.return_value = {
            "documentId": "doc1",
            "title": "My Document",
            "revisionId": "rev1",
            "body": {
                "content": [
                    {
                        "paragraph": {
                            "elements": [{"textRun": {"content": "Hello, World!\n"}}]
                        }
                    },
                    {
                        "paragraph": {
                            "elements": [
                                {"textRun": {"content": "Second paragraph.\n"}}
                            ]
                        }
                    },
                ]
            },
        }

        result = await google_docs_get_content("doc1")
        assert result["success"] is True
        assert result["data"]["id"] == "doc1"
        assert result["data"]["title"] == "My Document"
        assert "Hello, World!" in result["data"]["content"]

    @pytest.mark.asyncio
    async def test_get_doc_content_empty(self, mock_docs_service):
        mock_docs_service.documents().get().execute.return_value = {
            "documentId": "doc2",
            "title": "Empty Doc",
            "body": {"content": []},
        }

        result = await google_docs_get_content("doc2")
        assert result["success"] is True
        assert result["data"]["content"] == ""

    @pytest.mark.asyncio
    async def test_get_doc_content_error(self, mock_docs_service):
        mock_docs_service.documents().get().execute.side_effect = Exception(
            "Document not found"
        )

        result = await google_docs_get_content("invalid")
        assert result["success"] is False


class TestCreateDoc:
    @pytest.mark.asyncio
    async def test_create_doc_success(self, mock_docs_service):
        mock_docs_service.documents().create().execute.return_value = {
            "documentId": "new_doc",
            "title": "New Document",
        }

        result = await google_docs_create("New Document")
        assert result["success"] is True
        assert result["data"]["id"] == "new_doc"
        assert result["data"]["title"] == "New Document"
        assert "docs.google.com" in result["data"]["web_link"]

    @pytest.mark.asyncio
    async def test_create_doc_with_content(self, mock_docs_service):
        mock_docs_service.documents().create().execute.return_value = {
            "documentId": "new_doc",
            "title": "Doc with Content",
        }
        mock_docs_service.documents().batchUpdate().execute.return_value = {}

        result = await google_docs_create(
            "Doc with Content", content="Initial content here"
        )
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_create_doc_error(self, mock_docs_service):
        mock_docs_service.documents().create().execute.side_effect = Exception(
            "Creation failed"
        )

        result = await google_docs_create("Test")
        assert result["success"] is False


class TestAppendText:
    @pytest.mark.asyncio
    async def test_append_text_success(self, mock_docs_service):
        mock_docs_service.documents().get().execute.return_value = {
            "body": {"content": [{"endIndex": 100}]}
        }
        mock_docs_service.documents().batchUpdate().execute.return_value = {}

        result = await google_docs_append_text("doc1", " appended text")
        assert result["success"] is True
        assert result["data"]["updated"] is True
        assert result["data"]["document_id"] == "doc1"

    @pytest.mark.asyncio
    async def test_append_text_error(self, mock_docs_service):
        mock_docs_service.documents().get().execute.side_effect = Exception(
            "Document not found"
        )

        result = await google_docs_append_text("invalid", "text")
        assert result["success"] is False


class TestFindAndReplace:
    @pytest.mark.asyncio
    async def test_find_and_replace_success(self, mock_docs_service):
        mock_docs_service.documents().batchUpdate().execute.return_value = {
            "replies": [{"replaceAllText": {"occurrencesChanged": 5}}]
        }

        result = await google_docs_find_replace("doc1", "old", "new")
        assert result["success"] is True
        assert result["data"]["replacements"] == 5
        assert result["data"]["find_text"] == "old"
        assert result["data"]["replace_text"] == "new"

    @pytest.mark.asyncio
    async def test_find_and_replace_no_matches(self, mock_docs_service):
        mock_docs_service.documents().batchUpdate().execute.return_value = {
            "replies": [{"replaceAllText": {"occurrencesChanged": 0}}]
        }

        result = await google_docs_find_replace("doc1", "nonexistent", "new")
        assert result["success"] is True
        assert result["data"]["replacements"] == 0

    @pytest.mark.asyncio
    async def test_find_and_replace_error(self, mock_docs_service):
        mock_docs_service.documents().batchUpdate().execute.side_effect = Exception(
            "Permission denied"
        )

        result = await google_docs_find_replace("doc1", "old", "new")
        assert result["success"] is False


class TestListDocsInFolder:
    @pytest.mark.asyncio
    async def test_list_docs_in_folder_success(self, mock_docs_service):
        mock_docs_service.files().list().execute.return_value = {
            "files": [
                {
                    "id": "doc1",
                    "name": "Doc 1",
                    "modifiedTime": "2024-01-01T00:00:00Z",
                    "webViewLink": "https://docs.google.com/document/d/doc1",
                },
                {
                    "id": "doc2",
                    "name": "Doc 2",
                    "modifiedTime": "2024-01-02T00:00:00Z",
                    "webViewLink": "https://docs.google.com/document/d/doc2",
                },
            ]
        }

        result = await google_docs_list_in_folder("folder123")
        assert result["success"] is True
        assert result["data"]["total"] == 2

    @pytest.mark.asyncio
    async def test_list_docs_in_folder_empty(self, mock_docs_service):
        mock_docs_service.files().list().execute.return_value = {"files": []}

        result = await google_docs_list_in_folder("empty_folder")
        assert result["success"] is True
        assert result["data"]["total"] == 0

    @pytest.mark.asyncio
    async def test_list_docs_in_folder_error(self, mock_docs_service):
        mock_docs_service.files().list().execute.side_effect = Exception(
            "Folder not found"
        )

        result = await google_docs_list_in_folder("invalid")
        assert result["success"] is False
