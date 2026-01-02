"""HuMCP - Human-friendly MCP server with FastAPI adapter."""

from src.humcp.registry import TOOL_REGISTRY, ToolRegistration
from src.humcp.schemas import (
    CategorySummary,
    GetCategoryResponse,
    GetToolResponse,
    InputSchema,
    ListToolsResponse,
    SkillFull,
    SkillMetadata,
    ToolSummary,
)
from src.humcp.skills import (
    Skill,
    discover_skills,
    get_skill_content,
    get_skills_by_category,
)

__all__ = [
    # Registry
    "TOOL_REGISTRY",
    "ToolRegistration",
    # Skills
    "Skill",
    "discover_skills",
    "get_skill_content",
    "get_skills_by_category",
    # Schemas
    "CategorySummary",
    "GetCategoryResponse",
    "GetToolResponse",
    "InputSchema",
    "ListToolsResponse",
    "SkillFull",
    "SkillMetadata",
    "ToolSummary",
]
