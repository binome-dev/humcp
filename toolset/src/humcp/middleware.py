"""API Key authentication middleware for service-to-service calls."""

import logging
import os
import secrets

from fastapi import HTTPException, Request
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware

from src.humcp.auth import _current_user_id

logger = logging.getLogger(__name__)

SERVICE_API_KEY = os.getenv("SERVICE_API_KEY", "")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
JWT_ALGORITHM = "HS256"

# Log warning if no API key is configured
if not SERVICE_API_KEY:
    logger.warning(
        "SERVICE_API_KEY not configured. API key authentication is disabled. "
        "Set SERVICE_API_KEY environment variable for production."
    )


class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    Middleware to validate X-API-Key header for service-to-service calls.

    Also extracts user identity from Authorization Bearer JWT when present
    and stores it in a ContextVar for downstream tool handlers.

    Public paths (/, /docs, etc.) are exempt from authentication.
    Uses constant-time comparison to prevent timing attacks.
    """

    # Paths that don't require authentication
    PUBLIC_PATHS = {"/", "/docs", "/openapi.json", "/redoc", "/playground"}

    async def dispatch(self, request: Request, call_next):
        # Skip auth for public paths
        if request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)

        # Skip auth if no API key is configured (development mode)
        if not SERVICE_API_KEY:
            self._extract_user_id(request)
            return await call_next(request)

        # Validate API key using constant-time comparison
        api_key = request.headers.get("X-API-Key")
        if not api_key or not secrets.compare_digest(api_key, SERVICE_API_KEY):
            logger.warning("Invalid API key attempt for path: %s", request.url.path)
            raise HTTPException(
                status_code=401,
                detail="Invalid or missing API key",
            )

        # Extract user identity from Bearer JWT (if present)
        self._extract_user_id(request)

        return await call_next(request)

    @staticmethod
    def _extract_user_id(request: Request) -> None:
        """Decode Bearer JWT and store user_id in ContextVar for REST tool handlers."""
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer ") or not JWT_SECRET_KEY:
            _current_user_id.set(None)
            return

        token = auth_header[7:]
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            sub = payload.get("sub")
            if sub:
                _current_user_id.set(sub)
            else:
                _current_user_id.set(None)
        except JWTError:
            logger.debug("Failed to decode Bearer JWT in REST request")
            _current_user_id.set(None)
