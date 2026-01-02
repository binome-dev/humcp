"""Tests for humcp routes module."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.humcp.decorator import tool
from src.humcp.registry import ToolRegistration
from src.humcp.routes import (
    _build_categories,
    _build_tool_lookup,
    _format_tag,
    _get_schema_from_func,
    build_openapi_tags,
    register_routes,
)


class TestFormatTag:
    """Tests for the _format_tag function."""

    def test_lowercase_to_title(self):
        """Should convert lowercase to title case."""
        assert _format_tag("google") == "Google"

    def test_snake_case_to_title(self):
        """Should convert snake_case to Title Case with spaces."""
        assert _format_tag("local_files") == "Local Files"

    def test_multiple_underscores(self):
        """Should handle multiple underscores."""
        assert _format_tag("my_long_category_name") == "My Long Category Name"

    def test_already_capitalized(self):
        """Should handle already capitalized strings."""
        assert _format_tag("Google") == "Google"

    def test_empty_string(self):
        """Should handle empty string."""
        assert _format_tag("") == ""

    def test_single_letter(self):
        """Should handle single letter."""
        assert _format_tag("a") == "A"


class TestBuildOpenapiTags:
    """Tests for the build_openapi_tags function."""

    def test_returns_list(self, register_sample_tools):
        """Should return a list of tag definitions."""
        tags = build_openapi_tags()
        assert isinstance(tags, list)

    def test_includes_info_tag_first(self, register_sample_tools):
        """Should include Info tag as first element."""
        tags = build_openapi_tags()
        assert tags[0]["name"] == "Info"
        assert "description" in tags[0]

    def test_includes_category_tags(self, register_sample_tools):
        """Should include tags for each category."""
        tags = build_openapi_tags()
        tag_names = [t["name"] for t in tags]

        assert "Test" in tag_names  # "test" -> "Test"
        assert "Other" in tag_names  # "other" -> "Other"

    def test_tag_has_name_and_description(self, register_sample_tools):
        """Each tag should have name and description."""
        tags = build_openapi_tags()

        for tag in tags:
            assert "name" in tag
            assert "description" in tag

    def test_category_tags_sorted(self, register_sample_tools):
        """Category tags should be sorted alphabetically."""
        tags = build_openapi_tags()

        # Skip Info tag (first)
        category_tags = tags[1:]
        tag_names = [t["name"] for t in category_tags]
        assert tag_names == sorted(tag_names)

    def test_description_includes_tool_count(self, register_sample_tools):
        """Category descriptions should include tool count."""
        tags = build_openapi_tags()

        test_tag = next(t for t in tags if t["name"] == "Test")
        assert "2 endpoints" in test_tag["description"]

        other_tag = next(t for t in tags if t["name"] == "Other")
        assert "1 endpoints" in other_tag["description"]

    def test_empty_registry(self):
        """Should return only Info tag when registry is empty."""
        tags = build_openapi_tags()
        assert len(tags) == 1
        assert tags[0]["name"] == "Info"


class TestGetSchemaFromFunc:
    """Tests for the _get_schema_from_func function."""

    def test_simple_string_param(self):
        """Should extract string parameter."""

        async def func(name: str):
            pass

        schema = _get_schema_from_func(func)
        assert schema["type"] == "object"
        assert schema["properties"]["name"]["type"] == "string"
        assert "name" in schema["required"]

    def test_integer_param(self):
        """Should extract integer parameter."""

        async def func(count: int):
            pass

        schema = _get_schema_from_func(func)
        assert schema["properties"]["count"]["type"] == "integer"

    def test_float_param(self):
        """Should extract float parameter."""

        async def func(value: float):
            pass

        schema = _get_schema_from_func(func)
        assert schema["properties"]["value"]["type"] == "number"

    def test_boolean_param(self):
        """Should extract boolean parameter."""

        async def func(flag: bool):
            pass

        schema = _get_schema_from_func(func)
        assert schema["properties"]["flag"]["type"] == "boolean"

    def test_list_param(self):
        """Should extract list parameter."""

        async def func(items: list):
            pass

        schema = _get_schema_from_func(func)
        assert schema["properties"]["items"]["type"] == "array"

    def test_dict_param(self):
        """Should extract dict parameter."""

        async def func(data: dict):
            pass

        schema = _get_schema_from_func(func)
        assert schema["properties"]["data"]["type"] == "object"

    def test_optional_param_not_required(self):
        """Should not include optional params in required list."""

        async def func(required_param: str, optional_param: str = "default"):
            pass

        schema = _get_schema_from_func(func)
        assert "required_param" in schema["required"]
        assert "optional_param" not in schema["required"]

    def test_union_with_none(self):
        """Should handle Union[type, None] (Optional)."""

        async def func(value: str | None):
            pass

        schema = _get_schema_from_func(func)
        assert schema["properties"]["value"]["type"] == "string"

    def test_multiple_params(self):
        """Should extract multiple parameters."""

        async def func(name: str, count: int, active: bool = True):
            pass

        schema = _get_schema_from_func(func)
        assert len(schema["properties"]) == 3
        assert schema["properties"]["name"]["type"] == "string"
        assert schema["properties"]["count"]["type"] == "integer"
        assert schema["properties"]["active"]["type"] == "boolean"
        assert "name" in schema["required"]
        assert "count" in schema["required"]
        assert "active" not in schema["required"]

    def test_no_params(self):
        """Should handle function with no parameters."""

        async def func():
            pass

        schema = _get_schema_from_func(func)
        assert schema["type"] == "object"
        assert schema["properties"] == {}
        assert schema["required"] == []

    def test_unknown_type_defaults_to_string(self):
        """Should default unknown types to string."""

        class CustomType:
            pass

        async def func(value: CustomType):
            pass

        schema = _get_schema_from_func(func)
        assert schema["properties"]["value"]["type"] == "string"


class TestBuildCategories:
    """Tests for the _build_categories function."""

    def test_builds_category_map(self, register_sample_tools):
        """Should build category map from registry."""
        categories = _build_categories()

        assert "test" in categories
        assert "other" in categories
        assert len(categories["test"]) == 2
        assert len(categories["other"]) == 1

    def test_category_entry_structure(self, register_sample_tools):
        """Category entries should have name, description, endpoint."""
        categories = _build_categories()

        tool_entry = categories["test"][0]
        assert "name" in tool_entry
        assert "description" in tool_entry
        assert "endpoint" in tool_entry
        assert tool_entry["endpoint"].startswith("/tools/")

    def test_empty_registry(self):
        """Should handle empty registry."""
        categories = _build_categories()
        assert categories == {}


class TestBuildToolLookup:
    """Tests for the _build_tool_lookup function."""

    def test_builds_lookup_map(self, register_sample_tools):
        """Should build (category, name) -> ToolRegistration map."""
        lookup = _build_tool_lookup()

        assert ("test", "test_tool_one") in lookup
        assert ("test", "test_tool_two") in lookup
        assert ("other", "other_category_tool") in lookup

    def test_lookup_returns_registration(self, register_sample_tools):
        """Lookup should return ToolRegistration objects."""
        lookup = _build_tool_lookup()

        reg = lookup[("test", "test_tool_one")]
        assert isinstance(reg, ToolRegistration)
        assert reg.name == "test_tool_one"
        assert reg.category == "test"

    def test_empty_registry(self):
        """Should handle empty registry."""
        lookup = _build_tool_lookup()
        assert lookup == {}


class TestRegisterRoutes:
    """Tests for the register_routes function."""

    def test_registers_tool_endpoints(self, register_sample_tools):
        """Should register POST endpoints for each tool."""
        app = FastAPI()
        register_routes(app)
        client = TestClient(app)

        response = client.post("/tools/test_tool_one", json={"value": "test"})
        assert response.status_code == 200

    def test_registers_info_endpoints(self, register_sample_tools):
        """Should register info endpoints."""
        app = FastAPI()
        register_routes(app)
        client = TestClient(app)

        # /tools endpoint
        response = client.get("/tools")
        assert response.status_code == 200
        data = response.json()
        assert "total_tools" in data
        assert "categories" in data

    def test_tool_execution_success(self, register_sample_tools):
        """Should execute tool and return result."""
        app = FastAPI()
        register_routes(app)
        client = TestClient(app)

        response = client.post("/tools/test_tool_one", json={"value": "hello"})
        assert response.status_code == 200
        data = response.json()
        assert data["result"]["success"] is True
        assert data["result"]["data"]["value"] == "hello"

    def test_tool_execution_with_defaults(self, register_sample_tools):
        """Should use default values for optional params."""
        app = FastAPI()
        register_routes(app)
        client = TestClient(app)

        response = client.post("/tools/test_tool_two", json={"a": 5})
        assert response.status_code == 200
        data = response.json()
        assert data["result"]["data"]["result"] == 15  # 5 + 10 (default)

    def test_tool_execution_error(self, register_sample_tools):
        """Should return 500 on tool execution failure."""

        @tool("failing_tool", category="test")
        async def failing_tool():
            raise ValueError("Intentional failure")

        app = FastAPI()
        register_routes(app)
        client = TestClient(app)

        response = client.post("/tools/failing_tool", json={})
        assert response.status_code == 500
        assert "Tool failed" in response.json()["detail"]

    def test_category_endpoint(self, register_sample_tools):
        """Should list tools in category."""
        app = FastAPI()
        register_routes(app)
        client = TestClient(app)

        response = client.get("/tools/test")
        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "test"
        assert data["count"] == 2
        tool_names = [t["name"] for t in data["tools"]]
        assert "test_tool_one" in tool_names
        assert "test_tool_two" in tool_names

    def test_category_not_found(self, register_sample_tools):
        """Should return 404 for nonexistent category."""
        app = FastAPI()
        register_routes(app)
        client = TestClient(app)

        response = client.get("/tools/nonexistent")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_tool_info_endpoint(self, register_sample_tools):
        """Should return tool info with schema."""
        app = FastAPI()
        register_routes(app)
        client = TestClient(app)

        response = client.get("/tools/test/test_tool_one")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test_tool_one"
        assert data["category"] == "test"
        assert "input_schema" in data
        assert data["endpoint"] == "/tools/test_tool_one"

    def test_tool_info_with_category_prefix(self, register_sample_tools):
        """Should find tool by name with category prefix removed."""
        app = FastAPI()
        register_routes(app)
        client = TestClient(app)

        # Access tool via shortened name (without category prefix)
        response = client.get("/tools/test/tool_one")
        # This should work because it tries f"{category}_{tool_name}"
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test_tool_one"

    def test_tool_info_not_found(self, register_sample_tools):
        """Should return 404 for nonexistent tool."""
        app = FastAPI()
        register_routes(app)
        client = TestClient(app)

        response = client.get("/tools/test/nonexistent_tool")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestToolInfoEndpointSchema:
    """Tests for input_schema in tool info endpoint."""

    def test_schema_contains_properties(self, register_sample_tools):
        """Should include property definitions in schema."""
        app = FastAPI()
        register_routes(app)
        client = TestClient(app)

        response = client.get("/tools/test/test_tool_two")
        data = response.json()

        schema = data["input_schema"]
        assert "a" in schema["properties"]
        assert "b" in schema["properties"]
        assert schema["properties"]["a"]["type"] == "integer"
        assert schema["properties"]["b"]["type"] == "integer"

    def test_schema_contains_required_fields(self, register_sample_tools):
        """Should mark required fields in schema."""
        app = FastAPI()
        register_routes(app)
        client = TestClient(app)

        response = client.get("/tools/test/test_tool_two")
        data = response.json()

        schema = data["input_schema"]
        assert "a" in schema["required"]
        assert "b" not in schema["required"]


class TestOpenApiCategoryTags:
    """Tests for OpenAPI category tags in tool endpoints."""

    def test_tool_routes_use_category_tags(self, register_sample_tools):
        """Tool routes should use formatted category as tag."""
        app = FastAPI()
        register_routes(app)

        # Get OpenAPI schema
        openapi = app.openapi()
        paths = openapi["paths"]

        # Check test_tool_one uses "Test" tag
        tool_one_path = paths.get("/tools/test_tool_one")
        assert tool_one_path is not None
        assert "Test" in tool_one_path["post"]["tags"]

        # Check other_category_tool uses "Other" tag
        other_tool_path = paths.get("/tools/other_category_tool")
        assert other_tool_path is not None
        assert "Other" in other_tool_path["post"]["tags"]

    def test_info_endpoints_use_info_tag(self, register_sample_tools):
        """Info endpoints should use 'Info' tag."""
        app = FastAPI()
        register_routes(app)

        openapi = app.openapi()
        paths = openapi["paths"]

        # Check /tools uses Info tag
        tools_path = paths.get("/tools")
        assert tools_path is not None
        assert "Info" in tools_path["get"]["tags"]

    def test_openapi_tags_metadata(self, register_sample_tools):
        """App with openapi_tags should have tag descriptions."""
        tags = build_openapi_tags()
        app = FastAPI(openapi_tags=tags)
        register_routes(app)

        openapi = app.openapi()
        assert "tags" in openapi

        tag_names = [t["name"] for t in openapi["tags"]]
        assert "Info" in tag_names
        assert "Test" in tag_names
        assert "Other" in tag_names


class TestListToolsEndpoint:
    """Tests for the /tools list endpoint."""

    def test_total_tools_count(self, register_sample_tools):
        """Should return correct total tool count."""
        app = FastAPI()
        register_routes(app)
        client = TestClient(app)

        response = client.get("/tools")
        data = response.json()
        assert data["total_tools"] == 3

    def test_categories_structure(self, register_sample_tools):
        """Should return categories with count and tools list."""
        app = FastAPI()
        register_routes(app)
        client = TestClient(app)

        response = client.get("/tools")
        data = response.json()

        assert "test" in data["categories"]
        assert data["categories"]["test"]["count"] == 2
        assert len(data["categories"]["test"]["tools"]) == 2

    def test_categories_sorted(self, register_sample_tools):
        """Should return categories in sorted order."""
        app = FastAPI()
        register_routes(app)
        client = TestClient(app)

        response = client.get("/tools")
        data = response.json()

        category_names = list(data["categories"].keys())
        assert category_names == sorted(category_names)
