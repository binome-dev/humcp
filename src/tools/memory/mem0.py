"""Mem0 persistent memory tools for storing and retrieving user memories."""

from __future__ import annotations

import logging
from typing import Any

from src.humcp.credentials import resolve_credential
from src.humcp.decorator import tool
from src.tools.memory.schemas import (
    Mem0AddMemoryData,
    Mem0AddMemoryResponse,
    Mem0GetMemoriesData,
    Mem0GetMemoriesResponse,
    Mem0Memory,
    Mem0SearchMemoryData,
    Mem0SearchMemoryResponse,
)

try:
    from mem0 import MemoryClient
except ImportError as err:
    raise ImportError(
        "mem0ai is required for Mem0 tools. Install with: pip install mem0ai"
    ) from err

logger = logging.getLogger("humcp.tools.mem0")


def _get_client(api_key: str) -> MemoryClient:
    """Create a Mem0 MemoryClient using the provided API key.

    Args:
        api_key: The Mem0 API key.

    Returns:
        A configured MemoryClient instance.
    """
    return MemoryClient(api_key=api_key)


def _parse_memory(raw: dict[str, Any]) -> Mem0Memory:
    """Parse a raw memory dict from Mem0 into a Mem0Memory model."""
    return Mem0Memory(
        id=raw.get("id"),
        memory=raw.get("memory", ""),
        metadata=raw.get("metadata"),
        created_at=raw.get("created_at"),
        updated_at=raw.get("updated_at"),
    )


@tool()
async def mem0_add_memory(
    content: str,
    user_id: str,
    metadata: dict[str, Any] | None = None,
) -> Mem0AddMemoryResponse:
    """Store a memory for a user in Mem0's managed memory platform.

    Sends a message to the Mem0 MemoryClient.add() API, which asynchronously
    extracts and stores relevant facts from the content. The memory is associated
    with the given user_id and can be retrieved or searched later. Mem0 automatically
    deduplicates, merges, and manages memory lifecycle.

    Args:
        content: The text content to store as a memory. Mem0 will extract key facts
                 and relationships from this text. Must not be empty.
        user_id: The user ID to associate the memory with. All memories for a user
                 are scoped by this identifier. Must not be empty.
        metadata: Optional key-value metadata to attach to the memory for filtering
                  and categorization (e.g., {"source": "chat", "topic": "preferences"}).

    Returns:
        Confirmation of the stored memory with Mem0 operation results including
        any extracted or updated memory entries.
    """
    try:
        if not content.strip():
            return Mem0AddMemoryResponse(
                success=False, error="content must not be empty"
            )
        if not user_id.strip():
            return Mem0AddMemoryResponse(
                success=False, error="user_id must not be empty"
            )

        api_key = await resolve_credential("MEM0_API_KEY")
        if not api_key:
            return Mem0AddMemoryResponse(
                success=False, error="MEM0_API_KEY not configured."
            )

        logger.info(
            "Mem0 add memory user_id=%s content_length=%d",
            user_id,
            len(content),
        )

        client = _get_client(api_key)
        messages = [{"role": "user", "content": content}]

        kwargs: dict[str, Any] = {"user_id": user_id}
        if metadata:
            kwargs["metadata"] = metadata

        result = client.add(messages, **kwargs)

        results_list: list[dict[str, Any]] = []
        if isinstance(result, dict) and "results" in result:
            results_list = result.get("results", [])
        elif isinstance(result, list):
            results_list = result

        logger.info("Mem0 add memory complete results=%d", len(results_list))

        return Mem0AddMemoryResponse(
            success=True,
            data=Mem0AddMemoryData(
                message=f"Memory stored for user {user_id}",
                results=results_list,
            ),
        )
    except ValueError as e:
        return Mem0AddMemoryResponse(success=False, error=str(e))
    except Exception as e:
        logger.exception("Mem0 add memory failed")
        return Mem0AddMemoryResponse(
            success=False, error=f"Mem0 add memory failed: {str(e)}"
        )


