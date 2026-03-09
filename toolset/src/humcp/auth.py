"""Unified user identity resolution for MCP and REST paths."""

import logging
from contextvars import ContextVar
from uuid import UUID

logger = logging.getLogger(__name__)

# ContextVar set by APIKeyMiddleware for REST requests
_current_user_id: ContextVar[str | None] = ContextVar("current_user_id", default=None)


def get_current_user_id() -> UUID | None:
    """Return the authenticated user's UUID, or None if unauthenticated.

    Resolution order:
      1. FastMCP access token (MCP path — set by JWTVerifier middleware)
      2. ContextVar (REST path — set by APIKeyMiddleware)
    """
    # 1. MCP path: FastMCP's get_access_token()
    try:
        from fastmcp.server.dependencies import get_access_token

        token = get_access_token()
        if token is not None:
            sub = token.client_id or token.claims.get("sub")
            if sub:
                return UUID(sub)
    except (RuntimeError, ValueError, ImportError):
        pass

    # 2. REST path: ContextVar set by middleware
    user_id_str = _current_user_id.get()
    if user_id_str:
        try:
            return UUID(user_id_str)
        except ValueError:
            logger.warning("Invalid user_id in ContextVar: %s", user_id_str)

    return None
