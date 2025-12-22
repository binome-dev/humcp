import asyncio
import logging

from fastmcp import FastMCP

from src.tools.google.auth import SCOPES, get_google_service

logger = logging.getLogger("humcp.tools.google.tasks")

TASKS_READONLY_SCOPES = [SCOPES["tasks_readonly"]]
TASKS_FULL_SCOPES = [SCOPES["tasks"]]


async def list_task_lists(max_results: int = 100) -> dict:
    """List all task lists for the user."""
    try:

        def _list():
            service = get_google_service("tasks", "v1", TASKS_READONLY_SCOPES)
            results = service.tasklists().list(maxResults=max_results).execute()
            items = results.get("items", [])
            return {
                "task_lists": [
                    {
                        "id": tl["id"],
                        "title": tl.get("title", ""),
                        "updated": tl.get("updated", ""),
                    }
                    for tl in items
                ],
                "total": len(items),
            }

        logger.info("tasks_list_task_lists")
        result = await asyncio.to_thread(_list)
        return {"success": True, "data": result}
    except Exception as e:
        logger.exception("tasks_list_task_lists failed")
        return {"success": False, "error": str(e)}


async def get_task_list(task_list_id: str) -> dict:
    """Get details of a specific task list."""
    try:

        def _get():
            service = get_google_service("tasks", "v1", TASKS_READONLY_SCOPES)
            tl = service.tasklists().get(tasklist=task_list_id).execute()
            return {
                "id": tl["id"],
                "title": tl.get("title", ""),
                "updated": tl.get("updated", ""),
            }

        logger.info("tasks_get_task_list id=%s", task_list_id)
        result = await asyncio.to_thread(_get)
        return {"success": True, "data": result}
    except Exception as e:
        logger.exception("tasks_get_task_list failed")
        return {"success": False, "error": str(e)}


async def create_task_list(title: str) -> dict:
    """Create a new task list."""
    try:

        def _create():
            service = get_google_service("tasks", "v1", TASKS_FULL_SCOPES)
            tl = service.tasklists().insert(body={"title": title}).execute()
            return {
                "id": tl["id"],
                "title": tl.get("title", ""),
                "updated": tl.get("updated", ""),
            }

        logger.info("tasks_create_task_list title=%s", title)
        result = await asyncio.to_thread(_create)
        return {"success": True, "data": result}
    except Exception as e:
        logger.exception("tasks_create_task_list failed")
        return {"success": False, "error": str(e)}


async def delete_task_list(task_list_id: str) -> dict:
    """Delete a task list."""
    try:

        def _delete():
            service = get_google_service("tasks", "v1", TASKS_FULL_SCOPES)
            service.tasklists().delete(tasklist=task_list_id).execute()
            return {"deleted_task_list_id": task_list_id}

        logger.info("tasks_delete_task_list id=%s", task_list_id)
        result = await asyncio.to_thread(_delete)
        return {"success": True, "data": result}
    except Exception as e:
        logger.exception("tasks_delete_task_list failed")
        return {"success": False, "error": str(e)}


async def list_tasks(
    task_list_id: str = "@default",
    show_completed: bool = True,
    show_hidden: bool = False,
    max_results: int = 100,
) -> dict:
    """List tasks in a task list."""
    try:

        def _list():
            service = get_google_service("tasks", "v1", TASKS_READONLY_SCOPES)
            results = (
                service.tasks()
                .list(
                    tasklist=task_list_id,
                    showCompleted=show_completed,
                    showHidden=show_hidden,
                    maxResults=max_results,
                )
                .execute()
            )
            items = results.get("items", [])
            return {
                "tasks": [
                    {
                        "id": t["id"],
                        "title": t.get("title", ""),
                        "notes": t.get("notes", ""),
                        "status": t.get("status", ""),
                        "due": t.get("due", ""),
                        "completed": t.get("completed", ""),
                        "parent": t.get("parent", ""),
                        "position": t.get("position", ""),
                    }
                    for t in items
                ],
                "total": len(items),
            }

        logger.info("tasks_list_tasks list_id=%s", task_list_id)
        result = await asyncio.to_thread(_list)
        return {"success": True, "data": result}
    except Exception as e:
        logger.exception("tasks_list_tasks failed")
        return {"success": False, "error": str(e)}


async def get_task(task_list_id: str, task_id: str) -> dict:
    """Get details of a specific task."""
    try:

        def _get():
            service = get_google_service("tasks", "v1", TASKS_READONLY_SCOPES)
            t = service.tasks().get(tasklist=task_list_id, task=task_id).execute()
            return {
                "id": t["id"],
                "title": t.get("title", ""),
                "notes": t.get("notes", ""),
                "status": t.get("status", ""),
                "due": t.get("due", ""),
                "completed": t.get("completed", ""),
                "parent": t.get("parent", ""),
                "position": t.get("position", ""),
                "links": t.get("links", []),
            }

        logger.info("tasks_get_task list_id=%s task_id=%s", task_list_id, task_id)
        result = await asyncio.to_thread(_get)
        return {"success": True, "data": result}
    except Exception as e:
        logger.exception("tasks_get_task failed")
        return {"success": False, "error": str(e)}


