from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp.types import Tool

from src.adapter.routes import RouteGenerator


class TestGetToolCategories:
    def _create_mock_tool(self, name: str, description: str = None) -> Tool:
        tool = MagicMock(spec=Tool)
        tool.name = name
        tool.description = description or f"Description for {name}"
        tool.inputSchema = {"type": "object", "properties": {}}
        return tool

    def _create_route_generator(self, tools: dict) -> RouteGenerator:
        mock_client = MagicMock()
        generator = RouteGenerator(client=mock_client)
        generator.tools = tools
        return generator

    def test_single_category_single_tool(self):
        tools = {
            "calculator/add": self._create_mock_tool("calculator/add"),
        }
        generator = self._create_route_generator(tools)

        categories = generator._get_tool_categories()

        assert "calculator" in categories
        assert categories["calculator"]["tools_count"] == 1
        assert len(categories["calculator"]["tools"]) == 1
        assert categories["calculator"]["tools"][0]["name"] == "add"
        assert categories["calculator"]["tools"][0]["full_name"] == "calculator/add"

    def test_single_category_multiple_tools(self):
        tools = {
            "calculator/add": self._create_mock_tool("calculator/add"),
            "calculator/subtract": self._create_mock_tool("calculator/subtract"),
            "calculator/multiply": self._create_mock_tool("calculator/multiply"),
        }
        generator = self._create_route_generator(tools)

        categories = generator._get_tool_categories()

        assert "calculator" in categories
        assert categories["calculator"]["tools_count"] == 3
        assert len(categories["calculator"]["tools"]) == 3

    def test_multiple_categories(self):
        tools = {
            "calculator/add": self._create_mock_tool("calculator/add"),
            "filesystem/read": self._create_mock_tool("filesystem/read"),
            "shell/execute": self._create_mock_tool("shell/execute"),
        }
        generator = self._create_route_generator(tools)

        categories = generator._get_tool_categories()

        assert len(categories) == 3
        assert "calculator" in categories
        assert "filesystem" in categories
        assert "shell" in categories
        assert categories["calculator"]["tools_count"] == 1
        assert categories["filesystem"]["tools_count"] == 1
        assert categories["shell"]["tools_count"] == 1

    def test_uncategorized_tool(self):
        tools = {
            "simple_tool": self._create_mock_tool("simple_tool"),
        }
        generator = self._create_route_generator(tools)

        categories = generator._get_tool_categories()

        assert "uncategorized" in categories
        assert categories["uncategorized"]["tools_count"] == 1
        assert categories["uncategorized"]["tools"][0]["name"] == "simple_tool"

    def test_mixed_categorized_and_uncategorized(self):
        tools = {
            "calculator/add": self._create_mock_tool("calculator/add"),
            "simple_tool": self._create_mock_tool("simple_tool"),
        }
        generator = self._create_route_generator(tools)

        categories = generator._get_tool_categories()

        assert len(categories) == 2
        assert "calculator" in categories
        assert "uncategorized" in categories

    def test_nested_category_path(self):
        tools = {
            "data/csv/read": self._create_mock_tool("data/csv/read"),
        }
        generator = self._create_route_generator(tools)

        categories = generator._get_tool_categories()

        assert "data" in categories
        assert categories["data"]["tools_count"] == 1
        # The sub_tool should be "csv/read" (everything after first /)
        assert categories["data"]["tools"][0]["name"] == "csv/read"
        assert categories["data"]["tools"][0]["full_name"] == "data/csv/read"

    def test_empty_tools(self):
        tools = {}
        generator = self._create_route_generator(tools)

        categories = generator._get_tool_categories()

        assert categories == {}

    def test_tool_endpoint_path(self):
        tools = {
            "calculator/add": self._create_mock_tool("calculator/add"),
        }
        generator = self._create_route_generator(tools)

        categories = generator._get_tool_categories()

        expected_endpoint = "/tools/calculator/add"
        assert categories["calculator"]["tools"][0]["endpoint"] == expected_endpoint

    def test_custom_route_prefix(self):
        mock_client = MagicMock()
        generator = RouteGenerator(client=mock_client, route_prefix="/api/v1/tools")
        generator.tools = {
            "calculator/add": self._create_mock_tool("calculator/add"),
        }

        categories = generator._get_tool_categories()

        expected_endpoint = "/api/v1/tools/calculator/add"
        assert categories["calculator"]["tools"][0]["endpoint"] == expected_endpoint

    def test_tool_description_preserved(self):
        tools = {
            "calculator/add": self._create_mock_tool(
                "calculator/add", description="Add two numbers together"
            ),
        }
        generator = self._create_route_generator(tools)

        categories = generator._get_tool_categories()

        assert (
            categories["calculator"]["tools"][0]["description"]
            == "Add two numbers together"
        )


class TestRouteGeneratorInit:
    def test_default_route_prefix(self):
        mock_client = MagicMock()
        generator = RouteGenerator(client=mock_client)

        assert generator.route_prefix == "/tools"

    def test_custom_route_prefix(self):
        mock_client = MagicMock()
        generator = RouteGenerator(client=mock_client, route_prefix="/api/tools/")

        assert generator.route_prefix == "/api/tools"

    def test_default_tags(self):
        mock_client = MagicMock()
        generator = RouteGenerator(client=mock_client)

        assert generator.tags == ["MCP Tools"]

    def test_custom_tags(self):
        mock_client = MagicMock()
        generator = RouteGenerator(client=mock_client, tags=["Custom", "Tags"])

        assert generator.tags == ["Custom", "Tags"]

    def test_empty_tools_initially(self):
        mock_client = MagicMock()
        generator = RouteGenerator(client=mock_client)

        assert generator.tools == {}


class TestLoadTools:
    def _create_mock_tool_with_name(self, name: str) -> MagicMock:
        tool = MagicMock()
        tool.name = name  # Set as attribute, not spec
        tool.description = f"Description for {name}"
        tool.inputSchema = {}
        return tool

    @pytest.mark.asyncio
    async def test_load_tools_converts_list_to_dict(self):
        mock_client = MagicMock()
        tool1 = self._create_mock_tool_with_name("tool1")
        tool2 = self._create_mock_tool_with_name("tool2")
        mock_client.list_tools = AsyncMock(return_value=[tool1, tool2])

        generator = RouteGenerator(client=mock_client)
        result = await generator.load_tools()

        assert "tool1" in result
        assert "tool2" in result
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_load_tools_empty_list(self):
        mock_client = MagicMock()
        mock_client.list_tools = AsyncMock(return_value=[])

        generator = RouteGenerator(client=mock_client)
        result = await generator.load_tools()

        assert result == {}
