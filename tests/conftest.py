"""Shared fixtures for all tests."""

import pytest

from src.humcp.registry import _TOOL_NAMES, TOOL_REGISTRY


@pytest.fixture(autouse=True)
def clear_tool_registry():
    """Clear the tool registry before and after each test.

    This ensures tests don't interfere with each other by leaving
    tools registered from previous tests.
    """
    # Store original state
    original_registry = TOOL_REGISTRY.copy()
    original_names = _TOOL_NAMES.copy()

    # Clear for test
    TOOL_REGISTRY.clear()
    _TOOL_NAMES.clear()

    yield

    # Restore original state after test
    TOOL_REGISTRY.clear()
    TOOL_REGISTRY.extend(original_registry)
    _TOOL_NAMES.clear()
    _TOOL_NAMES.update(original_names)


@pytest.fixture
def sample_tool_func():
    """Create a sample async tool function for testing."""

    async def sample_func(param: str) -> dict:
        """A sample tool function."""
        return {"success": True, "data": {"param": param}}

    return sample_func


@pytest.fixture
def register_sample_tools():
    """Register sample tools for testing routes and server."""
    from src.humcp.decorator import tool

    @tool("test_tool_one", category="test")
    async def tool_one(value: str) -> dict:
        """First test tool."""
        return {"success": True, "data": {"value": value}}

    @tool("test_tool_two", category="test")
    async def tool_two(a: int, b: int = 10) -> dict:
        """Second test tool with optional param."""
        return {"success": True, "data": {"result": a + b}}

    @tool("other_category_tool", category="other")
    async def tool_three() -> dict:
        """Tool in different category."""
        return {"success": True, "data": {}}

    return [tool_one, tool_two, tool_three]
