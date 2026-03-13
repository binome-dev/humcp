"""ClickUp project management tools for task and workspace management.

Uses the ClickUp API v2. Requires a CLICKUP_API_KEY environment variable
(personal API token or OAuth2 token).

API Reference: https://developer.clickup.com/reference
"""

from __future__ import annotations

import logging

import httpx

from src.humcp.credentials import resolve_credential
from src.humcp.decorator import tool
from src.tools.project_management.schemas import (
    ClickUpSpaceData,
    ClickUpSpaceListData,
    ClickUpSpaceListResponse,
    ClickUpTaskData,
    ClickUpTaskListData,
    ClickUpTaskListResponse,
    ClickUpTaskResponse,
)

logger = logging.getLogger("humcp.tools.clickup")

CLICKUP_BASE_URL = "https://api.clickup.com/api/v2"


async def _get_headers() -> tuple[dict[str, str] | None, str | None]:
    """Build ClickUp API headers from environment variables.

    Returns:
        A tuple of (headers_dict, error_message).
    """
    api_key = await resolve_credential("CLICKUP_API_KEY")
    if not api_key:
        return (
            None,
            "ClickUp API key not configured. Set CLICKUP_API_KEY environment variable.",
        )
    return {"Authorization": api_key, "Content-Type": "application/json"}, None


def _parse_task(task: dict) -> ClickUpTaskData:
    """Parse a ClickUp task API response into a ClickUpTaskData model.

    Args:
        task: Raw task dict from the ClickUp API.

    Returns:
        Parsed ClickUpTaskData.
    """
    assignees = [a.get("username", a.get("id", "")) for a in task.get("assignees", [])]

    priority_obj = task.get("priority")
    priority_str = (
        priority_obj.get("priority") if isinstance(priority_obj, dict) else None
    )

    return ClickUpTaskData(
        id=task["id"],
        name=task["name"],
        description=task.get("description"),
        status=task.get("status", {}).get("status") if task.get("status") else None,
        priority=priority_str,
        assignees=assignees,
        due_date=task.get("due_date"),
        url=task.get("url"),
    )


@tool()
async def clickup_create_task(
    list_id: str,
    name: str,
    description: str = "",
    priority: int | None = None,
    due_date: int | None = None,
    assignees: list[int] | None = None,
) -> ClickUpTaskResponse:
    """Create a new task in a ClickUp list.

    Args:
        list_id: The ID of the ClickUp list to add the task to.
        name: The name of the task.
        description: The description of the task (Markdown supported).
        priority: Priority level (1=urgent, 2=high, 3=normal, 4=low). None for no priority.
        due_date: Due date as Unix timestamp in milliseconds.
        assignees: List of user IDs to assign to the task.

    Returns:
        Details of the newly created task.
    """
    try:
        headers, error = await _get_headers()
        if error or headers is None:
            return ClickUpTaskResponse(success=False, error=error)

        payload: dict = {"name": name, "description": description}
        if priority is not None:
            payload["priority"] = priority
        if due_date is not None:
            payload["due_date"] = due_date
        if assignees:
            payload["assignees"] = assignees

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{CLICKUP_BASE_URL}/list/{list_id}/task",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            task = response.json()

        data = _parse_task(task)

        logger.info("Created ClickUp task %s in list %s", task["id"], list_id)
        return ClickUpTaskResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Failed to create ClickUp task in list %s", list_id)
        return ClickUpTaskResponse(success=False, error=f"Failed to create task: {e}")


@tool()
async def clickup_get_task(task_id: str) -> ClickUpTaskResponse:
    """Retrieve details of a specific ClickUp task by its ID.

    Args:
        task_id: The ID of the ClickUp task.

    Returns:
        Task details including name, description, status, priority, and assignees.
    """
    try:
        headers, error = await _get_headers()
        if error or headers is None:
            return ClickUpTaskResponse(success=False, error=error)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{CLICKUP_BASE_URL}/task/{task_id}",
                headers=headers,
            )
            response.raise_for_status()
            task = response.json()

        data = _parse_task(task)

        return ClickUpTaskResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Failed to get ClickUp task %s", task_id)
        return ClickUpTaskResponse(success=False, error=f"Failed to get task: {e}")


