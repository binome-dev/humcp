from unittest.mock import MagicMock, patch

import pytest

from src.tools.google.gmail import (
    google_gmail_labels,
    google_gmail_read,
    google_gmail_search,
    google_gmail_send,
)


@pytest.fixture
def mock_gmail_service():
    with patch("src.tools.google.gmail.get_google_service") as mock:
        service = MagicMock()
        mock.return_value = service
        yield service


class TestSearch:
    @pytest.mark.asyncio
    async def test_search_success(self, mock_gmail_service):
        mock_gmail_service.users().messages().list().execute.return_value = {
            "messages": [{"id": "msg1", "threadId": "thread1"}]
        }
        mock_gmail_service.users().messages().get().execute.return_value = {
            "id": "msg1",
            "threadId": "thread1",
            "snippet": "Hello, this is a test email",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Test Subject"},
                    {"name": "From", "value": "sender@example.com"},
                    {"name": "To", "value": "recipient@example.com"},
                    {"name": "Date", "value": "Mon, 15 Jan 2024 10:00:00 +0000"},
                ]
            },
        }

        result = await google_gmail_search("test")
        assert result["success"] is True
        assert result["data"]["total"] == 1
        assert result["data"]["messages"][0]["subject"] == "Test Subject"
        assert result["data"]["messages"][0]["from"] == "sender@example.com"

    @pytest.mark.asyncio
    async def test_search_no_results(self, mock_gmail_service):
        mock_gmail_service.users().messages().list().execute.return_value = {
            "messages": []
        }

        result = await google_gmail_search("nonexistent query")
        assert result["success"] is True
        assert result["data"]["total"] == 0

    @pytest.mark.asyncio
    async def test_search_error(self, mock_gmail_service):
        mock_gmail_service.users().messages().list().execute.side_effect = Exception(
            "Search failed"
        )

        result = await google_gmail_search("test")
        assert result["success"] is False


class TestRead:
    @pytest.mark.asyncio
    async def test_read_success(self, mock_gmail_service):
        mock_gmail_service.users().messages().get().execute.return_value = {
            "id": "msg1",
            "threadId": "thread1",
            "labelIds": ["INBOX", "UNREAD"],
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Important Email"},
                    {"name": "From", "value": "boss@company.com"},
                    {"name": "To", "value": "me@company.com"},
                    {"name": "Cc", "value": "team@company.com"},
                    {"name": "Date", "value": "Mon, 15 Jan 2024 10:00:00 +0000"},
                ],
                "body": {"data": "SGVsbG8sIFdvcmxkIQ=="},  # "Hello, World!" in base64
            },
        }

        result = await google_gmail_read("msg1")
        assert result["success"] is True
        assert result["data"]["subject"] == "Important Email"
        assert result["data"]["body"] == "Hello, World!"
        assert "INBOX" in result["data"]["labels"]

    @pytest.mark.asyncio
    async def test_read_multipart(self, mock_gmail_service):
        mock_gmail_service.users().messages().get().execute.return_value = {
            "id": "msg2",
            "threadId": "thread2",
            "labelIds": ["INBOX"],
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Multipart Email"},
                    {"name": "From", "value": "sender@example.com"},
                ],
                "parts": [
                    {
                        "mimeType": "text/plain",
                        "body": {"data": "UGxhaW4gdGV4dA=="},  # "Plain text"
                    },
                    {
                        "mimeType": "text/html",
                        "body": {"data": "SFRNTA=="},  # "HTML"
                    },
                ],
            },
        }

        result = await google_gmail_read("msg2")
        assert result["success"] is True
        assert result["data"]["body"] == "Plain text"

    @pytest.mark.asyncio
    async def test_read_error(self, mock_gmail_service):
        mock_gmail_service.users().messages().get().execute.side_effect = Exception(
            "Message not found"
        )

        result = await google_gmail_read("invalid_id")
        assert result["success"] is False


class TestSend:
    @pytest.mark.asyncio
    async def test_send_success(self, mock_gmail_service):
        mock_gmail_service.users().messages().send().execute.return_value = {
            "id": "sent_msg",
            "threadId": "new_thread",
        }

        result = await google_gmail_send(
            to="recipient@example.com",
            subject="Test Email",
            body="This is a test email body.",
        )
        assert result["success"] is True
        assert result["data"]["message_id"] == "sent_msg"

    @pytest.mark.asyncio
    async def test_send_with_cc_bcc(self, mock_gmail_service):
        mock_gmail_service.users().messages().send().execute.return_value = {
            "id": "sent_msg2",
            "threadId": "thread2",
        }

        result = await google_gmail_send(
            to="recipient@example.com",
            subject="Team Update",
            body="Update content",
            cc="team@example.com",
            bcc="manager@example.com",
        )
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_send_error(self, mock_gmail_service):
        mock_gmail_service.users().messages().send().execute.side_effect = Exception(
            "Send failed"
        )

        result = await google_gmail_send(
            to="invalid",
            subject="Test",
            body="Body",
        )
        assert result["success"] is False


class TestLabels:
    @pytest.mark.asyncio
    async def test_labels_success(self, mock_gmail_service):
        mock_gmail_service.users().labels().list().execute.return_value = {
            "labels": [
                {"id": "INBOX", "name": "INBOX"},
                {"id": "SENT", "name": "SENT"},
                {"id": "Label_1", "name": "Work"},
            ]
        }

        result = await google_gmail_labels()
        assert result["success"] is True
        assert result["data"]["total"] == 3
        assert result["data"]["labels"][0]["name"] == "INBOX"

    @pytest.mark.asyncio
    async def test_labels_error(self, mock_gmail_service):
        mock_gmail_service.users().labels().list().execute.side_effect = Exception(
            "Failed to list labels"
        )

        result = await google_gmail_labels()
        assert result["success"] is False
