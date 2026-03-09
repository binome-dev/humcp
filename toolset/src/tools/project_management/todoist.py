"""Todoist task management tools.

Uses the Todoist REST API via the todoist-api-python SDK. Requires a
TODOIST_API_KEY environment variable.

API Reference: https://developer.todoist.com/rest/v2/
"""

from __future__ import annotations

import logging
import os

from src.humcp.decorator import tool
from src.tools.project_management.schemas import (
    TodoistCommentData,
    TodoistCommentListData,
    TodoistCommentListResponse,
    TodoistProjectData,
    TodoistProjectListData,
    TodoistProjectListResponse,
    TodoistTaskData,
    TodoistTaskListData,
    TodoistTaskListResponse,
    TodoistTaskResponse,
)

try:
    from todoist_api_python.api import TodoistAPI
except ImportError as err:
    raise ImportError(
        "todoist-api-python is required for Todoist tools. "
        "Install with: pip install todoist-api-python"
    ) from err

logger = logging.getLogger("humcp.tools.todoist")


def _get_todoist_client() -> tuple[TodoistAPI | None, str | None]:
    """Create a Todoist client from environment variables.

    Returns:
        A tuple of (client, error_message).
    """
    api_key = os.getenv("TODOIST_API_KEY")
    if not api_key:
        return (
            None,
            "Todoist API key not configured. Set TODOIST_API_KEY environment variable.",
        )
    return TodoistAPI(api_key), None


def _task_to_data(task: object) -> TodoistTaskData:
    """Convert a Todoist task object to a TodoistTaskData model.

    Args:
        task: A Todoist task object from the SDK.

    Returns:
        A TodoistTaskData Pydantic model.
    """
    due_str = None
    if hasattr(task, "due") and task.due:
        due_str = getattr(task.due, "date", None) or getattr(task.due, "string", None)

    labels: list[str] = []
    if hasattr(task, "labels") and task.labels:
        labels = list(task.labels)

    return TodoistTaskData(
        id=task.id,
        content=task.content,
        description=getattr(task, "description", None),
        project_id=getattr(task, "project_id", None),
        section_id=getattr(task, "section_id", None),
        priority=getattr(task, "priority", None),
        url=getattr(task, "url", None),
        due=due_str,
        is_completed=getattr(task, "is_completed", False),
        labels=labels,
    )


@tool()
async def todoist_create_task(
    content: str,
    description: str | None = None,
    project_id: str | None = None,
    section_id: str | None = None,
    priority: int | None = None,
    due_string: str | None = None,
    due_date: str | None = None,
    labels: list[str] | None = None,
) -> TodoistTaskResponse:
    """Create a new task in Todoist.

    Args:
        content: The task content/title.
        description: Optional task description.
        project_id: Optional project ID to add the task to.
        section_id: Optional section ID within the project.
        priority: Optional priority level (1=normal, 2=medium, 3=high, 4=urgent).
        due_string: Optional due date in natural language (e.g., "tomorrow at 12:00").
        due_date: Optional due date in YYYY-MM-DD format.
        labels: Optional list of label names to apply.

    Returns:
        Details of the newly created task.
    """
    try:
        client, error = _get_todoist_client()
        if error or client is None:
            return TodoistTaskResponse(success=False, error=error)

        kwargs: dict = {"content": content}
        if description is not None:
            kwargs["description"] = description
        if project_id is not None:
            kwargs["project_id"] = project_id
        if section_id is not None:
            kwargs["section_id"] = section_id
        if priority is not None:
            kwargs["priority"] = priority
        if due_string is not None:
            kwargs["due_string"] = due_string
        if due_date is not None:
            kwargs["due_date"] = due_date
        if labels is not None:
            kwargs["labels"] = labels

        task = client.add_task(**kwargs)
        logger.info("Created Todoist task %s", task.id)

        return TodoistTaskResponse(success=True, data=_task_to_data(task))
    except Exception as e:
        logger.exception("Failed to create Todoist task")
        return TodoistTaskResponse(success=False, error=f"Failed to create task: {e}")


@tool()
async def todoist_get_task(task_id: str) -> TodoistTaskResponse:
    """Retrieve a specific Todoist task by its ID.

    Args:
        task_id: The Todoist task ID.

    Returns:
        Task details including content, description, due date, and priority.
    """
    try:
        client, error = _get_todoist_client()
        if error or client is None:
            return TodoistTaskResponse(success=False, error=error)

        task = client.get_task(task_id)

        return TodoistTaskResponse(success=True, data=_task_to_data(task))
    except Exception as e:
        logger.exception("Failed to get Todoist task %s", task_id)
        return TodoistTaskResponse(success=False, error=f"Failed to get task: {e}")


