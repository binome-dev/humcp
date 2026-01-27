from unittest.mock import MagicMock, patch

import pytest

from src.tools.google.tasks import (
    google_tasks_clear_completed,
    google_tasks_complete_task,
    google_tasks_create_task,
    google_tasks_create_task_list,
    google_tasks_delete_task,
    google_tasks_delete_task_list,
    google_tasks_get_task,
    google_tasks_get_task_list,
    google_tasks_list_task_lists,
    google_tasks_list_tasks,
    google_tasks_update_task,
)


@pytest.fixture
def mock_tasks_service():
    with patch("src.tools.google.tasks.get_google_service") as mock:
        service = MagicMock()
        mock.return_value = service
        yield service


class TestListTaskLists:
    @pytest.mark.asyncio
    async def test_list_task_lists_success(self, mock_tasks_service):
        mock_tasks_service.tasklists().list().execute.return_value = {
            "items": [
                {"id": "list1", "title": "My Tasks", "updated": "2024-01-01T00:00:00Z"},
                {"id": "list2", "title": "Work", "updated": "2024-01-02T00:00:00Z"},
            ]
        }

        result = await google_tasks_list_task_lists()
        assert result["success"] is True
        assert result["data"]["total"] == 2
        assert result["data"]["task_lists"][0]["title"] == "My Tasks"

    @pytest.mark.asyncio
    async def test_list_task_lists_empty(self, mock_tasks_service):
        mock_tasks_service.tasklists().list().execute.return_value = {"items": []}

        result = await google_tasks_list_task_lists()
        assert result["success"] is True
        assert result["data"]["total"] == 0

    @pytest.mark.asyncio
    async def test_list_task_lists_error(self, mock_tasks_service):
        mock_tasks_service.tasklists().list().execute.side_effect = Exception(
            "API error"
        )

        result = await google_tasks_list_task_lists()
        assert result["success"] is False


class TestGetTaskList:
    @pytest.mark.asyncio
    async def test_get_task_list_success(self, mock_tasks_service):
        mock_tasks_service.tasklists().get().execute.return_value = {
            "id": "list1",
            "title": "My Tasks",
            "updated": "2024-01-01T00:00:00Z",
        }

        result = await google_tasks_get_task_list("list1")
        assert result["success"] is True
        assert result["data"]["id"] == "list1"
        assert result["data"]["title"] == "My Tasks"

    @pytest.mark.asyncio
    async def test_get_task_list_error(self, mock_tasks_service):
        mock_tasks_service.tasklists().get().execute.side_effect = Exception(
            "Not found"
        )

        result = await google_tasks_get_task_list("invalid")
        assert result["success"] is False


class TestCreateTaskList:
    @pytest.mark.asyncio
    async def test_create_task_list_success(self, mock_tasks_service):
        mock_tasks_service.tasklists().insert().execute.return_value = {
            "id": "new_list",
            "title": "New List",
            "updated": "2024-01-15T00:00:00Z",
        }

        result = await google_tasks_create_task_list("New List")
        assert result["success"] is True
        assert result["data"]["id"] == "new_list"
        assert result["data"]["title"] == "New List"

    @pytest.mark.asyncio
    async def test_create_task_list_error(self, mock_tasks_service):
        mock_tasks_service.tasklists().insert().execute.side_effect = Exception(
            "Creation failed"
        )

        result = await google_tasks_create_task_list("Test")
        assert result["success"] is False


class TestDeleteTaskList:
    @pytest.mark.asyncio
    async def test_delete_task_list_success(self, mock_tasks_service):
        mock_tasks_service.tasklists().delete().execute.return_value = None

        result = await google_tasks_delete_task_list("list1")
        assert result["success"] is True
        assert result["data"]["deleted_task_list_id"] == "list1"

    @pytest.mark.asyncio
    async def test_delete_task_list_error(self, mock_tasks_service):
        mock_tasks_service.tasklists().delete().execute.side_effect = Exception(
            "Not found"
        )

        result = await google_tasks_delete_task_list("invalid")
        assert result["success"] is False


class TestListTasks:
    @pytest.mark.asyncio
    async def test_list_tasks_success(self, mock_tasks_service):
        mock_tasks_service.tasks().list().execute.return_value = {
            "items": [
                {
                    "id": "task1",
                    "title": "Buy groceries",
                    "notes": "Milk, eggs, bread",
                    "status": "needsAction",
                    "due": "2024-01-20T00:00:00Z",
                },
                {
                    "id": "task2",
                    "title": "Call mom",
                    "status": "completed",
                    "completed": "2024-01-15T00:00:00Z",
                },
            ]
        }

        result = await google_tasks_list_tasks()
        assert result["success"] is True
        assert result["data"]["total"] == 2
        assert result["data"]["tasks"][0]["title"] == "Buy groceries"

    @pytest.mark.asyncio
    async def test_list_tasks_empty(self, mock_tasks_service):
        mock_tasks_service.tasks().list().execute.return_value = {"items": []}

        result = await google_tasks_list_tasks()
        assert result["success"] is True
        assert result["data"]["total"] == 0

    @pytest.mark.asyncio
    async def test_list_tasks_error(self, mock_tasks_service):
        mock_tasks_service.tasks().list().execute.side_effect = Exception("API error")

        result = await google_tasks_list_tasks()
        assert result["success"] is False