@tool()
async def mem0_search_memory(
    query: str,
    user_id: str,
    limit: int = 10,
) -> Mem0SearchMemoryResponse:
    """Search stored memories for a user using Mem0's semantic search.

    Uses the Mem0 MemoryClient.search() API to perform vector-based semantic
    search across all memories associated with the given user. Results are ranked
    by relevance to the query. This is useful for retrieving contextually relevant
    memories to augment AI agent responses.

    Args:
        query: The natural language search query to find relevant memories.
               Mem0 uses embedding-based similarity matching. Must not be empty.
        user_id: The user ID whose memories to search. Only memories stored under
                 this user_id are included in the search. Must not be empty.
        limit: Maximum number of results to return. Defaults to 10. Must be at
               least 1.

    Returns:
        A list of matching memories ranked by semantic relevance, each containing
        the memory text, metadata, and timestamps.
    """
    try:
        if not query.strip():
            return Mem0SearchMemoryResponse(
                success=False, error="query must not be empty"
            )
        if not user_id.strip():
            return Mem0SearchMemoryResponse(
                success=False, error="user_id must not be empty"
            )
        if limit < 1:
            return Mem0SearchMemoryResponse(
                success=False, error="limit must be at least 1"
            )

        api_key = await resolve_credential("MEM0_API_KEY")
        if not api_key:
            return Mem0SearchMemoryResponse(
                success=False, error="MEM0_API_KEY not configured."
            )

        logger.info(
            "Mem0 search memory user_id=%s query_length=%d limit=%d",
            user_id,
            len(query),
            limit,
        )

        client = _get_client(api_key)
        results = client.search(query=query, user_id=user_id, limit=limit)

        # Normalize results from Mem0 response
        raw_results: list[dict[str, Any]]
        if isinstance(results, dict) and "results" in results:
            raw_results = results.get("results", [])
        elif isinstance(results, list):
            raw_results = results
        else:
            raw_results = []

        memories = [_parse_memory(r) for r in raw_results]

        logger.info("Mem0 search memory complete results=%d", len(memories))

        return Mem0SearchMemoryResponse(
            success=True,
            data=Mem0SearchMemoryData(query=query, results=memories),
        )
    except ValueError as e:
        return Mem0SearchMemoryResponse(success=False, error=str(e))
    except Exception as e:
        logger.exception("Mem0 search memory failed")
        return Mem0SearchMemoryResponse(
            success=False, error=f"Mem0 search memory failed: {str(e)}"
        )


@tool()
async def mem0_get_memories(
    user_id: str,
) -> Mem0GetMemoriesResponse:
    """Retrieve all stored memories for a user from Mem0.

    Uses the Mem0 MemoryClient.get_all() API to fetch every memory associated
    with the given user_id. Unlike search(), this returns all memories without
    any relevance filtering. Useful for building a complete user profile or
    performing bulk memory management operations.

    Args:
        user_id: The user ID whose memories to retrieve. Must not be empty.

    Returns:
        A complete list of all memories stored for the given user, each
        containing the memory text, metadata, and timestamps.
    """
    try:
        if not user_id.strip():
            return Mem0GetMemoriesResponse(
                success=False, error="user_id must not be empty"
            )

        api_key = await resolve_credential("MEM0_API_KEY")
        if not api_key:
            return Mem0GetMemoriesResponse(
                success=False, error="MEM0_API_KEY not configured."
            )

        logger.info("Mem0 get memories user_id=%s", user_id)

        client = _get_client(api_key)
        results = client.get_all(user_id=user_id)

        # Normalize results from Mem0 response
        raw_results: list[dict[str, Any]]
        if isinstance(results, dict) and "results" in results:
            raw_results = results.get("results", [])
        elif isinstance(results, list):
            raw_results = results
        else:
            raw_results = []

        memories = [_parse_memory(r) for r in raw_results]

        logger.info("Mem0 get memories complete memories=%d", len(memories))

        return Mem0GetMemoriesResponse(
            success=True,
            data=Mem0GetMemoriesData(user_id=user_id, memories=memories),
        )
    except ValueError as e:
        return Mem0GetMemoriesResponse(success=False, error=str(e))
    except Exception as e:
        logger.exception("Mem0 get memories failed")
        return Mem0GetMemoriesResponse(
            success=False, error=f"Mem0 get memories failed: {str(e)}"
        )
