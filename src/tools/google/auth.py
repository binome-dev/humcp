import contextvars
import logging

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger("humcp.google.auth")

# Context variable to store access token from REST API calls
# This allows tools to access the token when called via REST (not MCP)
rest_access_token: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "rest_access_token", default=None
)


def set_rest_access_token(token: str) -> None:
    """Set the access token for REST API calls.

    Called by require_rest_auth when authenticating via cookie/header.
    """
    rest_access_token.set(token)


def get_google_service_from_mcp(service_name: str, version: str):
    """Build Google API service using the authenticated user's access token.

    This function tries to get the access token from multiple sources:
    1. REST context variable (set by require_rest_auth for cookie/header auth)
    2. MCP session context (via FastMCP's get_access_token)

    Args:
        service_name: Google API service name (e.g., 'calendar', 'gmail')
        version: API version (e.g., 'v3', 'v1')

    Returns:
        Authenticated Google API service client

    Raises:
        ValueError: If unable to get access token from any source
    """
    token_value = None

    # Check REST context variable (from cookie/header auth)
    rest_token = rest_access_token.get()
    if rest_token:
        logger.debug("Using access token from REST context")
        token_value = rest_token

    # Try FastMCP's get_access_token (for MCP session context)
    if not token_value:
        try:
            from fastmcp.server.dependencies import get_access_token

            access_token = get_access_token()
            if access_token and access_token.token:
                logger.debug("Using access token from MCP session")
                token_value = access_token.token
        except Exception as e:
            logger.debug("Could not get token from MCP session: %s", e)

    if not token_value:
        raise ValueError(
            "No access token available. Please authenticate via /login (REST) or MCP client."
        )

    # Create credentials from the access token
    creds = Credentials(token=token_value)

    # Build and return the Google API service
    return build(service_name, version, credentials=creds)
