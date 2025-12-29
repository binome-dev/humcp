"""Tests for humcp tool decorator."""

import asyncio

from src.humcp.decorator import _TOOL_NAMES, TOOL_REGISTRY, ToolRegistration, tool


class TestToolDecorator:
    def setup_method(self):
        """Clear registry before each test."""
        TOOL_REGISTRY.clear()
        _TOOL_NAMES.clear()

    def test_decorator_with_explicit_name(self):
        @tool("my_explicit_tool")
        async def my_func():
            pass

        assert len(TOOL_REGISTRY) == 1
        reg = TOOL_REGISTRY[-1]
        assert reg.name == "my_explicit_tool"
        assert reg.func is my_func

    def test_decorator_auto_generates_name_from_category_and_func(self):
        @tool(category="test_category")
        async def my_func():
            pass

        reg = TOOL_REGISTRY[-1]
        assert reg.name == "test_category_my_func"
        assert reg.category == "test_category"

    def test_decorator_with_explicit_category(self):
        @tool("tool_name", category="custom_category")
        async def categorized_func():
            pass

        reg = TOOL_REGISTRY[-1]
        assert reg.category == "custom_category"
        assert reg.name == "tool_name"

    def test_decorator_returns_original_function(self):
        @tool("preserved_func", category="test")
        async def original_func(a: int, b: int) -> int:
            return a + b

        result = asyncio.get_event_loop().run_until_complete(original_func(2, 3))
        assert result == 5

    def test_duplicate_name_raises_error(self):
        @tool("duplicate_tool", category="test")
        async def func1():
            pass

        try:

            @tool("duplicate_tool", category="test")
            async def func2():
                pass

            raise AssertionError("Should have raised ValueError")
        except ValueError as e:
            assert "Duplicate tool name" in str(e)


class TestToolRegistration:
    def test_tool_registration_frozen(self):
        def dummy_func():
            return None

        registration = ToolRegistration(
            name="test", category="test_cat", func=dummy_func
        )
        try:
            registration.name = "new_name"
            raise AssertionError("Should have raised an error")
        except Exception:
            pass

    def test_tool_registration_equality(self):
        def dummy_func():
            return None

        reg1 = ToolRegistration(name="test", category="cat", func=dummy_func)
        reg2 = ToolRegistration(name="test", category="cat", func=dummy_func)
        assert reg1 == reg2
