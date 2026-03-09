"""Pydantic output schemas for Google Tasks tools."""

from typing import Any

from pydantic import BaseModel, Field

from src.humcp.schemas import ToolResponse


class TaskListInfo(BaseModel):
    """Basic task list information."""

    id: str = Field(..., description="Task list ID")
    title: str = Field("", description="Task list title")
    updated: str = Field("", description="Last updated time")


class TaskInfo(BaseModel):
    """Information about a task."""

    id: str = Field(..., description="Task ID")
    title: str = Field("", description="Task title")
    notes: str = Field("", description="Task notes")
    status: str = Field("", description="Task status")
    due: str = Field("", description="Due date")
    completed: str = Field("", description="Completion time")
    parent: str = Field("", description="Parent task ID")
    position: str = Field("", description="Task position")


class TaskDetailed(BaseModel):
    """Detailed task information."""

    id: str = Field(..., description="Task ID")
    title: str = Field("", description="Task title")
    notes: str = Field("", description="Task notes")
    status: str = Field("", description="Task status")
    due: str = Field("", description="Due date")
    completed: str = Field("", description="Completion time")
    parent: str = Field("", description="Parent task ID")
    position: str = Field("", description="Task position")
    links: list[Any] = Field(default_factory=list, description="Task links")


class TaskCreated(BaseModel):
    """Information about a created task."""

    id: str = Field(..., description="Task ID")
    title: str = Field("", description="Task title")
    notes: str = Field("", description="Task notes")
    status: str = Field("", description="Task status")
    due: str = Field("", description="Due date")


class TaskUpdated(BaseModel):
    """Information about an updated task."""

    id: str = Field(..., description="Task ID")
    title: str = Field("", description="Task title")
    notes: str = Field("", description="Task notes")
    status: str = Field("", description="Task status")
    due: str = Field("", description="Due date")
    completed: str = Field("", description="Completion time")


class TaskDeleted(BaseModel):
    """Information about a deleted task."""

    deleted_task_id: str = Field(..., description="Deleted task ID")


class TaskListDeleted(BaseModel):
    """Information about a deleted task list."""

    deleted_task_list_id: str = Field(..., description="Deleted task list ID")


class TasksClearedCompleted(BaseModel):
    """Information about cleared completed tasks."""

    cleared: bool = Field(..., description="Whether clearing succeeded")
    task_list_id: str = Field(..., description="Task list ID")


class TasksListTaskListsData(BaseModel):
    """Output data for google_tasks_list_task_lists tool."""

    task_lists: list[TaskListInfo] = Field(..., description="List of task lists")
    total: int = Field(..., description="Total number of task lists")


class TasksListTasksData(BaseModel):
    """Output data for google_tasks_list_tasks tool."""

    tasks: list[TaskInfo] = Field(..., description="List of tasks")
    total: int = Field(..., description="Total number of tasks")


# Tasks Responses
class TasksListTaskListsResponse(ToolResponse[TasksListTaskListsData]):
    """Response for google_tasks_list_task_lists tool."""

    pass


class TasksGetTaskListResponse(ToolResponse[TaskListInfo]):
    """Response for google_tasks_get_task_list tool."""

    pass


class TasksCreateTaskListResponse(ToolResponse[TaskListInfo]):
    """Response for google_tasks_create_task_list tool."""

    pass


class TasksDeleteTaskListResponse(ToolResponse[TaskListDeleted]):
    """Response for google_tasks_delete_task_list tool."""

    pass


class TasksListTasksResponse(ToolResponse[TasksListTasksData]):
    """Response for google_tasks_list_tasks tool."""

    pass


class TasksGetTaskResponse(ToolResponse[TaskDetailed]):
    """Response for google_tasks_get_task tool."""

    pass


class TasksCreateTaskResponse(ToolResponse[TaskCreated]):
    """Response for google_tasks_create_task tool."""

    pass


class TasksUpdateTaskResponse(ToolResponse[TaskUpdated]):
    """Response for google_tasks_update_task tool."""

    pass


class TasksDeleteTaskResponse(ToolResponse[TaskDeleted]):
    """Response for google_tasks_delete_task tool."""

    pass


class TasksClearCompletedResponse(ToolResponse[TasksClearedCompleted]):
    """Response for google_tasks_clear_completed tool."""

    pass
