"""Tests for humcp tool decorator."""

import asyncio

import pytest

from src.humcp.decorator import tool
from src.humcp.registry import _TOOL_NAMES, TOOL_REGISTRY, ToolRegistration


class TestToolDecorator:
    """Tests for the @tool decorator."""

    def test_decorator_with_explicit_name(self):
        """Should register tool with explicit name."""

        @tool("my_explicit_tool")
        async def my_func():
            pass

        assert len(TOOL_REGISTRY) == 1
        reg = TOOL_REGISTRY[-1]
        assert reg.name == "my_explicit_tool"
        assert reg.func is my_func

    def test_decorator_auto_generates_name_from_category_and_func(self):
        """Should auto-generate name as category_funcname when no name given."""

        @tool(category="test_category")
        async def my_func():
            pass

        reg = TOOL_REGISTRY[-1]
        assert reg.name == "test_category_my_func"
        assert reg.category == "test_category"

    def test_decorator_with_explicit_category(self):
        """Should use explicit category when provided."""

        @tool("tool_name", category="custom_category")
        async def categorized_func():
            pass

        reg = TOOL_REGISTRY[-1]
        assert reg.category == "custom_category"
        assert reg.name == "tool_name"

    def test_decorator_default_category(self):
        """Should use 'humcp' category when not specified."""

        @tool("default_cat_tool")
        async def default_cat_func():
            pass

        reg = TOOL_REGISTRY[-1]
        assert reg.category == "humcp"

    def test_decorator_returns_original_function(self):
        """Decorated function should behave identically to original."""

        @tool("preserved_func", category="test")
        async def original_func(a: int, b: int) -> int:
            return a + b

        result = asyncio.get_event_loop().run_until_complete(original_func(2, 3))
        assert result == 5

    def test_decorator_preserves_function_metadata(self):
        """Should preserve function name and docstring."""

        @tool("metadata_tool", category="test")
        async def documented_func(param: str) -> dict:
            """This is a docstring."""
            return {"param": param}

        assert documented_func.__name__ == "documented_func"
        assert documented_func.__doc__ == "This is a docstring."

    def test_duplicate_name_raises_value_error(self):
        """Should raise ValueError when registering duplicate tool name."""

        @tool("duplicate_tool", category="test")
        async def func1():
            pass

        with pytest.raises(ValueError, match="Duplicate tool name"):

            @tool("duplicate_tool", category="test")
            async def func2():
                pass

    def test_decorator_with_sync_function(self):
        """Should work with synchronous functions."""

        @tool("sync_tool", category="test")
        def sync_func(x: int) -> int:
            return x * 2

        assert len(TOOL_REGISTRY) >= 1
        reg = TOOL_REGISTRY[-1]
        assert reg.name == "sync_tool"
        assert sync_func(5) == 10

    def test_decorator_with_no_params(self):
        """Should register tool with no parameters."""

        @tool("no_param_tool", category="test")
        async def no_param_func() -> dict:
            return {"success": True}

        reg = TOOL_REGISTRY[-1]
        assert reg.name == "no_param_tool"

    def test_decorator_with_type_hints(self):
        """Should register tool with complex type hints."""

        @tool("typed_tool", category="test")
        async def typed_func(
            required: str,
            optional: int = 10,
            nullable: str | None = None,
        ) -> dict:
            return {"required": required, "optional": optional}

        reg = TOOL_REGISTRY[-1]
        assert reg.name == "typed_tool"


class TestToolRegistration:
    """Tests for the ToolRegistration dataclass."""

    def test_tool_registration_frozen(self):
        """ToolRegistration should be immutable (frozen)."""

        def dummy_func():
            return None

        registration = ToolRegistration(
            name="test", category="test_cat", func=dummy_func
        )

        with pytest.raises((AttributeError, TypeError)):
            registration.name = "new_name"

    def test_tool_registration_equality(self):
        """ToolRegistrations with same values should be equal."""

        def dummy_func():
            return None

        reg1 = ToolRegistration(name="test", category="cat", func=dummy_func)
        reg2 = ToolRegistration(name="test", category="cat", func=dummy_func)
        assert reg1 == reg2

    def test_tool_registration_inequality_name(self):
        """ToolRegistrations with different names should not be equal."""

        def dummy_func():
            return None

        reg1 = ToolRegistration(name="test1", category="cat", func=dummy_func)
        reg2 = ToolRegistration(name="test2", category="cat", func=dummy_func)
        assert reg1 != reg2

    def test_tool_registration_inequality_category(self):
        """ToolRegistrations with different categories should not be equal."""

        def dummy_func():
            return None

        reg1 = ToolRegistration(name="test", category="cat1", func=dummy_func)
        reg2 = ToolRegistration(name="test", category="cat2", func=dummy_func)
        assert reg1 != reg2

    def test_tool_registration_hashable(self):
        """ToolRegistration should be hashable for use in sets."""

        def dummy_func():
            return None

        reg = ToolRegistration(name="test", category="cat", func=dummy_func)
        # Should not raise
        hash(reg)
        # Should be usable in set
        s = {reg}
        assert reg in s


class TestToolRegistry:
    """Tests for the global TOOL_REGISTRY."""

    def test_registry_is_list(self):
        """TOOL_REGISTRY should be a list."""
        assert isinstance(TOOL_REGISTRY, list)

    def test_registry_stores_registrations(self):
        """TOOL_REGISTRY should contain ToolRegistration objects."""

        @tool("registry_test", category="test")
        async def test_func():
            pass

        assert len(TOOL_REGISTRY) >= 1
        assert all(isinstance(reg, ToolRegistration) for reg in TOOL_REGISTRY)

    def test_tool_names_tracks_names(self):
        """_TOOL_NAMES should track registered names."""

        @tool("tracked_tool", category="test")
        async def tracked_func():
            pass

        assert "tracked_tool" in _TOOL_NAMES


class TestDecoratorEdgeCases:
    """Tests for edge cases in the @tool decorator."""

    def test_empty_name_uses_auto_generation(self):
        """Empty string name should trigger auto-generation."""

        @tool("", category="edge")
        async def empty_name_func():
            pass

        reg = TOOL_REGISTRY[-1]
        # Empty name should auto-generate
        assert reg.name == "edge_empty_name_func"

    def test_whitespace_category(self):
        """Category with only whitespace should be handled."""

        @tool("whitespace_cat_tool", category="  ")
        async def whitespace_cat_func():
            pass

        reg = TOOL_REGISTRY[-1]
        assert reg.category == "  "  # Preserves as-is

    def test_unicode_name(self):
        """Should handle unicode characters in names."""

        @tool("unicode_tool_\u00e9", category="test")
        async def unicode_func():
            pass

        reg = TOOL_REGISTRY[-1]
        assert reg.name == "unicode_tool_\u00e9"
