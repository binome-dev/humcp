"""Tests for tool builder."""

import pytest
from src.tools.builder.manager import reset_custom_tool_manager
from src.tools.builder.sandbox import (
    CompilationError,
    ExecutionError,
    compile_code,
    execute_sandboxed,
    validate_tool_code,
)
from src.tools.builder.storage import (
    CustomToolDefinition,
    InMemoryToolStorage,
    reset_tool_storage,
)
from src.tools.builder.tools import (
    tool_builder_create,
    tool_builder_delete,
    tool_builder_disable,
    tool_builder_enable,
    tool_builder_get,
    tool_builder_list,
    tool_builder_test,
    tool_builder_update,
)


@pytest.fixture(autouse=True)
def reset_state():
    """Reset storage and manager state before each test."""
    reset_tool_storage()
    reset_custom_tool_manager()
    yield
    reset_tool_storage()
    reset_custom_tool_manager()


class TestSandboxCompilation:
    """Tests for sandbox code compilation."""

    def test_compile_valid_code(self):
        """Should compile valid Python code."""
        code = """
def execute(x: int) -> dict:
    return {"success": True, "data": x * 2}
"""
        compiled = compile_code(code)
        assert compiled is not None

    def test_compile_syntax_error(self):
        """Should raise CompilationError for syntax errors."""
        code = "def broken("
        with pytest.raises(CompilationError):
            compile_code(code)

    @pytest.mark.asyncio
    async def test_execute_restricted_import(self):
        """Should reject restricted imports at runtime."""
        code = """
import os
def execute() -> dict:
    return {"success": True}
"""
        # RestrictedPython allows compilation but blocks execution
        compiled = compile_code(code)
        with pytest.raises(ExecutionError):
            await execute_sandboxed(compiled, "execute", {})


class TestSandboxExecution:
    """Tests for sandboxed code execution."""

    @pytest.mark.asyncio
    async def test_execute_simple_function(self):
        """Should execute simple function."""
        code = """
def execute(text: str) -> dict:
    return {"success": True, "data": text.upper()}
"""
        compiled = compile_code(code)
        result = await execute_sandboxed(compiled, "execute", {"text": "hello"})

        assert result["success"] is True
        assert result["data"] == "HELLO"

    @pytest.mark.asyncio
    async def test_execute_with_math(self):
        """Should allow math operations."""
        code = """
def execute(a: int, b: int) -> dict:
    return {"success": True, "data": {"sum": a + b, "product": a * b}}
"""
        compiled = compile_code(code)
        result = await execute_sandboxed(compiled, "execute", {"a": 5, "b": 3})

        assert result["success"] is True
        assert result["data"]["sum"] == 8
        assert result["data"]["product"] == 15

    @pytest.mark.asyncio
    async def test_execute_with_allowed_imports(self):
        """Should allow using allowed imports."""
        code = """
def execute(data: dict) -> dict:
    result = json.dumps(data)
    return {"success": True, "data": result}
"""
        compiled = compile_code(code)
        result = await execute_sandboxed(
            compiled, "execute", {"data": {"key": "value"}}
        )

        assert result["success"] is True
        assert '"key"' in result["data"]

    @pytest.mark.asyncio
    async def test_execute_missing_function(self):
        """Should raise error for missing function."""
        code = """
def other_func() -> dict:
    return {}
"""
        compiled = compile_code(code)
        with pytest.raises(ExecutionError, match="not found"):
            await execute_sandboxed(compiled, "execute", {})

    @pytest.mark.asyncio
    async def test_execute_invalid_return_type(self):
        """Should raise error for non-dict return."""
        code = """
def execute() -> dict:
    return "not a dict"
"""
        compiled = compile_code(code)
        with pytest.raises(ExecutionError, match="must return a dict"):
            await execute_sandboxed(compiled, "execute", {})

    @pytest.mark.asyncio
    async def test_execute_with_list_operations(self):
        """Should allow list operations."""
        code = """
def execute(items: list) -> dict:
    return {"success": True, "data": sorted(items)}
"""
        compiled = compile_code(code)
        result = await execute_sandboxed(compiled, "execute", {"items": [3, 1, 2]})

        assert result["success"] is True
        assert result["data"] == [1, 2, 3]


