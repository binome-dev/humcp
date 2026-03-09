"""Zep conversation memory tools for session-based memory management."""

from __future__ import annotations

import logging
import os

from src.humcp.decorator import tool
from src.tools.memory.schemas import (
    ZepAddMemoryResponse,
    ZepGetSessionResponse,
    ZepMemoryResult,
    ZepMessageData,
    ZepSearchMemoryData,
    ZepSearchMemoryResponse,
    ZepSessionData,
)

try:
    from zep_cloud import Message as ZepMessage
    from zep_cloud.client import AsyncZep
except ImportError as err:
    raise ImportError(
        "zep-cloud is required for Zep tools. Install with: pip install zep-cloud"
    ) from err

logger = logging.getLogger("humcp.tools.zep")


def _get_client() -> AsyncZep:
    """Create an async Zep client using the configured API key."""
    api_key = os.getenv("ZEP_API_KEY")
    if not api_key:
        raise ValueError("ZEP_API_KEY environment variable is not set")
    return AsyncZep(api_key=api_key)


@tool()
async def zep_add_memory(
    session_id: str,
    content: str,
    role: str = "user",
) -> ZepAddMemoryResponse:
    """Add a message to a Zep Cloud session (thread) memory.

    Sends a message to the Zep Cloud AsyncZep thread.add_messages() API. Zep
    automatically builds a knowledge graph from conversation messages, extracting
    entities, relationships, and facts that can be searched later via graph search.
    Messages are persisted in the thread's chronological history.

    Args:
        session_id: The Zep thread ID to add the message to. This is Zep's
                    session/conversation identifier. Must not be empty.
        content: The text content of the message. Zep will extract facts and
                 entities from this content for its knowledge graph. Must not
                 be empty.
        role: The role of the message sender. Common values: 'user', 'assistant',
              'system'. Defaults to 'user'. Maps to Zep's Message role_type.

    Returns:
        Confirmation of the stored message with the session ID.
    """
    try:
        if not session_id.strip():
            return ZepAddMemoryResponse(
                success=False, error="session_id must not be empty"
            )
        if not content.strip():
            return ZepAddMemoryResponse(
                success=False, error="content must not be empty"
            )

        logger.info(
            "Zep add memory session_id=%s role=%s content_length=%d",
            session_id,
            role,
            len(content),
        )

        client = _get_client()
        zep_message = ZepMessage(
            role=role,
            content=content,
            role_type=role,
        )

        await client.thread.add_messages(
            thread_id=session_id,
            messages=[zep_message],
        )

        logger.info("Zep add memory complete session_id=%s", session_id)

        return ZepAddMemoryResponse(
            success=True,
            data=ZepMessageData(
                session_id=session_id,
                message=f"Message from '{role}' added to session {session_id}",
            ),
        )
    except ValueError as e:
        return ZepAddMemoryResponse(success=False, error=str(e))
    except Exception as e:
        logger.exception("Zep add memory failed")
        return ZepAddMemoryResponse(
            success=False, error=f"Zep add memory failed: {str(e)}"
        )


@tool()
async def zep_search_memory(
    session_id: str,
    query: str,
    limit: int = 5,
) -> ZepSearchMemoryResponse:
    """Search Zep Cloud session memory for relevant facts using graph search.

    Uses the Zep Cloud AsyncZep graph.search() API to perform semantic search
    across the knowledge graph built from conversation messages. Searches the
    'edges' scope by default, which returns fact-level results extracted from
    the conversation. The search query is limited to 400 characters by Zep's API.

    First retrieves the thread to resolve the associated user_id, then performs
    graph search scoped to that user's knowledge graph.

    Args:
        session_id: The Zep thread ID to search within. Used to resolve the
                    associated user_id for graph search. Must not be empty.
        query: The natural language search query to find relevant facts and
               memories. Zep uses MMR reranking for diverse, relevant results.
               Must not be empty.
        limit: Maximum number of results to return. Defaults to 5. Must be at
               least 1.

    Returns:
        A list of matching facts from the session's knowledge graph, each with
        a relevance score.
    """
    try:
        if not session_id.strip():
            return ZepSearchMemoryResponse(
                success=False, error="session_id must not be empty"
            )
        if not query.strip():
            return ZepSearchMemoryResponse(
                success=False, error="query must not be empty"
            )
        if limit < 1:
            return ZepSearchMemoryResponse(
                success=False, error="limit must be at least 1"
            )

        logger.info(
            "Zep search memory session_id=%s query_length=%d limit=%d",
            session_id,
            len(query),
            limit,
        )

        client = _get_client()

        # Zep graph search uses user_id, but we search via session context
        # First get the session to find the user_id
        session_info = await client.thread.get(thread_id=session_id)
        user_id = getattr(session_info, "user_id", None)

        if not user_id:
            return ZepSearchMemoryResponse(
                success=False,
                error=f"No user associated with session {session_id}",
            )

        search_response = await client.graph.search(
            query=query,
            user_id=user_id,
            scope="edges",
            limit=limit,
        )

        results: list[ZepMemoryResult] = []
        if search_response.edges:
            for edge in search_response.edges:
                results.append(
                    ZepMemoryResult(
                        fact=edge.fact,
                        score=getattr(edge, "score", None),
                    )
                )

        logger.info("Zep search memory complete results=%d", len(results))

        return ZepSearchMemoryResponse(
            success=True,
            data=ZepSearchMemoryData(
                session_id=session_id,
                query=query,
                scope="edges",
                results=results,
            ),
        )
    except ValueError as e:
        return ZepSearchMemoryResponse(success=False, error=str(e))
    except Exception as e:
        logger.exception("Zep search memory failed")
        return ZepSearchMemoryResponse(
            success=False, error=f"Zep search memory failed: {str(e)}"
        )


@tool()
async def zep_get_session(
    session_id: str,
) -> ZepGetSessionResponse:
    """Retrieve session context and metadata from Zep Cloud.

    Uses the Zep Cloud AsyncZep thread.get_user_context() API to fetch the
    session's context summary, which is generated by performing graph search
    on nodes, edges, and episodes using the MMR reranker against the most
    recent messages. Also retrieves the thread metadata to count messages.

    The context summary is useful for providing an AI agent with relevant
    background about the user's conversation history and preferences.

    Args:
        session_id: The Zep thread ID to retrieve. Must not be empty.

    Returns:
        Session context summary (auto-generated by Zep from the knowledge
        graph) and total message count for the thread.
    """
    try:
        if not session_id.strip():
            return ZepGetSessionResponse(
                success=False, error="session_id must not be empty"
            )

        logger.info("Zep get session session_id=%s", session_id)

        client = _get_client()

        # Get session context
        context_response = await client.thread.get_user_context(
            thread_id=session_id, mode="basic"
        )
        context = getattr(context_response, "context", None)

        # Get session messages for count
        session_info = await client.thread.get(thread_id=session_id)
        messages = getattr(session_info, "messages", None)
        message_count = len(messages) if messages else 0

        logger.info(
            "Zep get session complete session_id=%s message_count=%d",
            session_id,
            message_count,
        )

        return ZepGetSessionResponse(
            success=True,
            data=ZepSessionData(
                session_id=session_id,
                context=context,
                message_count=message_count,
            ),
        )
    except ValueError as e:
        return ZepGetSessionResponse(success=False, error=str(e))
    except Exception as e:
        logger.exception("Zep get session failed")
        return ZepGetSessionResponse(
            success=False, error=f"Zep get session failed: {str(e)}"
        )