class TestGetTask:
    @pytest.mark.asyncio
    async def test_get_task_success(self, mock_tasks_service):
        mock_tasks_service.tasks().get().execute.return_value = {
            "id": "task1",
            "title": "Important task",
            "notes": "Details here",
            "status": "needsAction",
            "due": "2024-01-20T00:00:00Z",
            "links": [],
        }

        result = await google_tasks_get_task("list1", "task1")
        assert result["success"] is True
        assert result["data"]["id"] == "task1"
        assert result["data"]["title"] == "Important task"

    @pytest.mark.asyncio
    async def test_get_task_error(self, mock_tasks_service):
        mock_tasks_service.tasks().get().execute.side_effect = Exception("Not found")

        result = await google_tasks_get_task("list1", "invalid")
        assert result["success"] is False


class TestCreateTask:
    @pytest.mark.asyncio
    async def test_create_task_success(self, mock_tasks_service):
        mock_tasks_service.tasks().insert().execute.return_value = {
            "id": "new_task",
            "title": "New task",
            "notes": "Notes here",
            "status": "needsAction",
            "due": "2024-01-25T00:00:00Z",
        }

        result = await google_tasks_create_task(title="New task", notes="Notes here")
        assert result["success"] is True
        assert result["data"]["id"] == "new_task"
        assert result["data"]["title"] == "New task"

    @pytest.mark.asyncio
    async def test_create_task_error(self, mock_tasks_service):
        mock_tasks_service.tasks().insert().execute.side_effect = Exception(
            "Creation failed"
        )

        result = await google_tasks_create_task(title="Test")
        assert result["success"] is False


class TestUpdateTask:
    @pytest.mark.asyncio
    async def test_update_task_success(self, mock_tasks_service):
        mock_tasks_service.tasks().get().execute.return_value = {
            "id": "task1",
            "title": "Old title",
            "status": "needsAction",
        }
        mock_tasks_service.tasks().update().execute.return_value = {
            "id": "task1",
            "title": "Updated title",
            "status": "needsAction",
        }

        result = await google_tasks_update_task("list1", "task1", title="Updated title")
        assert result["success"] is True
        assert result["data"]["title"] == "Updated title"

    @pytest.mark.asyncio
    async def test_update_task_error(self, mock_tasks_service):
        mock_tasks_service.tasks().get().execute.side_effect = Exception("Not found")

        result = await google_tasks_update_task("list1", "invalid", title="New title")
        assert result["success"] is False


class TestDeleteTask:
    @pytest.mark.asyncio
    async def test_delete_task_success(self, mock_tasks_service):
        mock_tasks_service.tasks().delete().execute.return_value = None

        result = await google_tasks_delete_task("list1", "task1")
        assert result["success"] is True
        assert result["data"]["deleted_task_id"] == "task1"

    @pytest.mark.asyncio
    async def test_delete_task_error(self, mock_tasks_service):
        mock_tasks_service.tasks().delete().execute.side_effect = Exception("Not found")

        result = await google_tasks_delete_task("list1", "invalid")
        assert result["success"] is False


class TestCompleteTask:
    @pytest.mark.asyncio
    async def test_complete_task_success(self, mock_tasks_service):
        mock_tasks_service.tasks().get().execute.return_value = {
            "id": "task1",
            "title": "Task to complete",
            "status": "needsAction",
        }
        mock_tasks_service.tasks().update().execute.return_value = {
            "id": "task1",
            "title": "Task to complete",
            "status": "completed",
            "completed": "2024-01-15T00:00:00Z",
        }

        result = await google_tasks_complete_task("list1", "task1")
        assert result["success"] is True
        assert result["data"]["status"] == "completed"


class TestClearCompletedTasks:
    @pytest.mark.asyncio
    async def test_clear_completed_tasks_success(self, mock_tasks_service):
        mock_tasks_service.tasks().clear().execute.return_value = None

        result = await google_tasks_clear_completed()
        assert result["success"] is True
        assert result["data"]["cleared"] is True

    @pytest.mark.asyncio
    async def test_clear_completed_tasks_error(self, mock_tasks_service):
        mock_tasks_service.tasks().clear().execute.side_effect = Exception(
            "Clear failed"
        )

        result = await google_tasks_clear_completed()
        assert result["success"] is False
