"""Daytona tools for managing cloud development workspaces.

Supports creating, listing, starting, stopping, deleting workspaces, and
running commands inside them via the Daytona REST API.

Environment variables:
    DAYTONA_API_KEY: Bearer token for Daytona API authentication.
    DAYTONA_SERVER_URL: Daytona server URL (default: https://api.daytona.io).
"""

from __future__ import annotations

import logging
import os

from src.humcp.decorator import tool
from src.tools.cloud.schemas import (
    DaytonaCreateWorkspaceData,
    DaytonaCreateWorkspaceResponse,
    DaytonaDeleteWorkspaceData,
    DaytonaDeleteWorkspaceResponse,
    DaytonaListWorkspacesData,
    DaytonaListWorkspacesResponse,
    DaytonaRunCommandData,
    DaytonaRunCommandResponse,
    DaytonaStartStopWorkspaceData,
    DaytonaStartStopWorkspaceResponse,
    DaytonaWorkspaceInfo,
)

try:
    import httpx
except ImportError as err:
    raise ImportError(
        "httpx is required for Daytona tools. Install with: pip install httpx"
    ) from err

logger = logging.getLogger("humcp.tools.daytona")


def _get_daytona_config() -> tuple[str, dict[str, str]]:
    """Resolve Daytona server URL and authorization headers from environment.

    Returns:
        Tuple of (base_url, headers).
    """
    api_key = os.getenv("DAYTONA_API_KEY")
    server_url = os.getenv("DAYTONA_SERVER_URL", "https://api.daytona.io")
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return server_url.rstrip("/"), headers


def _check_configured() -> str | None:
    """Return an error message if Daytona is not configured, else None."""
    if not os.getenv("DAYTONA_API_KEY"):
        return "Daytona API key not configured. Set DAYTONA_API_KEY."
    return None


@tool()
async def daytona_create_workspace(
    repo_url: str,
    name: str | None = None,
) -> DaytonaCreateWorkspaceResponse:
    """Create a new Daytona workspace from a Git repository URL.

    Provisions a cloud development environment with the repository code
    pre-cloned and ready to use.

    Args:
        repo_url: The Git repository URL to initialize the workspace from
            (e.g. 'https://github.com/owner/repo').
        name: Optional workspace name. Auto-generated if omitted.

    Returns:
        Created workspace ID and repository URL.
    """
    try:
        err = _check_configured()
        if err:
            return DaytonaCreateWorkspaceResponse(success=False, error=err)

        base_url, headers = _get_daytona_config()

        logger.info("Creating Daytona workspace repo_url=%s name=%s", repo_url, name)
        payload: dict = {"repositories": [{"url": repo_url}]}
        if name:
            payload["name"] = name

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{base_url}/workspaces",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            result = response.json()

        workspace_id = result.get("id", result.get("workspaceId", "unknown"))
        data = DaytonaCreateWorkspaceData(
            workspace_id=str(workspace_id),
            repo_url=repo_url,
        )

        logger.info("Workspace created id=%s", workspace_id)
        return DaytonaCreateWorkspaceResponse(success=True, data=data)
    except httpx.HTTPStatusError as e:
        logger.exception("Daytona API returned an error")
        return DaytonaCreateWorkspaceResponse(
            success=False,
            error=f"Daytona API error {e.response.status_code}: {e.response.text}",
        )
    except Exception as e:
        logger.exception("Failed to create Daytona workspace")
        return DaytonaCreateWorkspaceResponse(
            success=False, error=f"Failed to create workspace: {str(e)}"
        )


@tool()
async def daytona_list_workspaces() -> DaytonaListWorkspacesResponse:
    """List all Daytona workspaces.

    Returns workspace metadata including ID, name, state, and repository URL.

    Returns:
        List of workspace information objects.
    """
    try:
        err = _check_configured()
        if err:
            return DaytonaListWorkspacesResponse(success=False, error=err)

        base_url, headers = _get_daytona_config()

        logger.info("Listing Daytona workspaces")
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{base_url}/workspaces",
                headers=headers,
            )
            response.raise_for_status()
            result = response.json()

        workspaces_raw = result if isinstance(result, list) else result.get("items", [])
        workspaces = [
            DaytonaWorkspaceInfo(
                id=str(ws.get("id", ws.get("workspaceId", "unknown"))),
                name=ws.get("name"),
                state=ws.get("state"),
                repo_url=ws.get("repository", {}).get("url")
                if isinstance(ws.get("repository"), dict)
                else None,
            )
            for ws in workspaces_raw
        ]

        data = DaytonaListWorkspacesData(
            workspaces=workspaces,
            count=len(workspaces),
        )

        logger.info("Listed %d Daytona workspaces", len(workspaces))
        return DaytonaListWorkspacesResponse(success=True, data=data)
    except httpx.HTTPStatusError as e:
        logger.exception("Daytona API returned an error")
        return DaytonaListWorkspacesResponse(
            success=False,
            error=f"Daytona API error {e.response.status_code}: {e.response.text}",
        )
    except Exception as e:
        logger.exception("Failed to list Daytona workspaces")
        return DaytonaListWorkspacesResponse(
            success=False, error=f"Failed to list workspaces: {str(e)}"
        )


