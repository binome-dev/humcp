import base64
import binascii
import logging
import os
import hmac
import time
from urllib.parse import unquote

from dotenv import load_dotenv
from fastmcp.server.auth.providers.google import GoogleProvider

from mcp.server.auth.middleware.client_auth import ClientAuthenticator
from mcp.server.auth.handlers.token import TokenHandler
from mcp.server.auth.middleware.client_auth import AuthenticationError

load_dotenv()

logger = logging.getLogger("humcp.auth")

# Enable debug logging for OAuth to diagnose authentication issues
logging.getLogger("fastmcp.server.auth").setLevel(logging.DEBUG)
logging.getLogger("mcp.server.auth").setLevel(logging.DEBUG)
logging.getLogger("mcp.server.auth.middleware.client_auth").setLevel(logging.DEBUG)
logging.getLogger("mcp.server.auth.handlers.token").setLevel(logging.DEBUG)


def apply_authentication_patches():
    """Apply monkey patches to support Postman's Basic Auth behavior.

    Postman sends client_id in Authorization header but not in form data.
    These patches extract the client_id from the Basic Auth header when needed.
    """
    _original_authenticate = ClientAuthenticator.authenticate_request

    async def patched_authenticate_request(self, request):
        """Patched authenticate_request that extracts client_id from Basic Auth header if missing."""
        form_data = await request.form()
        client_id = form_data.get("client_id")

        # If client_id is missing from form data, try to extract from Authorization header
        if not client_id:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Basic "):
                try:
                    encoded_credentials = auth_header[6:]
                    decoded = base64.b64decode(encoded_credentials).decode("utf-8")
                    if ":" in decoded:
                        basic_client_id, _ = decoded.split(":", 1)
                        client_id = unquote(basic_client_id)
                        logger.info("Extracted client_id from Basic Auth header: %s", client_id)
                except (ValueError, UnicodeDecodeError, binascii.Error) as e:
                    logger.warning("Failed to extract client_id from Basic Auth header: %s", e)

        if not client_id:
            raise AuthenticationError("Missing client_id")

        client = await self.provider.get_client(str(client_id))
        if not client:
            raise AuthenticationError("Invalid client_id")

        request_client_secret: str | None = None
        auth_header = request.headers.get("Authorization", "")

        if client.token_endpoint_auth_method == "client_secret_basic":
            if not auth_header.startswith("Basic "):
                raise AuthenticationError("Missing or invalid Basic authentication in Authorization header")

            try:
                encoded_credentials = auth_header[6:]
                decoded = base64.b64decode(encoded_credentials).decode("utf-8")
                if ":" not in decoded:
                    raise ValueError("Invalid Basic auth format")
                basic_client_id, request_client_secret = decoded.split(":", 1)

                basic_client_id = unquote(basic_client_id)
                request_client_secret = unquote(request_client_secret)

                if basic_client_id != client_id:
                    raise AuthenticationError("Client ID mismatch in Basic auth")
            except (ValueError, UnicodeDecodeError, binascii.Error):
                raise AuthenticationError("Invalid Basic authentication header")

        elif client.token_endpoint_auth_method == "client_secret_post":
            raw_form_data = form_data.get("client_secret")
            if isinstance(raw_form_data, str):
                request_client_secret = str(raw_form_data)

        elif client.token_endpoint_auth_method == "none":
            request_client_secret = None
        else:
            raise AuthenticationError(
                f"Unsupported auth method: {client.token_endpoint_auth_method}"
            )

        # Validate client secret if required
        if client.client_secret:
            if not request_client_secret:
                raise AuthenticationError("Client secret is required")

            if not hmac.compare_digest(client.client_secret.encode(), request_client_secret.encode()):
                raise AuthenticationError("Invalid client_secret")

            if client.client_secret_expires_at and client.client_secret_expires_at < int(time.time()):
                raise AuthenticationError("Client secret has expired")

        return client

    ClientAuthenticator.authenticate_request = patched_authenticate_request

    # Also patch TokenHandler to add client_id to form data for Pydantic validation
    _original_token_handle = TokenHandler.handle

    async def patched_token_handle(self, request):
        """Patched token handler that adds client_id to form data if missing."""
        # Check if client_id is missing from form data but present in Basic Auth header
        form_data = await request.form()
        if not form_data.get("client_id"):
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Basic "):
                try:
                    encoded_credentials = auth_header[6:]
                    decoded = base64.b64decode(encoded_credentials).decode("utf-8")
                    if ":" in decoded:
                        basic_client_id, _ = decoded.split(":", 1)
                        client_id = unquote(basic_client_id)

                        # Add client_id to form data dict for Pydantic validation
                        from starlette.datastructures import FormData as StarletteFormData
                        mutable_form = dict(form_data)
                        mutable_form["client_id"] = client_id

                        # Create a new FormData object with the client_id added
                        request._form = StarletteFormData(mutable_form)

                        logger.debug("Added client_id to form data for Pydantic validation: %s", client_id)
                except (ValueError, UnicodeDecodeError, binascii.Error) as e:
                    logger.warning("Failed to extract client_id for form validation: %s", e)

        # Call original handle method
        return await _original_token_handle(self, request)

    TokenHandler.handle = patched_token_handle
    logger.info("Applied authentication patches for Postman compatibility")


def create_auth_provider() -> GoogleProvider:
    """Create and configure the Google OAuth authentication provider.

    Returns:
        Configured GoogleProvider instance.

    Raises:
        ValueError: If required environment variables are not set.
    """
    # Apply patches before creating provider
    apply_authentication_patches()

    client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise ValueError(
            "GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET must be set in environment"
        )

    auth_provider = GoogleProvider(
        client_id=client_id,
        client_secret=client_secret,
        base_url="http://localhost:8080",
        required_scopes=[
            # OpenID Connect
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            # Gmail
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/gmail.modify",
            # Calendar
            "https://www.googleapis.com/auth/calendar",
            # Drive
            "https://www.googleapis.com/auth/drive",
            # Tasks
            "https://www.googleapis.com/auth/tasks",
            # Docs
            "https://www.googleapis.com/auth/documents",
            # Sheets
            "https://www.googleapis.com/auth/spreadsheets",
            # Slides
            "https://www.googleapis.com/auth/presentations",
            # Forms
            "https://www.googleapis.com/auth/forms.body",
            "https://www.googleapis.com/auth/forms.responses.readonly",
            # Chat
            "https://www.googleapis.com/auth/chat.spaces.readonly",
            "https://www.googleapis.com/auth/chat.messages",
        ],
        allowed_client_redirect_uris=["https://oauth.pstmn.io/v1/callback", "http://localhost:*"],
    )

    logger.info("Created Google OAuth provider")
    return auth_provider
