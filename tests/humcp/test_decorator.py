"""Tests for humcp tool decorator."""

import asyncio

from src.humcp.decorator import TOOL_REGISTRY, ToolRegistration, tool


class TestToolDecorator:
    def test_decorator_with_name(self):
        initial_count = len(TOOL_REGISTRY)

        @tool("test_tool_with_name")
        async def my_func():
            pass

        assert len(TOOL_REGISTRY) == initial_count + 1
        registration = TOOL_REGISTRY[-1]
        assert registration.name == "test_tool_with_name"
        assert registration.func is my_func

    def test_decorator_defaults_to_function_name(self):
        initial_count = len(TOOL_REGISTRY)

        @tool()
        async def another_test_func():
            pass

        assert len(TOOL_REGISTRY) == initial_count + 1
        registration = TOOL_REGISTRY[-1]
        assert registration.name == "another_test_func"

    def test_decorator_with_category(self):
        initial_count = len(TOOL_REGISTRY)

        @tool("categorized_tool", category="custom_category")
        async def categorized_func():
            pass

        assert len(TOOL_REGISTRY) == initial_count + 1
        registration = TOOL_REGISTRY[-1]
        assert registration.category == "custom_category"

    def test_decorator_returns_original_function(self):
        @tool("preserved_func")
        async def original_func(a: int, b: int) -> int:
            return a + b

        result = asyncio.get_event_loop().run_until_complete(original_func(2, 3))
        assert result == 5


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
