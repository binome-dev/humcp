"""Tests for humcp tool decorator."""

import asyncio

from src.humcp.decorator import (
    TOOL_ATTR,
    ToolMetadata,
    get_tool_category,
    get_tool_name,
    is_tool,
    tool,
)


class TestToolDecorator:
    """Tests for the @tool decorator."""

    def test_decorator_marks_function(self):
        """Should mark function with tool attribute."""

        @tool()
        async def my_func():
            pass

        assert is_tool(my_func)
        assert hasattr(my_func, TOOL_ATTR)

    def test_decorator_with_explicit_category(self):
        """Should store explicit category."""

        @tool(category="custom")
        async def func():
            pass

        assert get_tool_category(func) == "custom"

    def test_decorator_with_explicit_name(self):
        """Should store explicit name."""

        @tool("custom_name")
        async def func():
            pass

        assert get_tool_name(func) == "custom_name"

    def test_decorator_with_explicit_name_and_category(self):
        """Should store both explicit name and category."""

        @tool("my_tool", "my_category")
        async def func():
            pass

        assert get_tool_name(func) == "my_tool"
        assert get_tool_category(func) == "my_category"

    def test_decorator_auto_detects_category(self):
        """Should auto-detect category from file path."""

        @tool()
        async def func():
            pass

        # Category inferred from this file's parent dir (humcp)
        assert get_tool_category(func) == "humcp"

    def test_decorator_auto_detects_name(self):
        """Should auto-detect name from function name."""

        @tool()
        async def my_function():
            pass

        assert get_tool_name(my_function) == "my_function"

    def test_decorator_returns_original_function(self):
        """Decorated function should behave identically."""

        @tool()
        async def add(a: int, b: int) -> int:
            return a + b

        result = asyncio.get_event_loop().run_until_complete(add(2, 3))
        assert result == 5

    def test_decorator_preserves_function_metadata(self):
        """Should preserve function name and docstring."""

        @tool()
        async def documented_func(param: str) -> dict:
            """This is a docstring."""
            return {"param": param}

        assert documented_func.__name__ == "documented_func"
        assert documented_func.__doc__ == "This is a docstring."

    def test_decorator_with_sync_function(self):
        """Should work with synchronous functions."""

        @tool(category="test")
        def sync_func(x: int) -> int:
            return x * 2

        assert is_tool(sync_func)
        assert sync_func(5) == 10

    def test_decorator_with_no_params(self):
        """Should auto-detect name and category when no params given."""

        @tool()
        async def my_func():
            return {}

        assert is_tool(my_func)
        # Name from function name
        assert get_tool_name(my_func) == "my_func"
        # Category from file path (humcp)
        assert get_tool_category(my_func) == "humcp"


class TestIsTool:
    """Tests for is_tool function."""

    def test_returns_true_for_decorated(self):
        """Should return True for decorated functions."""

        @tool()
        def func():
            pass

        assert is_tool(func)

    def test_returns_false_for_undecorated(self):
        """Should return False for undecorated functions."""

        def func():
            pass

        assert not is_tool(func)


class TestGetToolName:
    """Tests for get_tool_name function."""

    def test_returns_name_for_decorated(self):
        """Should return name for decorated functions."""

        @tool("custom")
        def func():
            pass

        assert get_tool_name(func) == "custom"

    def test_returns_function_name_for_default(self):
        """Should return function name when no explicit name."""

        @tool()
        def my_tool():
            pass

        assert get_tool_name(my_tool) == "my_tool"

    def test_returns_function_name_for_undecorated(self):
        """Should return function name for undecorated functions."""

        def func():
            pass

        assert get_tool_name(func) == "func"


class TestGetToolCategory:
    """Tests for get_tool_category function."""

    def test_returns_category_for_decorated(self):
        """Should return category for decorated functions."""

        @tool(category="cat")
        def func():
            pass

        assert get_tool_category(func) == "cat"

    def test_returns_uncategorized_for_undecorated(self):
        """Should return 'uncategorized' for undecorated functions."""

        def func():
            pass

        assert get_tool_category(func) == "uncategorized"

    def test_metadata_attached_via_attribute(self):
        """ToolMetadata should be attached via TOOL_ATTR."""

        @tool("test_name", "test_cat")
        def func():
            pass

        assert hasattr(func, TOOL_ATTR)
        metadata = getattr(func, TOOL_ATTR)
        assert isinstance(metadata, ToolMetadata)
        assert metadata.name == "test_name"
        assert metadata.category == "test_cat"
