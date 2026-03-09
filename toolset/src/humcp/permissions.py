"""Lightweight permission checker querying iam.relationships directly."""

import logging
import os
from uuid import UUID

from fastapi import HTTPException, status
from shared.auth import satisfying_relations
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from src.humcp.auth import get_current_user_id

logger = logging.getLogger(__name__)

TOOLSET_REQUIRE_AUTH = os.getenv("TOOLSET_REQUIRE_AUTH", "").lower() == "true"

_engine: AsyncEngine | None = None


def _get_engine() -> AsyncEngine:
    global _engine
    if _engine is not None:
        return _engine

    db_url = os.getenv("DATABASE_URL", "")
    if not db_url:
        raise RuntimeError("DATABASE_URL is required for permission checks")

    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    _engine = create_async_engine(db_url, pool_size=3, max_overflow=2)
    return _engine


async def has_permission(
    actor_id: UUID,
    object_type: str,
    object_id: str,
    relation: str,
) -> bool:
    """Check if actor has the required relation on the object.

    Checks direct actor tuples and org-based tuples (actor is org member,
    org has relation on object).
    """
    satisfying = satisfying_relations(relation)

    try:
        engine = _get_engine()
    except RuntimeError:
        logger.warning("DATABASE_URL not set, skipping permission check")
        return True

    try:
        async with engine.connect() as conn:
            # 0. Check if this resource has ANY tuples at all.
            #    If not, the resource hasn't been onboarded to IAM — grant
            #    read-only (viewer) access but deny writes.
            exists = await conn.execute(
                text(
                    "SELECT 1 FROM iam.relationships "
                    "WHERE object_type = :obj_type AND object_id = :obj_id "
                    "LIMIT 1"
                ),
                {"obj_type": object_type, "obj_id": object_id},
            )
            if not exists.first():
                allowed = relation == "viewer"
                logger.debug(
                    "No IAM tuples for %s/%s, relation=%s → %s",
                    object_type,
                    object_id,
                    relation,
                    "allow" if allowed else "deny",
                )
                return allowed

            # 1. Direct actor -> object check
            result = await conn.execute(
                text(
                    "SELECT 1 FROM iam.relationships "
                    "WHERE object_type = :obj_type AND object_id = :obj_id "
                    "AND relation = ANY(:relations) "
                    "AND subject_type = 'actor' AND subject_id = :actor_id "
                    "LIMIT 1"
                ),
                {
                    "obj_type": object_type,
                    "obj_id": object_id,
                    "relations": list(satisfying),
                    "actor_id": str(actor_id),
                },
            )
            if result.first():
                return True

            # 2. Org-based: actor is member of org
            org_result = await conn.execute(
                text(
                    "SELECT object_id FROM iam.relationships "
                    "WHERE object_type = 'organization' AND relation = 'member' "
                    "AND subject_type = 'actor' AND subject_id = :actor_id"
                ),
                {"actor_id": str(actor_id)},
            )
            org_rows = org_result.fetchall()
            if not org_rows:
                return False

            org_ids = [r[0] for r in org_rows]

            # Check org has relation on object (direct or via #member subject set)
            org_match = await conn.execute(
                text(
                    "SELECT 1 FROM iam.relationships "
                    "WHERE object_type = :obj_type AND object_id = :obj_id "
                    "AND relation = ANY(:relations) "
                    "AND subject_type = 'organization' AND subject_id = ANY(:org_ids) "
                    "LIMIT 1"
                ),
                {
                    "obj_type": object_type,
                    "obj_id": object_id,
                    "relations": list(satisfying),
                    "org_ids": org_ids,
                },
            )
            if org_match.first():
                return True
    except ProgrammingError:
        # iam.relationships table doesn't exist yet (DB not initialized)
        logger.warning("iam.relationships table not found, skipping permission check")
        return True

    return False


async def check_permission(
    object_type: str,
    object_id: str,
    relation: str = "viewer",
) -> UUID | None:
    """Get current user and check permission on a resource.

    Returns:
        user_id if authenticated and authorized, None if no auth context (dev mode).

    Raises:
        HTTPException 401: if TOOLSET_REQUIRE_AUTH is true and no user context.
        HTTPException 403: if authenticated but lacks the required permission.
    """
    user_id = get_current_user_id()
    if user_id is None:
        if TOOLSET_REQUIRE_AUTH:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )
        return None

    if not await has_permission(user_id, object_type, object_id, relation):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You do not have {relation} access on this {object_type}",
        )
    return user_id


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