class TestValidateToolCode:
    """Tests for code validation."""

    def test_validate_valid_code(self):
        """Should accept valid code."""
        code = """
def execute(x: int) -> dict:
    return {"success": True, "data": x}
"""
        is_valid, error = validate_tool_code(code)
        assert is_valid is True
        assert error == ""

    def test_validate_missing_execute(self):
        """Should reject code without execute function."""
        code = """
def other_function() -> dict:
    return {}
"""
        is_valid, error = validate_tool_code(code)
        assert is_valid is False
        assert "execute" in error

    def test_validate_syntax_error(self):
        """Should reject code with syntax errors."""
        code = "def broken("
        is_valid, error = validate_tool_code(code)
        assert is_valid is False


class TestInMemoryToolStorage:
    """Tests for in-memory storage."""

    @pytest.mark.asyncio
    async def test_save_and_get(self):
        """Should save and retrieve tools."""
        storage = InMemoryToolStorage()
        tool = CustomToolDefinition(
            name="test_tool",
            description="Test",
            code="def execute(): return {}",
            parameters={},
        )

        await storage.save(tool)
        retrieved = await storage.get("test_tool")

        assert retrieved is not None
        assert retrieved.name == "test_tool"

    @pytest.mark.asyncio
    async def test_delete(self):
        """Should delete tools."""
        storage = InMemoryToolStorage()
        tool = CustomToolDefinition(
            name="test_tool",
            description="Test",
            code="def execute(): return {}",
            parameters={},
        )

        await storage.save(tool)
        result = await storage.delete("test_tool")

        assert result is True
        assert await storage.get("test_tool") is None

    @pytest.mark.asyncio
    async def test_list_all(self):
        """Should list all tools."""
        storage = InMemoryToolStorage()

        await storage.save(
            CustomToolDefinition(name="tool1", description="", code="", parameters={})
        )
        await storage.save(
            CustomToolDefinition(name="tool2", description="", code="", parameters={})
        )

        tools = await storage.list_all()
        assert len(tools) == 2

    @pytest.mark.asyncio
    async def test_update(self):
        """Should update tool fields."""
        storage = InMemoryToolStorage()
        tool = CustomToolDefinition(
            name="test_tool",
            description="Original",
            code="def execute(): return {}",
            parameters={},
        )

        await storage.save(tool)
        updated = await storage.update("test_tool", description="Updated")

        assert updated is not None
        assert updated.description == "Updated"


class TestToolBuilderCreate:
    """Tests for tool_builder_create."""

    @pytest.mark.asyncio
    async def test_create_success(self):
        """Should create a custom tool."""
        result = await tool_builder_create(
            name="my_tool",
            description="Test tool",
            code="""
def execute(x: int) -> dict:
    return {"success": True, "data": x * 2}
""",
            parameters={"x": {"type": "integer"}},
        )

        assert result.success is True
        assert result.data.name == "my_tool"
        assert result.data.enabled is False

    @pytest.mark.asyncio
    async def test_create_duplicate(self):
        """Should reject duplicate names."""
        await tool_builder_create(
            name="duplicate",
            description="First",
            code="def execute(): return {}",
        )

        result = await tool_builder_create(
            name="duplicate",
            description="Second",
            code="def execute(): return {}",
        )

        assert result.success is False
        assert "already exists" in result.error

    @pytest.mark.asyncio
    async def test_create_invalid_code(self):
        """Should reject invalid code."""
        result = await tool_builder_create(
            name="bad_tool",
            description="Test",
            code="def broken(",
        )

        assert result.success is False
        assert "Invalid code" in result.error


class TestToolBuilderList:
    """Tests for tool_builder_list."""

    @pytest.mark.asyncio
    async def test_list_empty(self):
        """Should return empty list."""
        result = await tool_builder_list()

        assert result.success is True
        assert result.data == []

    @pytest.mark.asyncio
    async def test_list_multiple(self):
        """Should return all tools."""
        await tool_builder_create(
            name="tool1", description="", code="def execute(): return {}"
        )
        await tool_builder_create(
            name="tool2", description="", code="def execute(): return {}"
        )

        result = await tool_builder_list()

        assert result.success is True
        assert len(result.data) == 2


