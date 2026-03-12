"""Docker tools for managing containers and images via the local Docker daemon.

Uses the ``docker`` Python SDK (docker-py) to communicate with the Docker
Engine API through the local socket.
"""

from __future__ import annotations

import logging
from typing import Any

from src.humcp.decorator import tool
from src.tools.cloud.schemas import (
    DockerContainerInfo,
    DockerContainerLogsData,
    DockerContainerLogsResponse,
    DockerImageInfo,
    DockerListContainersData,
    DockerListContainersResponse,
    DockerListImagesData,
    DockerListImagesResponse,
    DockerRemoveContainerData,
    DockerRemoveContainerResponse,
    DockerRunContainerData,
    DockerRunContainerResponse,
    DockerStopContainerData,
    DockerStopContainerResponse,
)

try:
    import docker
    from docker.errors import DockerException
except ImportError as err:
    raise ImportError(
        "docker is required for Docker tools. Install with: pip install docker"
    ) from err

logger = logging.getLogger("humcp.tools.docker")


def _get_docker_client():
    """Create a Docker client connected to the local daemon."""
    return docker.from_env()


@tool()
async def docker_list_containers(
    all: bool = False,
) -> DockerListContainersResponse:
    """List Docker containers on the local Docker daemon.

    Returns container metadata including ID, name, image, status, creation
    time, and port mappings.

    Args:
        all: If True, show all containers including stopped ones.
             Defaults to False (only running containers).

    Returns:
        List of container information objects.
    """
    try:
        logger.info("Listing Docker containers all=%s", all)
        client = _get_docker_client()
        containers = client.containers.list(all=all)

        container_list = [
            DockerContainerInfo(
                id=container.id,
                name=container.name,
                image=(
                    container.image.tags[0]
                    if container.image.tags
                    else container.image.id
                ),
                status=container.status,
                created=container.attrs.get("Created"),
                ports=container.ports,
            )
            for container in containers
        ]

        data = DockerListContainersData(
            containers=container_list,
            count=len(container_list),
        )

        logger.info("Listed %d Docker containers", len(container_list))
        return DockerListContainersResponse(success=True, data=data)
    except DockerException as e:
        logger.exception("Failed to list Docker containers")
        return DockerListContainersResponse(
            success=False, error=f"Docker error: {str(e)}"
        )
    except Exception as e:
        logger.exception("Failed to list Docker containers")
        return DockerListContainersResponse(
            success=False, error=f"Failed to list containers: {str(e)}"
        )


@tool()
async def docker_run_container(
    image: str,
    command: str | None = None,
    name: str | None = None,
    environment: dict[str, str] | None = None,
    ports: dict[str, int] | None = None,
    detach: bool = True,
) -> DockerRunContainerResponse:
    """Run a new Docker container from an image.

    Pulls the image if not available locally, then creates and starts a
    container.  The container runs in detached mode by default.

    Args:
        image: Docker image name (e.g. 'python:3.13-slim', 'nginx:latest').
        command: Optional command to run inside the container.
        name: Optional container name. Docker assigns a random name if omitted.
        environment: Optional dict of environment variables to set.
        ports: Optional port mapping dict (container_port -> host_port),
            e.g. {"80": 8080} maps container port 80 to host port 8080.
        detach: Run container in background. Defaults to True.

    Returns:
        Container ID and image information on success.
    """
    try:
        logger.info("Running Docker container image=%s", image)
        client = _get_docker_client()

        kwargs: dict[str, Any] = {
            "image": image,
            "detach": detach,
        }
        if command is not None:
            kwargs["command"] = command
        if name is not None:
            kwargs["name"] = name
        if environment is not None:
            kwargs["environment"] = environment
        if ports is not None:
            kwargs["ports"] = {f"{cp}/tcp": int(hp) for cp, hp in ports.items()}

        container = client.containers.run(**kwargs)

        data = DockerRunContainerData(
            container_id=container.id,
            image=image,
        )

        logger.info("Container started id=%s image=%s", container.id, image)
        return DockerRunContainerResponse(success=True, data=data)
    except DockerException as e:
        logger.exception("Failed to run Docker container")
        return DockerRunContainerResponse(
            success=False, error=f"Docker error: {str(e)}"
        )
    except Exception as e:
        logger.exception("Failed to run Docker container")
        return DockerRunContainerResponse(
            success=False, error=f"Failed to run container: {str(e)}"
        )


