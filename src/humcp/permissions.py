"""Simplified permission checker for standalone HuMCP deployment.

This module provides auth/permission primitives without requiring the
shared.auth IAM library (graphite-workflow-builder internal). It can be
upgraded to full IAM checks when shared.auth is available.
"""

import logging
import os
from uuid import UUID

from fastapi import HTTPException, status

from src.humcp.auth import get_current_user_id

logger = logging.getLogger(__name__)

TOOLSET_REQUIRE_AUTH = os.getenv("TOOLSET_REQUIRE_AUTH", "").lower() == "true"


async def require_auth() -> UUID | None:
    """Require authentication without checking a specific resource permission.

    Returns:
        user_id if authenticated, None if no auth context (dev mode).

    Raises:
        HTTPException 401: if TOOLSET_REQUIRE_AUTH is true and no user context.
    """
    user_id = get_current_user_id()
    if user_id is None and TOOLSET_REQUIRE_AUTH:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return user_id


STRICT_PERMISSIONS = os.getenv("STRICT_PERMISSIONS", "").lower() == "true"


async def check_permission(
    object_type: str,
    object_id: str,
    relation: str = "viewer",
) -> UUID | None:
    """Get current user and check permission on a resource.

    Simplified version: delegates to require_auth() only.
    Upgrade to full IAM checks when shared.auth is available.

    When STRICT_PERMISSIONS=true, rejects all calls since no IAM backend
    is configured to actually verify fine-grained permissions.

    Returns:
        user_id if authenticated, None if no auth context (dev mode).

    Raises:
        HTTPException 401: if TOOLSET_REQUIRE_AUTH is true and no user context.
        HTTPException 403: if STRICT_PERMISSIONS is true (no IAM backend).
    """
    if STRICT_PERMISSIONS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Fine-grained permissions not configured. Set up IAM backend or disable STRICT_PERMISSIONS.",
        )
    logger.warning(
        "Permission check stub: object_type=%s object_id=%s relation=%s (not enforced)",
        object_type,
        object_id,
        relation,
    )
    return await require_auth()