@tool()
async def todoist_update_task(
    task_id: str,
    content: str | None = None,
    description: str | None = None,
    priority: int | None = None,
    due_string: str | None = None,
    due_date: str | None = None,
    labels: list[str] | None = None,
) -> TodoistTaskResponse:
    """Update an existing Todoist task.

    Args:
        task_id: The ID of the task to update.
        content: New task content/title.
        description: New task description.
        priority: New priority level (1=normal, 2=medium, 3=high, 4=urgent).
        due_string: New due date in natural language.
        due_date: New due date in YYYY-MM-DD format.
        labels: New list of label names (replaces existing labels).

    Returns:
        Updated task details.
    """
    try:
        client, error = _get_todoist_client()
        if error or client is None:
            return TodoistTaskResponse(success=False, error=error)

        kwargs: dict = {}
        if content is not None:
            kwargs["content"] = content
        if description is not None:
            kwargs["description"] = description
        if priority is not None:
            kwargs["priority"] = priority
        if due_string is not None:
            kwargs["due_string"] = due_string
        if due_date is not None:
            kwargs["due_date"] = due_date
        if labels is not None:
            kwargs["labels"] = labels

        if not kwargs:
            return TodoistTaskResponse(
                success=False, error="At least one field must be provided to update."
            )

        result = client.update_task(task_id, **kwargs)

        logger.info("Updated Todoist task %s", task_id)

        # update_task may return bool or task; fetch task for consistent response
        if isinstance(result, bool):
            task = client.get_task(task_id)
            return TodoistTaskResponse(success=True, data=_task_to_data(task))

        return TodoistTaskResponse(success=True, data=_task_to_data(result))
    except Exception as e:
        logger.exception("Failed to update Todoist task %s", task_id)
        return TodoistTaskResponse(success=False, error=f"Failed to update task: {e}")


@tool()
async def todoist_close_task(task_id: str) -> TodoistTaskResponse:
    """Close (complete) a Todoist task.

    Args:
        task_id: The ID of the task to close.

    Returns:
        The closed task details.
    """
    try:
        client, error = _get_todoist_client()
        if error or client is None:
            return TodoistTaskResponse(success=False, error=error)

        client.close_task(task_id)

        logger.info("Closed Todoist task %s", task_id)

        # Fetch updated task to return full details
        task = client.get_task(task_id)
        return TodoistTaskResponse(success=True, data=_task_to_data(task))
    except Exception as e:
        logger.exception("Failed to close Todoist task %s", task_id)
        return TodoistTaskResponse(success=False, error=f"Failed to close task: {e}")


@tool()
async def todoist_get_tasks(
    project_id: str | None = None,
    section_id: str | None = None,
    label: str | None = None,
) -> TodoistTaskListResponse:
    """Get active tasks from Todoist, optionally filtered by project, section, or label.

    Args:
        project_id: Optional project ID to filter tasks by.
        section_id: Optional section ID to filter tasks by.
        label: Optional label name to filter tasks by.

    Returns:
        List of active tasks matching the filters.
    """
    try:
        client, error = _get_todoist_client()
        if error or client is None:
            return TodoistTaskListResponse(success=False, error=error)

        kwargs: dict = {}
        if project_id is not None:
            kwargs["project_id"] = project_id
        if section_id is not None:
            kwargs["section_id"] = section_id
        if label is not None:
            kwargs["label"] = label

        tasks_result = client.get_tasks(**kwargs)

        # The SDK may return a tuple or list depending on version
        if isinstance(tasks_result, tuple):
            tasks_iter = tasks_result[0]
        else:
            tasks_iter = tasks_result

        tasks = [_task_to_data(t) for t in tasks_iter]

        logger.info("Retrieved %d Todoist tasks", len(tasks))

        return TodoistTaskListResponse(
            success=True,
            data=TodoistTaskListData(tasks=tasks, total=len(tasks)),
        )
    except Exception as e:
        logger.exception("Failed to get Todoist tasks")
        return TodoistTaskListResponse(success=False, error=f"Failed to get tasks: {e}")


@tool()
async def todoist_list_projects() -> TodoistProjectListResponse:
    """List all projects in the Todoist account.

    Returns:
        List of projects with their IDs and names.
    """
    try:
        client, error = _get_todoist_client()
        if error or client is None:
            return TodoistProjectListResponse(success=False, error=error)

        projects_result = client.get_projects()

        if isinstance(projects_result, tuple):
            projects_iter = projects_result[0]
        else:
            projects_iter = projects_result

        projects = [
            TodoistProjectData(
                id=p.id,
                name=p.name,
                color=getattr(p, "color", None),
                is_favorite=getattr(p, "is_favorite", False),
                url=getattr(p, "url", None),
            )
            for p in projects_iter
        ]

        logger.info("Listed %d Todoist projects", len(projects))

        return TodoistProjectListResponse(
            success=True,
            data=TodoistProjectListData(projects=projects, total=len(projects)),
        )
    except Exception as e:
        logger.exception("Failed to list Todoist projects")
        return TodoistProjectListResponse(
            success=False, error=f"Failed to list projects: {e}"
        )


@tool()
async def todoist_get_comments(task_id: str) -> TodoistCommentListResponse:
    """Get all comments on a Todoist task.

    Args:
        task_id: The ID of the task to get comments for.

    Returns:
        List of comments on the task.
    """
    try:
        client, error = _get_todoist_client()
        if error or client is None:
            return TodoistCommentListResponse(success=False, error=error)

        comments_result = client.get_comments(task_id=task_id)

        if isinstance(comments_result, tuple):
            comments_iter = comments_result[0]
        else:
            comments_iter = comments_result

        comments = [
            TodoistCommentData(
                id=c.id,
                content=c.content,
                task_id=getattr(c, "task_id", None),
                posted_at=getattr(c, "posted_at", None),
            )
            for c in comments_iter
        ]

        logger.info("Retrieved %d comments for Todoist task %s", len(comments), task_id)

        return TodoistCommentListResponse(
            success=True,
            data=TodoistCommentListData(comments=comments, total=len(comments)),
        )
    except Exception as e:
        logger.exception("Failed to get comments for Todoist task %s", task_id)
        return TodoistCommentListResponse(
            success=False, error=f"Failed to get comments: {e}"
        )
