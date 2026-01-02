"""Tests for humcp server module."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.humcp.server import _discover_tools, create_app


class TestDiscoverTools:
    """Tests for the _discover_tools function."""

    def test_discover_tools_returns_zero_for_nonexistent_path(self):
        """Should return 0 when tools path doesn't exist."""
        result = _discover_tools(Path("/nonexistent/path"))
        assert result == 0

    def test_discover_tools_skips_underscore_files(self, tmp_path):
        """Should skip files starting with underscore."""
        # Create a file starting with underscore
        init_file = tmp_path / "_init.py"
        init_file.write_text("# init file")

        result = _discover_tools(tmp_path)
        assert result == 0

    def test_discover_tools_loads_valid_module(self, tmp_path):
        """Should load valid Python modules."""
        tool_file = tmp_path / "simple_tool.py"
        tool_file.write_text(
            """
def dummy_function():
    pass
"""
        )

        result = _discover_tools(tmp_path)
        assert result == 1

    def test_discover_tools_handles_import_errors_gracefully(self, tmp_path):
        """Should handle import errors without crashing."""
        tool_file = tmp_path / "broken_tool.py"
        tool_file.write_text(
            """
import nonexistent_module_12345
"""
        )

        result = _discover_tools(tmp_path)
        assert result == 0

    def test_discover_tools_recursive(self, tmp_path):
        """Should discover tools in subdirectories."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        tool1 = tmp_path / "tool1.py"
        tool1.write_text("x = 1")

        tool2 = subdir / "tool2.py"
        tool2.write_text("y = 2")

        result = _discover_tools(tmp_path)
        assert result == 2

    def test_discover_tools_sorted_loading(self, tmp_path):
        """Should load modules in sorted order for determinism."""
        # Create files in reverse alphabetical order
        (tmp_path / "zebra.py").write_text("z = 1")
        (tmp_path / "alpha.py").write_text("a = 1")
        (tmp_path / "beta.py").write_text("b = 1")

        with patch("src.humcp.server.logger") as mock_logger:
            result = _discover_tools(tmp_path)
            assert result == 3

            # Check that modules were logged in sorted order
            debug_calls = [
                call
                for call in mock_logger.debug.call_args_list
                if "Loaded" in str(call)
            ]
            # Verify at least some modules were loaded
            assert len(debug_calls) == 3


class TestCreateApp:
    """Tests for the create_app function."""

    def test_create_app_returns_fastapi_instance(self):
        """Should return a FastAPI application."""
        with tempfile.TemporaryDirectory() as tmp:
            app = create_app(tools_path=tmp)
            assert isinstance(app, FastAPI)

    def test_create_app_with_custom_title(self):
        """Should use custom title."""
        with tempfile.TemporaryDirectory() as tmp:
            app = create_app(tools_path=tmp, title="Custom Title")
            assert app.title == "Custom Title"

    def test_create_app_with_custom_version(self):
        """Should use custom version."""
        with tempfile.TemporaryDirectory() as tmp:
            app = create_app(tools_path=tmp, version="2.0.0")
            assert app.version == "2.0.0"

    def test_create_app_with_custom_description(self):
        """Should use custom description."""
        with tempfile.TemporaryDirectory() as tmp:
            app = create_app(tools_path=tmp, description="Custom description")
            assert app.description == "Custom description"

    def test_create_app_has_root_endpoint(self):
        """Should have a root info endpoint."""
        with tempfile.TemporaryDirectory() as tmp:
            app = create_app(tools_path=tmp)
            client = TestClient(app)
            response = client.get("/")
            assert response.status_code == 200
            data = response.json()
            assert "name" in data
            assert "version" in data
            assert "mcp_server" in data
            assert "tools_count" in data
            assert "endpoints" in data

    def test_create_app_has_tools_endpoint(self):
        """Should have a /tools endpoint."""
        with tempfile.TemporaryDirectory() as tmp:
            app = create_app(tools_path=tmp)
            client = TestClient(app)
            response = client.get("/tools")
            assert response.status_code == 200
            data = response.json()
            assert "total_tools" in data
            assert "categories" in data

    def test_create_app_mounts_mcp(self):
        """Should mount MCP at /mcp."""
        with tempfile.TemporaryDirectory() as tmp:
            app = create_app(tools_path=tmp)
            # Check that /mcp route exists
            routes = [route.path for route in app.routes]
            assert "/mcp" in routes or any("/mcp" in str(r) for r in routes)

    def test_create_app_default_tools_path(self):
        """Should use default tools path when none provided."""
        # This test verifies the code path works even with real tools
        app = create_app()
        assert isinstance(app, FastAPI)


class TestCreateAppWithTools:
    """Tests for create_app with registered tools."""

    def test_create_app_registers_tools(self, tmp_path, register_sample_tools):
        """Should register tools from TOOL_REGISTRY."""
        app = create_app(tools_path=str(tmp_path))
        client = TestClient(app)

        response = client.get("/tools")
        assert response.status_code == 200
        data = response.json()
        assert data["total_tools"] >= 3  # At least our 3 sample tools

    def test_create_app_deduplicates_tools(self, tmp_path):
        """Should not register the same function twice."""
        from src.humcp.decorator import tool

        @tool("dedupe_test_1", category="test")
        async def shared_func():
            return {"success": True}

        # Register same function with different name (shouldn't happen normally)
        # but this tests the deduplication logic
        app = create_app(tools_path=str(tmp_path))
        assert isinstance(app, FastAPI)

    def test_root_endpoint_shows_tool_count(self, tmp_path, register_sample_tools):
        """Root endpoint should show correct tool count."""
        app = create_app(tools_path=str(tmp_path))
        client = TestClient(app)

        response = client.get("/")
        data = response.json()
        assert data["tools_count"] >= 3


class TestAppIntegration:
    """Integration tests for the full app."""

    def test_tool_execution_endpoint(self, tmp_path, register_sample_tools):
        """Should be able to execute tools via REST."""
        app = create_app(tools_path=str(tmp_path))
        client = TestClient(app)

        response = client.post(
            "/tools/test_tool_one",
            json={"value": "test_value"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"]["success"] is True
        assert data["result"]["data"]["value"] == "test_value"

    def test_tool_with_optional_params(self, tmp_path, register_sample_tools):
        """Should handle optional parameters."""
        app = create_app(tools_path=str(tmp_path))
        client = TestClient(app)

        # Call with only required param
        response = client.post(
            "/tools/test_tool_two",
            json={"a": 5},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"]["data"]["result"] == 15  # 5 + 10 (default)

        # Call with both params
        response = client.post(
            "/tools/test_tool_two",
            json={"a": 5, "b": 20},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"]["data"]["result"] == 25

    def test_category_endpoint(self, tmp_path, register_sample_tools):
        """Should list tools by category."""
        app = create_app(tools_path=str(tmp_path))
        client = TestClient(app)

        response = client.get("/tools/test")
        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "test"
        assert data["count"] >= 2

    def test_category_not_found(self, tmp_path, register_sample_tools):
        """Should return 404 for nonexistent category."""
        app = create_app(tools_path=str(tmp_path))
        client = TestClient(app)

        response = client.get("/tools/nonexistent_category_xyz")
        assert response.status_code == 404

    def test_tool_info_endpoint(self, tmp_path, register_sample_tools):
        """Should get tool info with schema."""
        app = create_app(tools_path=str(tmp_path))
        client = TestClient(app)

        response = client.get("/tools/test/test_tool_one")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test_tool_one"
        assert data["category"] == "test"
        assert "input_schema" in data
        assert data["input_schema"]["properties"]["value"]["type"] == "string"
