"""Tests for humcp routes module."""

from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.humcp.decorator import RegisteredTool
from src.humcp.routes import (
    _build_categories,
    _format_tag,
    build_openapi_tags,
    register_routes,
)


def make_registered_tool(
    name: str, category: str, description: str, parameters: dict, fn
) -> RegisteredTool:
    """Create a mock RegisteredTool for testing."""
    mock_tool = Mock()
    mock_tool.name = name
    mock_tool.description = description
    mock_tool.parameters = parameters
    mock_tool.output_schema = None
    mock_tool.fn = fn
    return RegisteredTool(tool=mock_tool, category=category)


@pytest.fixture
def sample_registrations():
    """Create sample tool registrations."""

    async def tool_one(value: str) -> dict:
        """First test tool."""
        return {"success": True, "data": {"value": value}}

    async def tool_two(a: int, b: int = 10) -> dict:
        """Second test tool."""
        return {"success": True, "data": {"result": a + b}}

    async def tool_three() -> dict:
        """Tool in other category."""
        return {"success": True, "data": {}}

    return [
        make_registered_tool(
            "test_tool_one",
            "test",
            "First test tool.",
            {
                "type": "object",
                "properties": {"value": {"type": "string"}},
                "required": ["value"],
            },
            tool_one,
        ),
        make_registered_tool(
            "test_tool_two",
            "test",
            "Second test tool.",
            {
                "type": "object",
                "properties": {
                    "a": {"type": "integer"},
                    "b": {"type": "integer"},
                },
                "required": ["a"],
            },
            tool_two,
        ),
        make_registered_tool(
            "other_tool",
            "other",
            "Tool in other category.",
            {"type": "object", "properties": {}, "required": []},
            tool_three,
        ),
    ]


class TestFormatTag:
    """Tests for _format_tag."""

    def test_lowercase(self):
        assert _format_tag("google") == "Google"

    def test_snake_case(self):
        assert _format_tag("local_files") == "Local Files"

    def test_empty(self):
        assert _format_tag("") == ""


class TestBuildOpenapiTags:
    """Tests for build_openapi_tags."""

    def test_includes_info_tag(self, sample_registrations):
        tags = build_openapi_tags(sample_registrations)
        assert tags[0]["name"] == "Info"

    def test_includes_category_tags(self, sample_registrations):
        tags = build_openapi_tags(sample_registrations)
        names = [t["name"] for t in tags]
        assert "Test" in names
        assert "Other" in names

    def test_empty_list(self):
        tags = build_openapi_tags([])
        assert len(tags) == 1
        assert tags[0]["name"] == "Info"


class TestBuildCategories:
    """Tests for _build_categories."""

    def test_builds_map(self, sample_registrations):
        cats = _build_categories(sample_registrations)
        assert "test" in cats
        assert len(cats["test"]) == 2

    def test_empty_list(self):
        assert _build_categories([]) == {}


class TestRegisterRoutes:
    """Tests for register_routes."""

    def test_registers_endpoints(self, sample_registrations, tmp_path):
        app = FastAPI()
        register_routes(app, tmp_path, sample_registrations)
        client = TestClient(app)

        resp = client.post("/tools/test_tool_one", json={"value": "test"})
        assert resp.status_code == 200

    def test_tools_list_endpoint(self, sample_registrations, tmp_path):
        app = FastAPI()
        register_routes(app, tmp_path, sample_registrations)
        client = TestClient(app)

        resp = client.get("/tools")
        assert resp.status_code == 200
        assert resp.json()["total_tools"] == 3

    def test_category_endpoint(self, sample_registrations, tmp_path):
        app = FastAPI()
        register_routes(app, tmp_path, sample_registrations)
        client = TestClient(app)

        resp = client.get("/tools/test")
        assert resp.status_code == 200
        assert resp.json()["count"] == 2

    def test_tool_info_endpoint(self, sample_registrations, tmp_path):
        app = FastAPI()
        register_routes(app, tmp_path, sample_registrations)
        client = TestClient(app)

        resp = client.get("/tools/test/test_tool_one")
        assert resp.status_code == 200
        assert "input_schema" in resp.json()

    def test_tool_execution(self, sample_registrations, tmp_path):
        app = FastAPI()
        register_routes(app, tmp_path, sample_registrations)
        client = TestClient(app)

        resp = client.post("/tools/test_tool_two", json={"a": 5})
        assert resp.status_code == 200
        assert resp.json()["result"]["data"]["result"] == 15

    def test_categories_endpoint(self, sample_registrations, tmp_path):
        app = FastAPI()
        register_routes(app, tmp_path, sample_registrations)
        client = TestClient(app)

        resp = client.get("/categories")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_categories"] == 2
        assert len(data["categories"]) == 2
        # Check categories are sorted
        names = [c["name"] for c in data["categories"]]
        assert names == ["other", "test"]
        # Check tool counts and skill field
        test_cat = next(c for c in data["categories"] if c["name"] == "test")
        assert test_cat["tool_count"] == 2
        assert test_cat["skill"] is None  # No SKILL.md in tmp_path
        other_cat = next(c for c in data["categories"] if c["name"] == "other")
        assert other_cat["tool_count"] == 1
        assert other_cat["skill"] is None  # No SKILL.md in tmp_path