@tool()
async def docker_stop_container(
    container_id: str,
    timeout: int = 10,
) -> DockerStopContainerResponse:
    """Stop a running Docker container.

    Sends SIGTERM and waits for the container to stop.  If the container
    does not stop within the timeout, SIGKILL is sent.

    Args:
        container_id: The ID or name of the container to stop.
        timeout: Seconds to wait before sending SIGKILL. Defaults to 10.

    Returns:
        Confirmation message on success.
    """
    try:
        logger.info("Stopping Docker container id=%s timeout=%d", container_id, timeout)
        client = _get_docker_client()
        container = client.containers.get(container_id)
        container.stop(timeout=timeout)

        data = DockerStopContainerData(
            container_id=container_id,
            message=f"Container {container_id} stopped successfully",
        )

        logger.info("Container stopped id=%s", container_id)
        return DockerStopContainerResponse(success=True, data=data)
    except DockerException as e:
        logger.exception("Failed to stop Docker container")
        return DockerStopContainerResponse(
            success=False, error=f"Docker error: {str(e)}"
        )
    except Exception as e:
        logger.exception("Failed to stop Docker container")
        return DockerStopContainerResponse(
            success=False, error=f"Failed to stop container: {str(e)}"
        )


@tool()
async def docker_get_container_logs(
    container_id: str,
    tail: int = 100,
    timestamps: bool = False,
) -> DockerContainerLogsResponse:
    """Get logs from a Docker container.

    Retrieves stdout and stderr output from the container.  Use ``tail``
    to limit the number of lines returned.

    Args:
        container_id: The ID or name of the container.
        tail: Number of lines to return from the end of the logs. Defaults to 100.
        timestamps: Whether to include timestamps in each log line. Defaults to False.

    Returns:
        Container log output as a string.
    """
    try:
        logger.info("Getting logs container=%s tail=%d", container_id, tail)
        client = _get_docker_client()
        container = client.containers.get(container_id)
        logs = container.logs(tail=tail, timestamps=timestamps)

        log_text = (
            logs.decode("utf-8", errors="replace")
            if isinstance(logs, bytes)
            else str(logs)
        )

        data = DockerContainerLogsData(
            container_id=container_id,
            logs=log_text,
            tail=tail,
        )

        logger.info("Got logs container=%s lines=%d", container_id, tail)
        return DockerContainerLogsResponse(success=True, data=data)
    except DockerException as e:
        logger.exception("Failed to get container logs")
        return DockerContainerLogsResponse(
            success=False, error=f"Docker error: {str(e)}"
        )
    except Exception as e:
        logger.exception("Failed to get container logs")
        return DockerContainerLogsResponse(
            success=False, error=f"Failed to get container logs: {str(e)}"
        )


@tool()
async def docker_remove_container(
    container_id: str,
    force: bool = False,
) -> DockerRemoveContainerResponse:
    """Remove a Docker container.

    Removes a stopped container.  Use ``force=True`` to remove a running
    container (it will be killed first).

    Args:
        container_id: The ID or name of the container to remove.
        force: Force removal of a running container. Defaults to False.

    Returns:
        Confirmation message on success.
    """
    try:
        logger.info("Removing Docker container id=%s force=%s", container_id, force)
        client = _get_docker_client()
        container = client.containers.get(container_id)
        container.remove(force=force)

        data = DockerRemoveContainerData(
            container_id=container_id,
            message=f"Container {container_id} removed successfully",
        )

        logger.info("Container removed id=%s", container_id)
        return DockerRemoveContainerResponse(success=True, data=data)
    except DockerException as e:
        logger.exception("Failed to remove Docker container")
        return DockerRemoveContainerResponse(
            success=False, error=f"Docker error: {str(e)}"
        )
    except Exception as e:
        logger.exception("Failed to remove Docker container")
        return DockerRemoveContainerResponse(
            success=False, error=f"Failed to remove container: {str(e)}"
        )


@tool()
async def docker_list_images() -> DockerListImagesResponse:
    """List Docker images available on the local Docker daemon.

    Returns image metadata including ID, tags, size, and creation date.

    Returns:
        List of Docker image information objects.
    """
    try:
        logger.info("Listing Docker images")
        client = _get_docker_client()
        images = client.images.list()

        image_list = [
            DockerImageInfo(
                id=img.id,
                tags=img.tags if img.tags else [],
                size=img.attrs.get("Size"),
                created=img.attrs.get("Created"),
            )
            for img in images
        ]

        data = DockerListImagesData(
            images=image_list,
            count=len(image_list),
        )

        logger.info("Listed %d Docker images", len(image_list))
        return DockerListImagesResponse(success=True, data=data)
    except DockerException as e:
        logger.exception("Failed to list Docker images")
        return DockerListImagesResponse(success=False, error=f"Docker error: {str(e)}")
    except Exception as e:
        logger.exception("Failed to list Docker images")
        return DockerListImagesResponse(
            success=False, error=f"Failed to list images: {str(e)}"
        )