@tool()
async def clickup_update_task(
    task_id: str,
    name: str | None = None,
    description: str | None = None,
    status: str | None = None,
    priority: int | None = None,
    due_date: int | None = None,
) -> ClickUpTaskResponse:
    """Update an existing ClickUp task.

    Args:
        task_id: The ID of the task to update.
        name: New task name.
        description: New task description.
        status: New status name (must match a status in the task's list).
        priority: New priority (1=urgent, 2=high, 3=normal, 4=low). Use 0 to clear.
        due_date: New due date as Unix timestamp in milliseconds.

    Returns:
        Updated task details.
    """
    try:
        headers, error = await _get_headers()
        if error or headers is None:
            return ClickUpTaskResponse(success=False, error=error)

        payload: dict = {}
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        if status is not None:
            payload["status"] = status
        if priority is not None:
            payload["priority"] = priority
        if due_date is not None:
            payload["due_date"] = due_date

        if not payload:
            return ClickUpTaskResponse(
                success=False, error="At least one field must be provided to update."
            )

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.put(
                f"{CLICKUP_BASE_URL}/task/{task_id}",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            task = response.json()

        data = _parse_task(task)

        logger.info("Updated ClickUp task %s", task_id)
        return ClickUpTaskResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Failed to update ClickUp task %s", task_id)
        return ClickUpTaskResponse(success=False, error=f"Failed to update task: {e}")


@tool()
async def clickup_list_tasks(
    list_id: str,
    page: int = 0,
    statuses: list[str] | None = None,
    assignees: list[str] | None = None,
) -> ClickUpTaskListResponse:
    """List tasks in a ClickUp list. Returns up to 100 tasks per page.

    Args:
        list_id: The ID of the ClickUp list.
        page: Page number for pagination (0-indexed).
        statuses: Filter by status names (e.g., ["open", "in progress"]).
        assignees: Filter by assignee user IDs.

    Returns:
        List of tasks in the list.
    """
    try:
        headers, error = await _get_headers()
        if error or headers is None:
            return ClickUpTaskListResponse(success=False, error=error)

        params: dict = {"page": page}
        if statuses:
            for i, s in enumerate(statuses):
                params["statuses[]"] = (
                    s if i == 0 else params.get("statuses[]", "") + f"&statuses[]={s}"
                )
        if assignees:
            for _a in assignees:
                params.setdefault("assignees[]", [])

        # ClickUp uses array query params - build URL manually
        query_parts = [f"page={page}"]
        if statuses:
            for s in statuses:
                query_parts.append(f"statuses[]={s}")
        if assignees:
            for a in assignees:
                query_parts.append(f"assignees[]={a}")

        url = f"{CLICKUP_BASE_URL}/list/{list_id}/task?{'&'.join(query_parts)}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()

        tasks = [_parse_task(t) for t in result.get("tasks", [])]

        logger.info("Listed %d ClickUp tasks in list %s", len(tasks), list_id)

        return ClickUpTaskListResponse(
            success=True,
            data=ClickUpTaskListData(tasks=tasks, total=len(tasks)),
        )
    except Exception as e:
        logger.exception("Failed to list ClickUp tasks in list %s", list_id)
        return ClickUpTaskListResponse(
            success=False, error=f"Failed to list tasks: {e}"
        )


@tool()
async def clickup_list_spaces(
    team_id: str,
) -> ClickUpSpaceListResponse:
    """List spaces in a ClickUp workspace (team).

    Args:
        team_id: The ID of the ClickUp workspace/team.

    Returns:
        List of spaces in the workspace.
    """
    try:
        headers, error = await _get_headers()
        if error or headers is None:
            return ClickUpSpaceListResponse(success=False, error=error)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{CLICKUP_BASE_URL}/team/{team_id}/space",
                headers=headers,
            )
            response.raise_for_status()
            result = response.json()

        spaces = [
            ClickUpSpaceData(
                id=space["id"],
                name=space["name"],
                private=space.get("private", False),
            )
            for space in result.get("spaces", [])
        ]

        logger.info("Listed %d ClickUp spaces in team %s", len(spaces), team_id)

        return ClickUpSpaceListResponse(
            success=True,
            data=ClickUpSpaceListData(spaces=spaces, total=len(spaces)),
        )
    except Exception as e:
        logger.exception("Failed to list ClickUp spaces in team %s", team_id)
        return ClickUpSpaceListResponse(
            success=False, error=f"Failed to list spaces: {e}"
        )
