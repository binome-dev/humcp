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
            "calculator_add": self._create_mock_tool("calculator_add"),
        }
        generator = self._create_route_generator(tools)

        categories = generator._get_tool_categories()

        assert "calculator" in categories
        assert len(categories["calculator"]) == 1
        assert categories["calculator"][0]["name"] == "add"
        assert categories["calculator"][0]["full_name"] == "calculator_add"

    def test_single_category_multiple_tools(self):
        tools = {
            "calculator_add": self._create_mock_tool("calculator_add"),
            "calculator_subtract": self._create_mock_tool("calculator_subtract"),
            "calculator_multiply": self._create_mock_tool("calculator_multiply"),
        }
        generator = self._create_route_generator(tools)

        categories = generator._get_tool_categories()

        assert "calculator" in categories
        assert len(categories["calculator"]) == 3

    def test_multiple_categories(self):
        tools = {
            "calculator_add": self._create_mock_tool("calculator_add"),
            "filesystem_read": self._create_mock_tool("filesystem_read"),
            "shell_execute": self._create_mock_tool("shell_execute"),
        }
        generator = self._create_route_generator(tools)

        categories = generator._get_tool_categories()

        assert len(categories) == 3
        assert "calculator" in categories
        assert "filesystem" in categories
        assert "shell" in categories
        assert len(categories["calculator"]) == 1
        assert len(categories["filesystem"]) == 1
        assert len(categories["shell"]) == 1

    def test_uncategorized_tool(self):
        tools = {
            "simpletool": self._create_mock_tool("simpletool"),
        }
        generator = self._create_route_generator(tools)

        categories = generator._get_tool_categories()

        assert "uncategorized" in categories
        assert len(categories["uncategorized"]) == 1
        assert categories["uncategorized"][0]["name"] == "simpletool"

    def test_mixed_categorized_and_uncategorized(self):
        tools = {
            "calculator_add": self._create_mock_tool("calculator_add"),
            "simpletool": self._create_mock_tool("simpletool"),
        }
        generator = self._create_route_generator(tools)

        categories = generator._get_tool_categories()

        assert len(categories) == 2
        assert "calculator" in categories
        assert "uncategorized" in categories

    def test_nested_category_path(self):
        tools = {
            "data_csv_read": self._create_mock_tool("data_csv_read"),
        }
        generator = self._create_route_generator(tools)

        categories = generator._get_tool_categories()

        assert "data" in categories
        assert len(categories["data"]) == 1
        assert categories["data"][0]["name"] == "csv_read"
        assert categories["data"][0]["full_name"] == "data_csv_read"

    def test_empty_tools(self):
        tools = {}
        generator = self._create_route_generator(tools)

        categories = generator._get_tool_categories()

        assert categories == {}

    def test_tool_endpoint_path(self):
        tools = {
            "calculator_add": self._create_mock_tool("calculator_add"),
        }
        generator = self._create_route_generator(tools)

        categories = generator._get_tool_categories()

        expected_endpoint = "/tools/calculator_add"
        assert categories["calculator"][0]["endpoint"] == expected_endpoint

    def test_custom_route_prefix(self):
        mock_client = MagicMock()
        generator = RouteGenerator(client=mock_client, route_prefix="/api/v1/tools")
        generator.tools = {
            "calculator_add": self._create_mock_tool("calculator_add"),
        }

        categories = generator._get_tool_categories()

        expected_endpoint = "/api/v1/tools/calculator_add"
        assert categories["calculator"][0]["endpoint"] == expected_endpoint

    def test_tool_description_preserved(self):
        tools = {
            "calculator_add": self._create_mock_tool(
                "calculator_add", description="Add two numbers together"
            ),
        }
        generator = self._create_route_generator(tools)

        categories = generator._get_tool_categories()

        assert categories["calculator"][0]["description"] == "Add two numbers together"


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
