"""Shared fixtures for all tests."""

import pytest


@pytest.fixture(autouse=True)
def allow_absolute_paths_for_tests(monkeypatch):
    """Allow absolute paths in filesystem tools during tests."""
    monkeypatch.setenv("HUMCP_ALLOW_ABSOLUTE_PATHS", "true")


@pytest.fixture
def sample_tools(tmp_path):
    """Create sample tool files for testing."""
    # test category
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    (test_dir / "tool_one.py").write_text('''
from src.humcp.decorator import tool

@tool(category="test")
async def test_tool_one(value: str) -> dict:
    """First test tool."""
    return {"success": True, "data": {"value": value}}
''')

    (test_dir / "tool_two.py").write_text('''
from src.humcp.decorator import tool

@tool(category="test")
async def test_tool_two(a: int, b: int = 10) -> dict:
    """Second test tool."""
    return {"success": True, "data": {"result": a + b}}
''')

    # other category
    other_dir = tmp_path / "other"
    other_dir.mkdir()

    (other_dir / "tool_three.py").write_text('''
from src.humcp.decorator import tool

@tool(category="other")
async def other_tool() -> dict:
    """Tool in other category."""
    return {"success": True, "data": {}}
''')

    return tmp_path