class TestToolBuilderGet:
    """Tests for tool_builder_get."""

    @pytest.mark.asyncio
    async def test_get_success(self):
        """Should return tool details."""
        await tool_builder_create(
            name="my_tool",
            description="Test",
            code="def execute(): return {}",
        )

        result = await tool_builder_get("my_tool")

        assert result.success is True
        assert result.data.name == "my_tool"

    @pytest.mark.asyncio
    async def test_get_not_found(self):
        """Should return error for missing tool."""
        result = await tool_builder_get("nonexistent")

        assert result.success is False
        assert "not found" in result.error


class TestToolBuilderDelete:
    """Tests for tool_builder_delete."""

    @pytest.mark.asyncio
    async def test_delete_success(self):
        """Should delete tool."""
        await tool_builder_create(
            name="to_delete",
            description="",
            code="def execute(): return {}",
        )

        result = await tool_builder_delete("to_delete")

        assert result.success is True

        # Verify deleted
        get_result = await tool_builder_get("to_delete")
        assert get_result.success is False

    @pytest.mark.asyncio
    async def test_delete_not_found(self):
        """Should return error for missing tool."""
        result = await tool_builder_delete("nonexistent")

        assert result.success is False
        assert "not found" in result.error


class TestToolBuilderUpdate:
    """Tests for tool_builder_update."""

    @pytest.mark.asyncio
    async def test_update_description(self):
        """Should update description."""
        await tool_builder_create(
            name="my_tool",
            description="Original",
            code="def execute(): return {}",
        )

        result = await tool_builder_update("my_tool", description="Updated")

        assert result.success is True
        assert result.data.description == "Updated"

    @pytest.mark.asyncio
    async def test_update_code(self):
        """Should update code."""
        await tool_builder_create(
            name="my_tool",
            description="Test",
            code="def execute(): return {'v': 1}",
        )

        new_code = "def execute(): return {'v': 2}"
        result = await tool_builder_update("my_tool", code=new_code)

        assert result.success is True
        assert result.data.code == new_code

    @pytest.mark.asyncio
    async def test_update_invalid_code(self):
        """Should reject invalid code."""
        await tool_builder_create(
            name="my_tool",
            description="Test",
            code="def execute(): return {}",
        )

        result = await tool_builder_update("my_tool", code="def broken(")

        assert result.success is False
        assert "Invalid code" in result.error


class TestToolBuilderTest:
    """Tests for tool_builder_test."""

    @pytest.mark.asyncio
    async def test_test_success(self):
        """Should execute tool and return result."""
        await tool_builder_create(
            name="double",
            description="Double a number",
            code="""
def execute(x: int) -> dict:
    return {"success": True, "data": x * 2}
""",
        )

        result = await tool_builder_test("double", params={"x": 5})

        assert result.success is True
        assert result.data.result["data"] == 10

    @pytest.mark.asyncio
    async def test_test_not_found(self):
        """Should return error for missing tool."""
        result = await tool_builder_test("nonexistent", params={})

        assert result.success is False
        assert "not found" in result.error


class TestToolBuilderEnableDisable:
    """Tests for enable/disable."""

    @pytest.mark.asyncio
    async def test_enable_success(self):
        """Should enable tool."""
        await tool_builder_create(
            name="my_tool",
            description="",
            code="def execute(): return {}",
        )

        result = await tool_builder_enable("my_tool")

        assert result.success is True
        assert result.data.enabled is True

    @pytest.mark.asyncio
    async def test_enable_already_enabled(self):
        """Should return error if already enabled."""
        await tool_builder_create(
            name="my_tool",
            description="",
            code="def execute(): return {}",
        )
        await tool_builder_enable("my_tool")

        result = await tool_builder_enable("my_tool")

        assert result.success is False
        assert "already enabled" in result.error

    @pytest.mark.asyncio
    async def test_disable_success(self):
        """Should disable tool."""
        await tool_builder_create(
            name="my_tool",
            description="",
            code="def execute(): return {}",
        )
        await tool_builder_enable("my_tool")

        result = await tool_builder_disable("my_tool")

        assert result.success is True
        assert result.data.enabled is False

    @pytest.mark.asyncio
    async def test_disable_already_disabled(self):
        """Should return error if already disabled."""
        await tool_builder_create(
            name="my_tool",
            description="",
            code="def execute(): return {}",
        )

        result = await tool_builder_disable("my_tool")

        assert result.success is False
        assert "already disabled" in result.error