async def create_task(
    task_list_id: str = "@default",
    title: str = "",
    notes: str = "",
    due: str = "",
    parent: str = "",
) -> dict:
    """Create a new task."""
    try:

        def _create():
            service = get_google_service("tasks", "v1", TASKS_FULL_SCOPES)
            body = {"title": title}
            if notes:
                body["notes"] = notes
            if due:
                body["due"] = due

            kwargs = {"tasklist": task_list_id, "body": body}
            if parent:
                kwargs["parent"] = parent

            t = service.tasks().insert(**kwargs).execute()
            return {
                "id": t["id"],
                "title": t.get("title", ""),
                "notes": t.get("notes", ""),
                "status": t.get("status", ""),
                "due": t.get("due", ""),
            }

        logger.info("tasks_create_task title=%s", title)
        result = await asyncio.to_thread(_create)
        return {"success": True, "data": result}
    except Exception as e:
        logger.exception("tasks_create_task failed")
        return {"success": False, "error": str(e)}


async def update_task(
    task_list_id: str,
    task_id: str,
    title: str = "",
    notes: str = "",
    status: str = "",
    due: str = "",
) -> dict:
    """Update an existing task."""
    try:

        def _update():
            service = get_google_service("tasks", "v1", TASKS_FULL_SCOPES)
            # Get current task first
            current = (
                service.tasks().get(tasklist=task_list_id, task=task_id).execute()
            )

            # Update only provided fields
            if title:
                current["title"] = title
            if notes:
                current["notes"] = notes
            if status:
                current["status"] = status
            if due:
                current["due"] = due

            t = (
                service.tasks()
                .update(tasklist=task_list_id, task=task_id, body=current)
                .execute()
            )
            return {
                "id": t["id"],
                "title": t.get("title", ""),
                "notes": t.get("notes", ""),
                "status": t.get("status", ""),
                "due": t.get("due", ""),
                "completed": t.get("completed", ""),
            }

        logger.info("tasks_update_task task_id=%s", task_id)
        result = await asyncio.to_thread(_update)
        return {"success": True, "data": result}
    except Exception as e:
        logger.exception("tasks_update_task failed")
        return {"success": False, "error": str(e)}


async def delete_task(task_list_id: str, task_id: str) -> dict:
    """Delete a task."""
    try:

        def _delete():
            service = get_google_service("tasks", "v1", TASKS_FULL_SCOPES)
            service.tasks().delete(tasklist=task_list_id, task=task_id).execute()
            return {"deleted_task_id": task_id}

        logger.info("tasks_delete_task task_id=%s", task_id)
        result = await asyncio.to_thread(_delete)
        return {"success": True, "data": result}
    except Exception as e:
        logger.exception("tasks_delete_task failed")
        return {"success": False, "error": str(e)}


async def complete_task(task_list_id: str, task_id: str) -> dict:
    """Mark a task as completed."""
    return await update_task(task_list_id, task_id, status="completed")


async def clear_completed_tasks(task_list_id: str = "@default") -> dict:
    """Clear all completed tasks from a task list."""
    try:

        def _clear():
            service = get_google_service("tasks", "v1", TASKS_FULL_SCOPES)
            service.tasks().clear(tasklist=task_list_id).execute()
            return {"cleared": True, "task_list_id": task_list_id}

        logger.info("tasks_clear_completed list_id=%s", task_list_id)
        result = await asyncio.to_thread(_clear)
        return {"success": True, "data": result}
    except Exception as e:
        logger.exception("tasks_clear_completed failed")
        return {"success": False, "error": str(e)}


def register_tools(mcp: FastMCP) -> None:
    """Register all Google Tasks tools with the MCP server."""
    mcp.tool(name="tasks_list_task_lists")(list_task_lists)
    mcp.tool(name="tasks_get_task_list")(get_task_list)
    mcp.tool(name="tasks_create_task_list")(create_task_list)
    mcp.tool(name="tasks_delete_task_list")(delete_task_list)
    mcp.tool(name="tasks_list_tasks")(list_tasks)
    mcp.tool(name="tasks_get_task")(get_task)
    mcp.tool(name="tasks_create_task")(create_task)
    mcp.tool(name="tasks_update_task")(update_task)
    mcp.tool(name="tasks_delete_task")(delete_task)
    mcp.tool(name="tasks_complete_task")(complete_task)
    mcp.tool(name="tasks_clear_completed")(clear_completed_tasks)
