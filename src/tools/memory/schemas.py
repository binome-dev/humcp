"""Pydantic output schemas for memory tools."""

from typing import Any

from pydantic import BaseModel, Field

from src.humcp.schemas import ToolResponse

# =============================================================================
# Mem0 Schemas
# =============================================================================


class Mem0Memory(BaseModel):
    """A single memory entry from Mem0."""

    id: str | None = Field(None, description="Memory ID")
    memory: str = Field(..., description="Memory content")
    metadata: dict[str, Any] | None = Field(None, description="Associated metadata")
    created_at: str | None = Field(None, description="Creation timestamp")
    updated_at: str | None = Field(None, description="Last update timestamp")


class Mem0AddMemoryData(BaseModel):
    """Output data for mem0_add_memory tool."""

    message: str = Field(..., description="Confirmation message")
    results: list[dict[str, Any]] = Field(
        default_factory=list, description="Memory operation results from Mem0"
    )


class Mem0SearchMemoryData(BaseModel):
    """Output data for mem0_search_memory tool."""

    query: str = Field(..., description="The search query that was executed")
    results: list[Mem0Memory] = Field(
        default_factory=list, description="List of matching memories"
    )


class Mem0GetMemoriesData(BaseModel):
    """Output data for mem0_get_memories tool."""

    user_id: str = Field(..., description="User ID for which memories were retrieved")
    memories: list[Mem0Memory] = Field(
        default_factory=list, description="List of all memories"
    )


# =============================================================================
# Zep Schemas
# =============================================================================


class ZepMessageData(BaseModel):
    """Output data for zep_add_memory tool."""

    session_id: str = Field(..., description="Zep session ID")
    message: str = Field(..., description="Confirmation message")


class ZepMemoryResult(BaseModel):
    """A single memory result from Zep search."""

    fact: str | None = Field(default=None, description="Fact text from edges")
    name: str | None = Field(default=None, description="Node name")
    summary: str | None = Field(default=None, description="Node summary")
    score: float | None = Field(default=None, description="Relevance score")


class ZepSearchMemoryData(BaseModel):
    """Output data for zep_search_memory tool."""

    session_id: str = Field(..., description="Zep session ID")
    query: str = Field(..., description="The search query that was executed")
    scope: str = Field(..., description="Search scope (edges or nodes)")
    results: list[ZepMemoryResult] = Field(
        default_factory=list, description="List of matching memory results"
    )


class ZepSessionData(BaseModel):
    """Output data for zep_get_session tool."""

    session_id: str = Field(..., description="Zep session ID")
    context: str | None = Field(None, description="Session context summary")
    message_count: int = Field(0, description="Number of messages in the session")


# =============================================================================
# Response Wrappers (inheriting from ToolResponse[T])
# =============================================================================


class Mem0AddMemoryResponse(ToolResponse[Mem0AddMemoryData]):
    """Response schema for mem0_add_memory tool."""

    pass


class Mem0SearchMemoryResponse(ToolResponse[Mem0SearchMemoryData]):
    """Response schema for mem0_search_memory tool."""

    pass


class Mem0GetMemoriesResponse(ToolResponse[Mem0GetMemoriesData]):
    """Response schema for mem0_get_memories tool."""

    pass


class ZepAddMemoryResponse(ToolResponse[ZepMessageData]):
    """Response schema for zep_add_memory tool."""

    pass


class ZepSearchMemoryResponse(ToolResponse[ZepSearchMemoryData]):
    """Response schema for zep_search_memory tool."""

    pass


class ZepGetSessionResponse(ToolResponse[ZepSessionData]):
    """Response schema for zep_get_session tool."""

    pass
