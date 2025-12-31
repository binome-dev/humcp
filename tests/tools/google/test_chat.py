from unittest.mock import MagicMock, patch

import pytest

from src.tools.google.chat import (
    get_message,
    get_messages,
    get_space,
    list_spaces,
    send_message,
)


@pytest.fixture
def mock_chat_service():
    with patch("src.tools.google.chat.get_google_service") as mock:
        service = MagicMock()
        mock.return_value = service
        yield service


class TestListSpaces:
    @pytest.mark.asyncio
    async def test_list_spaces_success(self, mock_chat_service):
        mock_chat_service.spaces().list().execute.return_value = {
            "spaces": [
                {
                    "name": "spaces/space1",
                    "displayName": "Engineering Team",
                    "type": "ROOM",
                    "singleUserBotDm": False,
                    "threaded": True,
                },
                {
                    "name": "spaces/space2",
                    "displayName": "",
                    "type": "DIRECT_MESSAGE",
                    "singleUserBotDm": True,
                    "threaded": False,
                },
            ]
        }

        result = await list_spaces()
        assert result["success"] is True
        assert result["data"]["total"] == 2
        assert result["data"]["spaces"][0]["display_name"] == "Engineering Team"
        assert result["data"]["spaces"][0]["type"] == "ROOM"

    @pytest.mark.asyncio
    async def test_list_spaces_filter_room(self, mock_chat_service):
        mock_chat_service.spaces().list().execute.return_value = {
            "spaces": [
                {"name": "spaces/space1", "type": "ROOM"},
                {"name": "spaces/space2", "type": "DIRECT_MESSAGE"},
            ]
        }

        result = await list_spaces(space_type="room")
        assert result["success"] is True
        assert result["data"]["total"] == 1

    @pytest.mark.asyncio
    async def test_list_spaces_empty(self, mock_chat_service):
        mock_chat_service.spaces().list().execute.return_value = {"spaces": []}

        result = await list_spaces()
        assert result["success"] is True
        assert result["data"]["total"] == 0

    @pytest.mark.asyncio
    async def test_list_spaces_error(self, mock_chat_service):
        mock_chat_service.spaces().list().execute.side_effect = Exception("API error")

        result = await list_spaces()
        assert result["success"] is False


class TestGetSpace:
    @pytest.mark.asyncio
    async def test_get_space_success(self, mock_chat_service):
        mock_chat_service.spaces().get().execute.return_value = {
            "name": "spaces/space1",
            "displayName": "Project Alpha",
            "type": "ROOM",
            "singleUserBotDm": False,
            "threaded": True,
            "externalUserAllowed": False,
        }

        result = await get_space("spaces/space1")
        assert result["success"] is True
        assert result["data"]["name"] == "spaces/space1"
        assert result["data"]["display_name"] == "Project Alpha"
        assert result["data"]["threaded"] is True

    @pytest.mark.asyncio
    async def test_get_space_error(self, mock_chat_service):
        mock_chat_service.spaces().get().execute.side_effect = Exception("Not found")

        result = await get_space("spaces/invalid")
        assert result["success"] is False


class TestGetMessages:
    @pytest.mark.asyncio
    async def test_get_messages_success(self, mock_chat_service):
        mock_chat_service.spaces().messages().list().execute.return_value = {
            "messages": [
                {
                    "name": "spaces/space1/messages/msg1",
                    "text": "Hello everyone!",
                    "sender": {"displayName": "John Doe", "type": "HUMAN"},
                    "createTime": "2024-01-15T10:00:00Z",
                    "thread": {"name": "spaces/space1/threads/thread1"},
                },
                {
                    "name": "spaces/space1/messages/msg2",
                    "text": "Hi John!",
                    "sender": {"displayName": "Jane Smith", "type": "HUMAN"},
                    "createTime": "2024-01-15T10:01:00Z",
                    "thread": {"name": "spaces/space1/threads/thread1"},
                },
            ]
        }

        result = await get_messages("spaces/space1")
        assert result["success"] is True
        assert result["data"]["total"] == 2
        assert result["data"]["messages"][0]["text"] == "Hello everyone!"
        assert result["data"]["messages"][0]["sender"] == "John Doe"

    @pytest.mark.asyncio
    async def test_get_messages_empty(self, mock_chat_service):
        mock_chat_service.spaces().messages().list().execute.return_value = {
            "messages": []
        }

        result = await get_messages("spaces/space1")
        assert result["success"] is True
        assert result["data"]["total"] == 0

    @pytest.mark.asyncio
    async def test_get_messages_error(self, mock_chat_service):
        mock_chat_service.spaces().messages().list().execute.side_effect = Exception(
            "Space not found"
        )

        result = await get_messages("spaces/invalid")
        assert result["success"] is False


class TestGetMessage:
    @pytest.mark.asyncio
    async def test_get_message_success(self, mock_chat_service):
        mock_chat_service.spaces().messages().get().execute.return_value = {
            "name": "spaces/space1/messages/msg1",
            "text": "Important update",
            "sender": {"displayName": "Admin Bot", "type": "BOT"},
            "createTime": "2024-01-15T10:00:00Z",
            "thread": {"name": "spaces/space1/threads/thread1"},
            "space": {"name": "spaces/space1"},
        }

        result = await get_message("spaces/space1/messages/msg1")
        assert result["success"] is True
        assert result["data"]["text"] == "Important update"
        assert result["data"]["sender_type"] == "BOT"

    @pytest.mark.asyncio
    async def test_get_message_error(self, mock_chat_service):
        mock_chat_service.spaces().messages().get().execute.side_effect = Exception(
            "Message not found"
        )

        result = await get_message("spaces/space1/messages/invalid")
        assert result["success"] is False


class TestSendMessage:
    @pytest.mark.asyncio
    async def test_send_message_success(self, mock_chat_service):
        mock_chat_service.spaces().messages().create().execute.return_value = {
            "name": "spaces/space1/messages/new_msg",
            "text": "Hello from the bot!",
            "createTime": "2024-01-15T10:30:00Z",
            "thread": {"name": "spaces/space1/threads/new_thread"},
        }

        result = await send_message("spaces/space1", "Hello from the bot!")
        assert result["success"] is True
        assert result["data"]["text"] == "Hello from the bot!"
        assert "new_msg" in result["data"]["name"]

    @pytest.mark.asyncio
    async def test_send_message_with_thread(self, mock_chat_service):
        mock_chat_service.spaces().messages().create().execute.return_value = {
            "name": "spaces/space1/messages/reply_msg",
            "text": "This is a reply",
            "createTime": "2024-01-15T10:35:00Z",
            "thread": {"name": "spaces/space1/threads/existing_thread"},
        }

        result = await send_message(
            "spaces/space1", "This is a reply", thread_key="existing_thread"
        )
        assert result["success"] is True
        assert "existing_thread" in result["data"]["thread_name"]

    @pytest.mark.asyncio
    async def test_send_message_error(self, mock_chat_service):
        mock_chat_service.spaces().messages().create().execute.side_effect = Exception(
            "Permission denied"
        )

        result = await send_message("spaces/space1", "Test message")
        assert result["success"] is False
