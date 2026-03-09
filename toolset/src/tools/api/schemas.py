"""Pydantic output schemas for API tools."""

from typing import Any

from pydantic import BaseModel, Field

from src.humcp.schemas import ToolResponse

# =============================================================================
# HTTP Client Schemas
# =============================================================================


class HttpResponseData(BaseModel):
    """Output data for http_request tool."""

    status_code: int = Field(..., description="HTTP status code of the response")
    headers: dict[str, str] = Field(
        default_factory=dict, description="Response headers"
    )
    body: Any = Field(None, description="Response body (JSON-parsed if possible)")
    url: str = Field(..., description="The final URL that was requested")
    method: str = Field(..., description="HTTP method used")
    elapsed_ms: float | None = Field(
        None, description="Request duration in milliseconds"
    )


# =============================================================================
# Response Wrappers (inheriting from ToolResponse[T])
# =============================================================================


class HttpResponseResponse(ToolResponse[HttpResponseData]):
    """Response schema for http_request tool."""

    pass
