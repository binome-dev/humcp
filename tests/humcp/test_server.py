"""Tests for humcp server module."""

import tempfile
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.humcp.server import _load_modules, create_app


class TestLoadModules:
    """Tests for the _load_modules function."""

    def test_returns_empty_for_nonexistent_path(self):
        """Should return empty list when path doesn't exist."""
        result = _load_modules(Path("/nonexistent/path"))
        assert result == []

    def test_skips_underscore_files(self, tmp_path):
        """Should skip files starting with underscore."""
        (tmp_path / "_init.py").write_text("# init")
        result = _load_modules(tmp_path)
        assert result == []

    def test_loads_valid_module(self, tmp_path):
        """Should load valid Python modules."""
        (tmp_path / "tool.py").write_text("x = 1")
        result = _load_modules(tmp_path)
        assert len(result) == 1

    def test_handles_import_errors(self, tmp_path):
        """Should handle import errors gracefully."""
        (tmp_path / "broken.py").write_text("import nonexistent_xyz")
        result = _load_modules(tmp_path)
        assert result == []

    def test_recursive_loading(self, tmp_path):
        """Should load from subdirectories."""
        subdir = tmp_path / "sub"
        subdir.mkdir()
        (tmp_path / "a.py").write_text("x = 1")
        (subdir / "b.py").write_text("y = 2")
        result = _load_modules(tmp_path)
        assert len(result) == 2


class TestCreateApp:
    """Tests for the create_app function."""

    def test_returns_fastapi(self):
        """Should return a FastAPI instance."""
        with tempfile.TemporaryDirectory() as tmp:
            app = create_app(tools_path=tmp)
            assert isinstance(app, FastAPI)

    def test_custom_title(self):
        """Should use custom title."""
        with tempfile.TemporaryDirectory() as tmp:
            app = create_app(tools_path=tmp, title="Custom")
            assert app.title == "Custom"

    def test_root_endpoint(self):
        """Should have root info endpoint."""
        with tempfile.TemporaryDirectory() as tmp:
            app = create_app(tools_path=tmp)
            client = TestClient(app)
            resp = client.get("/")
            assert resp.status_code == 200
            data = resp.json()
            assert "name" in data
            assert "mcp_server" in data
            assert "tools_count" in data

    def test_tools_endpoint(self):
        """Should have /tools endpoint."""
        with tempfile.TemporaryDirectory() as tmp:
            app = create_app(tools_path=tmp)
            client = TestClient(app)
            resp = client.get("/tools")
            assert resp.status_code == 200
            assert "total_tools" in resp.json()

    def test_mounts_mcp(self):
        """Should mount MCP at /mcp."""
        with tempfile.TemporaryDirectory() as tmp:
            app = create_app(tools_path=tmp)
            routes = [r.path for r in app.routes]
            assert "/mcp" in routes or any("/mcp" in str(r) for r in routes)

    def test_discovers_and_registers_tools(self, sample_tools):
        """Should discover and register tools."""
        app = create_app(tools_path=str(sample_tools))
        client = TestClient(app)
        resp = client.get("/tools")
        assert resp.json()["total_tools"] == 3

    def test_tool_execution(self, sample_tools):
        """Should execute tools via REST."""
        app = create_app(tools_path=str(sample_tools))
        client = TestClient(app)
        resp = client.post("/tools/test_tool_one", json={"value": "hello"})
        assert resp.status_code == 200
        assert resp.json()["result"]["data"]["value"] == "hello"

    def test_category_endpoint(self, sample_tools):
        """Should list tools by category."""
        app = create_app(tools_path=str(sample_tools))
        client = TestClient(app)
        resp = client.get("/tools/test")
        assert resp.status_code == 200
        assert resp.json()["count"] == 2