@tool()
async def daytona_run_command(
    workspace_id: str,
    command: str,
) -> DaytonaRunCommandResponse:
    """Run a shell command inside a Daytona workspace.

    Executes the command in the workspace's default project container and
    returns the output and exit code.

    Args:
        workspace_id: The ID of the workspace to run the command in.
        command: The shell command to execute.

    Returns:
        Command output and exit code.
    """
    try:
        err = _check_configured()
        if err:
            return DaytonaRunCommandResponse(success=False, error=err)

        base_url, headers = _get_daytona_config()

        logger.info(
            "Running command in Daytona workspace=%s command=%s",
            workspace_id,
            command[:100],
        )
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{base_url}/workspaces/{workspace_id}/exec",
                headers=headers,
                json={"command": command},
            )
            response.raise_for_status()
            result = response.json()

        output = result.get("output", result.get("result", ""))
        exit_code = result.get("exitCode", result.get("exit_code"))

        data = DaytonaRunCommandData(
            workspace_id=workspace_id,
            output=str(output),
            exit_code=exit_code,
        )

        logger.info(
            "Command completed workspace=%s exit_code=%s", workspace_id, exit_code
        )
        return DaytonaRunCommandResponse(success=True, data=data)
    except httpx.HTTPStatusError as e:
        logger.exception("Daytona API returned an error")
        return DaytonaRunCommandResponse(
            success=False,
            error=f"Daytona API error {e.response.status_code}: {e.response.text}",
        )
    except Exception as e:
        logger.exception("Failed to run command in Daytona workspace")
        return DaytonaRunCommandResponse(
            success=False, error=f"Failed to run command: {str(e)}"
        )


@tool()
async def daytona_start_workspace(
    workspace_id: str,
) -> DaytonaStartStopWorkspaceResponse:
    """Start a stopped Daytona workspace.

    Resumes a previously stopped workspace, restoring its state and files.

    Args:
        workspace_id: The ID of the workspace to start.

    Returns:
        Confirmation that the workspace is starting.
    """
    try:
        err = _check_configured()
        if err:
            return DaytonaStartStopWorkspaceResponse(success=False, error=err)

        base_url, headers = _get_daytona_config()

        logger.info("Starting Daytona workspace id=%s", workspace_id)
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{base_url}/workspaces/{workspace_id}/start",
                headers=headers,
            )
            response.raise_for_status()

        data = DaytonaStartStopWorkspaceData(
            workspace_id=workspace_id,
            message=f"Workspace {workspace_id} is starting",
        )

        logger.info("Workspace start initiated id=%s", workspace_id)
        return DaytonaStartStopWorkspaceResponse(success=True, data=data)
    except httpx.HTTPStatusError as e:
        logger.exception("Daytona API returned an error")
        return DaytonaStartStopWorkspaceResponse(
            success=False,
            error=f"Daytona API error {e.response.status_code}: {e.response.text}",
        )
    except Exception as e:
        logger.exception("Failed to start Daytona workspace")
        return DaytonaStartStopWorkspaceResponse(
            success=False, error=f"Failed to start workspace: {str(e)}"
        )


@tool()
async def daytona_stop_workspace(
    workspace_id: str,
) -> DaytonaStartStopWorkspaceResponse:
    """Stop a running Daytona workspace.

    Pauses the workspace to save resources.  Files and state are preserved
    and the workspace can be restarted later.

    Args:
        workspace_id: The ID of the workspace to stop.

    Returns:
        Confirmation that the workspace is stopping.
    """
    try:
        err = _check_configured()
        if err:
            return DaytonaStartStopWorkspaceResponse(success=False, error=err)

        base_url, headers = _get_daytona_config()

        logger.info("Stopping Daytona workspace id=%s", workspace_id)
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{base_url}/workspaces/{workspace_id}/stop",
                headers=headers,
            )
            response.raise_for_status()

        data = DaytonaStartStopWorkspaceData(
            workspace_id=workspace_id,
            message=f"Workspace {workspace_id} is stopping",
        )

        logger.info("Workspace stop initiated id=%s", workspace_id)
        return DaytonaStartStopWorkspaceResponse(success=True, data=data)
    except httpx.HTTPStatusError as e:
        logger.exception("Daytona API returned an error")
        return DaytonaStartStopWorkspaceResponse(
            success=False,
            error=f"Daytona API error {e.response.status_code}: {e.response.text}",
        )
    except Exception as e:
        logger.exception("Failed to stop Daytona workspace")
        return DaytonaStartStopWorkspaceResponse(
            success=False, error=f"Failed to stop workspace: {str(e)}"
        )


@tool()
async def daytona_delete_workspace(
    workspace_id: str,
) -> DaytonaDeleteWorkspaceResponse:
    """Delete a Daytona workspace permanently.

    Removes the workspace and all associated resources.  This action
    cannot be undone.

    Args:
        workspace_id: The ID of the workspace to delete.

    Returns:
        Confirmation that the workspace was deleted.
    """
    try:
        err = _check_configured()
        if err:
            return DaytonaDeleteWorkspaceResponse(success=False, error=err)

        base_url, headers = _get_daytona_config()

        logger.info("Deleting Daytona workspace id=%s", workspace_id)
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.delete(
                f"{base_url}/workspaces/{workspace_id}",
                headers=headers,
            )
            response.raise_for_status()

        data = DaytonaDeleteWorkspaceData(
            workspace_id=workspace_id,
            message=f"Workspace {workspace_id} deleted successfully",
        )

        logger.info("Workspace deleted id=%s", workspace_id)
        return DaytonaDeleteWorkspaceResponse(success=True, data=data)
    except httpx.HTTPStatusError as e:
        logger.exception("Daytona API returned an error")
        return DaytonaDeleteWorkspaceResponse(
            success=False,
            error=f"Daytona API error {e.response.status_code}: {e.response.text}",
        )
    except Exception as e:
        logger.exception("Failed to delete Daytona workspace")
        return DaytonaDeleteWorkspaceResponse(
            success=False, error=f"Failed to delete workspace: {str(e)}"
        )
