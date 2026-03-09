"""Web scraping tool using Apify cloud actors."""

from __future__ import annotations

import logging
from typing import Any

from src.humcp.credentials import resolve_credential
from src.humcp.decorator import tool
from src.tools.web_scraping.schemas import ActorRunData, ActorRunResponse

logger = logging.getLogger("humcp.tools.apify")


@tool()
async def apify_run_actor(
    actor_id: str,
    input_data: dict[str, Any] | None = None,
) -> ActorRunResponse:
    """Run an Apify actor and return its results.

    Apify actors are pre-built scrapers and automation tools that run in the cloud.
    Pass an actor ID (e.g., 'apify/web-scraper') and optional input data.
    Requires APIFY_API_TOKEN.

    Args:
        actor_id: The Apify actor ID to run (e.g., 'apify/web-scraper').
        input_data: Input parameters for the actor as a dictionary.

    Returns:
        Results from the actor run.
    """
    try:
        try:
            from apify_client import ApifyClient
        except ImportError as err:
            raise ImportError(
                "apify-client is required for Apify tools. "
                "Install with: pip install apify-client"
            ) from err

        api_token = await resolve_credential("APIFY_API_TOKEN")
        if not api_token:
            return ActorRunResponse(
                success=False,
                error="Apify API not configured. Set APIFY_API_TOKEN.",
            )

        if not actor_id:
            return ActorRunResponse(success=False, error="Actor ID is required")

        logger.info("Apify run actor start actor_id=%s", actor_id)

        client = ApifyClient(api_token)
        run_input = input_data if input_data else {}

        details = client.actor(actor_id=actor_id).call(run_input=run_input)

        if not details:
            return ActorRunResponse(
                success=False,
                error=f"Actor {actor_id} did not return run details",
            )

        run_id = details.get("id")
        if not run_id:
            return ActorRunResponse(
                success=False,
                error=f"No run ID returned for actor {actor_id}",
            )

        run = client.run(run_id=run_id)
        results = run.dataset().list_items(clean=True).items

        data = ActorRunData(
            actor_id=actor_id,
            results=results,
            total_items=len(results),
        )

        logger.info(
            "Apify run actor complete actor_id=%s items=%d", actor_id, len(results)
        )
        return ActorRunResponse(success=True, data=data)

    except ImportError:
        raise
    except Exception as e:
        logger.exception("Apify run actor failed")
        return ActorRunResponse(
            success=False, error=f"Apify run actor failed: {str(e)}"
        )
