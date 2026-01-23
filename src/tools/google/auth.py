import json
import logging
import os
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger("humcp.google.auth")

def get_google_service_from_mcp(service_name: str, version: str):
    """Build Google API service using the MCP session's access token.

    This function gets the access token from the authenticated MCP session
    instead of using a separate OAuth flow. The user authenticates once
    when connecting to the MCP server, and that token is reused for all
    Google API calls.

    Args:
        service_name: Google API service name (e.g., 'calendar', 'gmail')
        version: API version (e.g., 'v3', 'v1')

    Returns:
        Authenticated Google API service client

    Raises:
        ValueError: If unable to get access token from MCP session
    """
    try:
        from fastmcp.server.dependencies import get_access_token

        # Get the access token from the MCP session
        access_token = get_access_token()

        if not access_token or not access_token.token:
            raise ValueError("No access token available in MCP session")

        # Create credentials from the access token
        creds = Credentials(token=access_token.token)

        # Build and return the Google API service
        return build(service_name, version, credentials=creds)

    except ImportError:
        raise ValueError(
            "FastMCP dependencies not available. This function must be called "
            "from within an MCP tool context."
        )
    except Exception as e:
        logger.error("Failed to build Google service from MCP token: %s", e)
        raise ValueError(
            f"Failed to authenticate with Google using MCP session: {e}"
        )

