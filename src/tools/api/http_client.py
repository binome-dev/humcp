"""HTTP client tool for making arbitrary HTTP requests."""

from __future__ import annotations

import ipaddress
import logging
import os
import socket
import time
from typing import Any
from urllib.parse import urlparse

from src.humcp.decorator import tool
from src.tools.api.schemas import (
    HttpResponseData,
    HttpResponseResponse,
)


def _is_private_url(url: str) -> bool:
    """Check if URL resolves to a private/internal IP range."""
    parsed = urlparse(url)
    hostname = parsed.hostname
    if not hostname:
        return True

    # Block known metadata endpoints and localhost
    blocked_hosts = {
        "localhost",
        "127.0.0.1",
        "::1",
        "0.0.0.0",
        "metadata.google.internal",
        "metadata.goog",
        "169.254.169.254",
    }
    if hostname in blocked_hosts:
        return True

    try:
        resolved = socket.getaddrinfo(hostname, None)
        for _, _, _, _, addr in resolved:
            ip = ipaddress.ip_address(addr[0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return True
    except (socket.gaierror, ValueError):
        pass

    return False


try:
    import httpx
except ImportError as err:
    raise ImportError(
        "httpx is required for HTTP client tools. Install with: pip install httpx"
    ) from err

logger = logging.getLogger("humcp.tools.http_client")


@tool()
async def http_request(
    method: str,
    url: str,
    headers: dict[str, str] | None = None,
    body: dict[str, Any] | None = None,
    timeout: int = 30,
) -> HttpResponseResponse:
    """Make an HTTP request to any URL and return the response.

    A general-purpose HTTP client supporting GET, POST, PUT, PATCH, DELETE,
    HEAD, and OPTIONS methods. The response body is automatically parsed as
    JSON when the Content-Type indicates JSON; otherwise it is returned as
    plain text. Includes automatic timing measurement for performance analysis.

    The request body (JSON) is only sent for POST, PUT, and PATCH methods;
    it is silently ignored for other methods. Custom headers can be provided
    for authentication (e.g., Bearer tokens, API keys) or content negotiation.

    Args:
        method: HTTP method to use. Supported values: GET, POST, PUT, PATCH,
                DELETE, HEAD, OPTIONS. Case-insensitive.
        url: The full URL to send the request to. Must start with 'http://' or
             'https://'. Query parameters should be included in the URL.
        headers: Optional dictionary of HTTP headers to include in the request.
                 Useful for Authorization, Content-Type overrides, or custom
                 API key headers (e.g., {"Authorization": "Bearer <token>"}).
        body: Optional dictionary to send as a JSON request body. Only used for
              POST, PUT, and PATCH methods. Set to None for GET/DELETE requests.
        timeout: Request timeout in seconds. The request will be aborted if no
                 response is received within this duration. Defaults to 30 seconds.
                 Increase for slow APIs or large payloads; decrease for
                 latency-sensitive operations. Range: 1-300 recommended.

    Returns:
        Response containing the HTTP status code, response headers, parsed body
        (JSON object or plain text), final URL (after redirects), HTTP method,
        and elapsed time in milliseconds.
    """
    try:
        normalized_method = method.upper()
        allowed_methods = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
        if normalized_method not in allowed_methods:
            return HttpResponseResponse(
                success=False,
                error=f"Unsupported HTTP method: {method}. Use one of: {', '.join(sorted(allowed_methods))}",
            )

        if not url.startswith(("http://", "https://")):
            return HttpResponseResponse(
                success=False,
                error="URL must start with http:// or https://",
            )

        if os.getenv("HTTP_ALLOW_PRIVATE", "").lower() != "true" and _is_private_url(
            url
        ):
            return HttpResponseResponse(
                success=False,
                error="Requests to private/internal network addresses are blocked. Set HTTP_ALLOW_PRIVATE=true to allow.",
            )

        logger.info("HTTP %s %s", normalized_method, url)
        start_time = time.monotonic()

        request_kwargs: dict[str, Any] = {
            "method": normalized_method,
            "url": url,
            "timeout": timeout,
        }
        if headers is not None:
            request_kwargs["headers"] = headers
        if body is not None and normalized_method in {"POST", "PUT", "PATCH"}:
            request_kwargs["json"] = body

        async with httpx.AsyncClient() as client:
            response = await client.request(**request_kwargs)

        elapsed_ms = (time.monotonic() - start_time) * 1000

        response_headers = dict(response.headers)

        response_body: Any
        try:
            response_body = response.json()
        except Exception:
            response_body = response.text

        data = HttpResponseData(
            status_code=response.status_code,
            headers=response_headers,
            body=response_body,
            url=str(response.url),
            method=normalized_method,
            elapsed_ms=round(elapsed_ms, 2),
        )

        logger.info(
            "HTTP %s %s status=%d elapsed=%.1fms",
            normalized_method,
            url,
            response.status_code,
            elapsed_ms,
        )
        return HttpResponseResponse(success=True, data=data)
    except httpx.TimeoutException:
        logger.exception("HTTP request timed out")
        return HttpResponseResponse(
            success=False,
            error=f"Request timed out after {timeout} seconds",
        )
    except httpx.ConnectError as e:
        logger.exception("HTTP connection failed")
        return HttpResponseResponse(
            success=False,
            error=f"Connection failed: {str(e)}",
        )
    except Exception as e:
        logger.exception("HTTP request failed")
        return HttpResponseResponse(
            success=False, error=f"HTTP request failed: {str(e)}"
        )
