"""Apache Airflow tools for managing DAGs, DAG runs, and task instances via the stable REST API (v1).

Environment variables:
    AIRFLOW_BASE_URL: Base URL of the Airflow webserver (default: http://localhost:8080).
    AIRFLOW_USERNAME: Username for basic authentication.
    AIRFLOW_PASSWORD: Password for basic authentication.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from src.humcp.decorator import tool
from src.tools.cloud.schemas import (
    AirflowDagInfo,
    AirflowDagRunData,
    AirflowDagRunResponse,
    AirflowListDagsData,
    AirflowListDagsResponse,
    AirflowListTaskInstancesData,
    AirflowListTaskInstancesResponse,
    AirflowPauseDagData,
    AirflowPauseDagResponse,
    AirflowTaskInstanceInfo,
    AirflowTriggerDagData,
    AirflowTriggerDagResponse,
)

try:
    import httpx
except ImportError as err:
    raise ImportError(
        "httpx is required for Airflow tools. Install with: pip install httpx"
    ) from err

logger = logging.getLogger("humcp.tools.airflow")


def _get_airflow_config() -> tuple[str, httpx.BasicAuth | None]:
    """Resolve Airflow base URL and authentication from environment.

    Returns:
        Tuple of (base_url, auth).
    """
    base_url = os.getenv("AIRFLOW_BASE_URL", "http://localhost:8080")
    username = os.getenv("AIRFLOW_USERNAME")
    password = os.getenv("AIRFLOW_PASSWORD")
    auth = httpx.BasicAuth(username, password) if username and password else None
    return base_url.rstrip("/"), auth


def _check_configured() -> str | None:
    """Return an error message if Airflow is not configured, else None."""
    if not os.getenv("AIRFLOW_BASE_URL"):
        return "Airflow not configured. Set AIRFLOW_BASE_URL."
    return None


@tool()
async def airflow_list_dags(
    only_active: bool = True,
) -> AirflowListDagsResponse:
    """List all DAGs in the Airflow instance.

    Retrieves DAG metadata including schedule, pause state, owners, and tags
    from the Airflow stable REST API (``/api/v1/dags``).

    Args:
        only_active: If True, only return active (unpaused) DAGs. Defaults to True.

    Returns:
        List of DAG information objects.
    """
    try:
        err = _check_configured()
        if err:
            return AirflowListDagsResponse(success=False, error=err)

        base_url, auth = _get_airflow_config()

        logger.info("Listing Airflow DAGs only_active=%s", only_active)
        params: dict[str, Any] = {}
        if only_active:
            params["only_active"] = "true"

        async with httpx.AsyncClient(timeout=30, auth=auth) as client:
            response = await client.get(
                f"{base_url}/api/v1/dags",
                headers={"Content-Type": "application/json"},
                params=params,
            )
            response.raise_for_status()
            result = response.json()

        dags = [
            AirflowDagInfo(
                dag_id=dag["dag_id"],
                description=dag.get("description"),
                is_paused=dag.get("is_paused"),
                is_active=dag.get("is_active"),
                file_token=dag.get("file_token"),
                owners=dag.get("owners"),
                schedule_interval=dag.get("schedule_interval", {}).get("value")
                if isinstance(dag.get("schedule_interval"), dict)
                else dag.get("schedule_interval"),
                tags=[t["name"] for t in dag.get("tags", []) if isinstance(t, dict)]
                if dag.get("tags")
                else None,
            )
            for dag in result.get("dags", [])
        ]

        data = AirflowListDagsData(
            dags=dags,
            count=len(dags),
        )

        logger.info("Listed %d Airflow DAGs", len(dags))
        return AirflowListDagsResponse(success=True, data=data)
    except httpx.HTTPStatusError as e:
        logger.exception("Airflow API returned an error")
        return AirflowListDagsResponse(
            success=False,
            error=f"Airflow API error {e.response.status_code}: {e.response.text}",
        )
    except Exception as e:
        logger.exception("Failed to list Airflow DAGs")
        return AirflowListDagsResponse(
            success=False, error=f"Failed to list DAGs: {str(e)}"
        )


@tool()
async def airflow_trigger_dag(
    dag_id: str,
    conf: dict[str, Any] | None = None,
    logical_date: str | None = None,
    note: str | None = None,
) -> AirflowTriggerDagResponse:
    """Trigger a new Airflow DAG run.

    Creates a DAG run via ``POST /api/v1/dags/{dag_id}/dagRuns``.  An optional
    JSON configuration dict can be passed to parameterise the run.

    Args:
        dag_id: The identifier of the DAG to trigger.
        conf: Optional configuration dict to pass to the DAG run.
        logical_date: Optional logical date in ISO 8601 format for the DAG run.
        note: Optional note to attach to the DAG run.

    Returns:
        DAG run identifier, state, and execution date.
    """
    try:
        err = _check_configured()
        if err:
            return AirflowTriggerDagResponse(success=False, error=err)

        base_url, auth = _get_airflow_config()

        logger.info("Triggering Airflow DAG dag_id=%s", dag_id)
        payload: dict[str, Any] = {}
        if conf is not None:
            payload["conf"] = conf
        if logical_date is not None:
            payload["logical_date"] = logical_date
        if note is not None:
            payload["note"] = note

        async with httpx.AsyncClient(timeout=30, auth=auth) as client:
            response = await client.post(
                f"{base_url}/api/v1/dags/{dag_id}/dagRuns",
                headers={"Content-Type": "application/json"},
                json=payload,
            )
            response.raise_for_status()
            result = response.json()

        data = AirflowTriggerDagData(
            dag_id=dag_id,
            dag_run_id=result.get("dag_run_id", "unknown"),
            state=result.get("state"),
            execution_date=result.get("execution_date") or result.get("logical_date"),
        )

        logger.info("DAG triggered dag_id=%s run_id=%s", dag_id, data.dag_run_id)
        return AirflowTriggerDagResponse(success=True, data=data)
    except httpx.HTTPStatusError as e:
        logger.exception("Airflow API returned an error")
        return AirflowTriggerDagResponse(
            success=False,
            error=f"Airflow API error {e.response.status_code}: {e.response.text}",
        )
    except Exception as e:
        logger.exception("Failed to trigger Airflow DAG")
        return AirflowTriggerDagResponse(
            success=False, error=f"Failed to trigger DAG: {str(e)}"
        )


@tool()
async def airflow_get_dag_run(
    dag_id: str,
    run_id: str,
) -> AirflowDagRunResponse:
    """Get the status of a specific Airflow DAG run.

    Retrieves run details including state, start/end dates from
    ``GET /api/v1/dags/{dag_id}/dagRuns/{run_id}``.

    Args:
        dag_id: The DAG identifier.
        run_id: The DAG run identifier (dag_run_id).

    Returns:
        DAG run state and timing details.
    """
    try:
        err = _check_configured()
        if err:
            return AirflowDagRunResponse(success=False, error=err)

        base_url, auth = _get_airflow_config()

        logger.info("Getting Airflow DAG run dag_id=%s run_id=%s", dag_id, run_id)
        async with httpx.AsyncClient(timeout=30, auth=auth) as client:
            response = await client.get(
                f"{base_url}/api/v1/dags/{dag_id}/dagRuns/{run_id}",
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            result = response.json()

        data = AirflowDagRunData(
            dag_id=dag_id,
            dag_run_id=result.get("dag_run_id", run_id),
            state=result.get("state", "unknown"),
            execution_date=result.get("execution_date") or result.get("logical_date"),
            start_date=result.get("start_date"),
            end_date=result.get("end_date"),
        )

        logger.info(
            "DAG run status dag_id=%s run_id=%s state=%s",
            dag_id,
            run_id,
            data.state,
        )
        return AirflowDagRunResponse(success=True, data=data)
    except httpx.HTTPStatusError as e:
        logger.exception("Airflow API returned an error")
        return AirflowDagRunResponse(
            success=False,
            error=f"Airflow API error {e.response.status_code}: {e.response.text}",
        )
    except Exception as e:
        logger.exception("Failed to get Airflow DAG run")
        return AirflowDagRunResponse(
            success=False, error=f"Failed to get DAG run: {str(e)}"
        )


@tool()
async def airflow_list_task_instances(
    dag_id: str,
    run_id: str,
) -> AirflowListTaskInstancesResponse:
    """List task instances for a specific Airflow DAG run.

    Returns the individual task states within a DAG run, useful for
    debugging failures or monitoring progress.

    Args:
        dag_id: The DAG identifier.
        run_id: The DAG run identifier (dag_run_id).

    Returns:
        List of task instance details including state, duration, and operator.
    """
    try:
        err = _check_configured()
        if err:
            return AirflowListTaskInstancesResponse(success=False, error=err)

        base_url, auth = _get_airflow_config()

        logger.info("Listing task instances dag_id=%s run_id=%s", dag_id, run_id)
        async with httpx.AsyncClient(timeout=30, auth=auth) as client:
            response = await client.get(
                f"{base_url}/api/v1/dags/{dag_id}/dagRuns/{run_id}/taskInstances",
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            result = response.json()

        task_instances = [
            AirflowTaskInstanceInfo(
                task_id=ti["task_id"],
                state=ti.get("state"),
                start_date=ti.get("start_date"),
                end_date=ti.get("end_date"),
                duration=ti.get("duration"),
                try_number=ti.get("try_number"),
                operator=ti.get("operator"),
            )
            for ti in result.get("task_instances", [])
        ]

        data = AirflowListTaskInstancesData(
            dag_id=dag_id,
            dag_run_id=run_id,
            task_instances=task_instances,
            count=len(task_instances),
        )

        logger.info(
            "Listed %d task instances for dag_id=%s run_id=%s",
            len(task_instances),
            dag_id,
            run_id,
        )
        return AirflowListTaskInstancesResponse(success=True, data=data)
    except httpx.HTTPStatusError as e:
        logger.exception("Airflow API returned an error")
        return AirflowListTaskInstancesResponse(
            success=False,
            error=f"Airflow API error {e.response.status_code}: {e.response.text}",
        )
    except Exception as e:
        logger.exception("Failed to list task instances")
        return AirflowListTaskInstancesResponse(
            success=False, error=f"Failed to list task instances: {str(e)}"
        )


@tool()
async def airflow_pause_dag(
    dag_id: str,
) -> AirflowPauseDagResponse:
    """Pause an Airflow DAG to prevent new runs from being scheduled.

    Sets ``is_paused=true`` on the DAG via ``PATCH /api/v1/dags/{dag_id}``.

    Args:
        dag_id: The DAG identifier to pause.

    Returns:
        Confirmation of pause state.
    """
    try:
        err = _check_configured()
        if err:
            return AirflowPauseDagResponse(success=False, error=err)

        base_url, auth = _get_airflow_config()

        logger.info("Pausing Airflow DAG dag_id=%s", dag_id)
        async with httpx.AsyncClient(timeout=30, auth=auth) as client:
            response = await client.patch(
                f"{base_url}/api/v1/dags/{dag_id}",
                headers={"Content-Type": "application/json"},
                json={"is_paused": True},
            )
            response.raise_for_status()

        data = AirflowPauseDagData(dag_id=dag_id, is_paused=True)
        logger.info("DAG paused dag_id=%s", dag_id)
        return AirflowPauseDagResponse(success=True, data=data)
    except httpx.HTTPStatusError as e:
        logger.exception("Airflow API returned an error")
        return AirflowPauseDagResponse(
            success=False,
            error=f"Airflow API error {e.response.status_code}: {e.response.text}",
        )
    except Exception as e:
        logger.exception("Failed to pause Airflow DAG")
        return AirflowPauseDagResponse(
            success=False, error=f"Failed to pause DAG: {str(e)}"
        )


@tool()
async def airflow_unpause_dag(
    dag_id: str,
) -> AirflowPauseDagResponse:
    """Unpause an Airflow DAG to allow new runs to be scheduled.

    Sets ``is_paused=false`` on the DAG via ``PATCH /api/v1/dags/{dag_id}``.

    Args:
        dag_id: The DAG identifier to unpause.

    Returns:
        Confirmation of pause state.
    """
    try:
        err = _check_configured()
        if err:
            return AirflowPauseDagResponse(success=False, error=err)

        base_url, auth = _get_airflow_config()

        logger.info("Unpausing Airflow DAG dag_id=%s", dag_id)
        async with httpx.AsyncClient(timeout=30, auth=auth) as client:
            response = await client.patch(
                f"{base_url}/api/v1/dags/{dag_id}",
                headers={"Content-Type": "application/json"},
                json={"is_paused": False},
            )
            response.raise_for_status()

        data = AirflowPauseDagData(dag_id=dag_id, is_paused=False)
        logger.info("DAG unpaused dag_id=%s", dag_id)
        return AirflowPauseDagResponse(success=True, data=data)
    except httpx.HTTPStatusError as e:
        logger.exception("Airflow API returned an error")
        return AirflowPauseDagResponse(
            success=False,
            error=f"Airflow API error {e.response.status_code}: {e.response.text}",
        )
    except Exception as e:
        logger.exception("Failed to unpause Airflow DAG")
        return AirflowPauseDagResponse(
            success=False, error=f"Failed to unpause DAG: {str(e)}"
        )
