"""Tests for MCP Apps discovery and delivery."""

import tempfile
from pathlib import Path

from fastapi.testclient import TestClient
from src.humcp.server import _discover_apps, create_app


class TestDiscoverApps:
    """Tests for the _discover_apps function."""

    def test_returns_empty_for_nonexistent_path(self):
        """Should return empty dict when path doesn't exist."""
        result = _discover_apps(Path("/nonexistent/path"))
        assert result == {}

    def test_discovers_html_files(self, tmp_path):
        """Should discover HTML files and map tool_name -> path."""
        category_dir = tmp_path / "calculator"
        category_dir.mkdir()
        html_file = category_dir / "add.html"
        html_file.write_text("<html>add app</html>")

        result = _discover_apps(tmp_path)
        assert "add" in result
        assert result["add"] == html_file

    def test_discovers_nested_apps(self, tmp_path):
        """Should discover apps in nested category directories."""
        (tmp_path / "calculator").mkdir()
        (tmp_path / "calculator" / "add.html").write_text("<html>add</html>")
        (tmp_path / "calculator" / "subtract.html").write_text("<html>sub</html>")
        (tmp_path / "search").mkdir()
        (tmp_path / "search" / "tavily.html").write_text("<html>search</html>")

        result = _discover_apps(tmp_path)
        assert len(result) == 3
        assert "add" in result
        assert "subtract" in result
        assert "tavily" in result

    def test_ignores_non_html_files(self, tmp_path):
        """Should only discover .html files."""
        (tmp_path / "readme.md").write_text("# readme")
        (tmp_path / "app.html").write_text("<html>app</html>")
        (tmp_path / "style.css").write_text("body {}")

        result = _discover_apps(tmp_path)
        assert len(result) == 1
        assert "app" in result

    def test_empty_directory(self, tmp_path):
        """Should return empty dict for empty directory."""
        result = _discover_apps(tmp_path)
        assert result == {}


class TestAppsRestEndpoints:
    """Tests for REST /apps endpoints."""

    def _create_app_with_apps(self, tools_dir, apps_dir, config_file):
        """Helper to create app with both tools and apps directories."""
        return create_app(
            tools_path=str(tools_dir),
            config_path=str(config_file),
            apps_path=str(apps_dir),
        )

    def test_list_apps_empty(self, empty_config):
        """Should return empty list when no apps exist."""
        with (
            tempfile.TemporaryDirectory() as tools,
            tempfile.TemporaryDirectory() as apps,
        ):
            app = self._create_app_with_apps(tools, apps, empty_config)
            client = TestClient(app)
            resp = client.get("/apps")
            assert resp.status_code == 200
            data = resp.json()
            assert data["total_apps"] == 0
            assert data["apps"] == []

    def test_list_apps_with_bundles(self, empty_config):
        """Should list discovered app bundles."""
        with (
            tempfile.TemporaryDirectory() as tools,
            tempfile.TemporaryDirectory() as apps,
        ):
            apps_path = Path(apps)
            calc_dir = apps_path / "calculator"
            calc_dir.mkdir()
            (calc_dir / "add.html").write_text("<html>add app</html>")

            app = self._create_app_with_apps(tools, apps, empty_config)
            client = TestClient(app)
            resp = client.get("/apps")
            assert resp.status_code == 200
            data = resp.json()
            assert data["total_apps"] == 1
            assert data["apps"][0]["tool_name"] == "add"
            assert data["apps"][0]["rest_endpoint"] == "/apps/add"
            assert "ui://" in data["apps"][0]["mcp_resource"]

    def test_get_app_html(self, empty_config):
        """Should serve HTML content for existing app."""
        with (
            tempfile.TemporaryDirectory() as tools,
            tempfile.TemporaryDirectory() as apps,
        ):
            apps_path = Path(apps)
            calc_dir = apps_path / "calculator"
            calc_dir.mkdir()
            html_content = "<html><body>Calculator Add App</body></html>"
            (calc_dir / "add.html").write_text(html_content)

            app = self._create_app_with_apps(tools, apps, empty_config)
            client = TestClient(app)
            resp = client.get("/apps/add")
            assert resp.status_code == 200
            assert resp.headers["content-type"].startswith("text/html")
            assert "Calculator Add App" in resp.text

    def test_get_app_html_not_found(self, empty_config):
        """Should return 404 for non-existent app."""
        with (
            tempfile.TemporaryDirectory() as tools,
            tempfile.TemporaryDirectory() as apps,
        ):
            app = self._create_app_with_apps(tools, apps, empty_config)
            client = TestClient(app)
            resp = client.get("/apps/nonexistent")
            assert resp.status_code == 404

    def test_root_includes_apps_count(self, empty_config):
        """Root endpoint should include apps_count."""
        with (
            tempfile.TemporaryDirectory() as tools,
            tempfile.TemporaryDirectory() as apps,
        ):
            apps_path = Path(apps)
            calc_dir = apps_path / "calculator"
            calc_dir.mkdir()
            (calc_dir / "add.html").write_text("<html>add</html>")

            app = self._create_app_with_apps(tools, apps, empty_config)
            client = TestClient(app)
            resp = client.get("/")
            assert resp.status_code == 200
            data = resp.json()
            assert data["apps_count"] == 1
            assert "apps" in data["endpoints"]


class TestAppToolBinding:
    """Tests for binding apps to tools via AppConfig."""

    def test_tool_with_matching_app_gets_app_config(self, empty_config):
        """Tool with matching HTML app should get AppConfig attached."""
        with tempfile.TemporaryDirectory() as tmp:
            tools_path = Path(tmp) / "tools"
            apps_path = Path(tmp) / "apps"
            tools_path.mkdir()
            apps_path.mkdir()

            # Create a tool
            test_dir = tools_path / "test"
            test_dir.mkdir()
            (test_dir / "my_tool.py").write_text('''
from src.humcp.decorator import tool

@tool(category="test")
async def my_tool(x: int) -> dict:
    """A test tool."""
    return {"success": True, "data": {"x": x}}
''')

            # Create matching app
            calc_dir = apps_path / "test"
            calc_dir.mkdir()
            (calc_dir / "my_tool.html").write_text("<html>my tool app</html>")

            app = create_app(
                tools_path=str(tools_path),
                config_path=str(empty_config),
                apps_path=str(apps_path),
            )

            # Verify tool is registered and app is served
            client = TestClient(app)
            resp = client.get("/apps/my_tool")
            assert resp.status_code == 200
            assert "my tool app" in resp.text

            # Verify tool still executes
            resp = client.post("/tools/my_tool", json={"x": 42})
            assert resp.status_code == 200

    def test_tool_without_matching_app(self, empty_config):
        """Tool without matching HTML app should still work normally."""
        with tempfile.TemporaryDirectory() as tmp:
            tools_path = Path(tmp) / "tools"
            apps_path = Path(tmp) / "apps"
            tools_path.mkdir()
            apps_path.mkdir()

            test_dir = tools_path / "test"
            test_dir.mkdir()
            (test_dir / "plain_tool.py").write_text('''
from src.humcp.decorator import tool

@tool(category="test")
async def plain_tool(val: str) -> dict:
    """A plain tool without app."""
    return {"success": True, "data": {"val": val}}
''')

            app = create_app(
                tools_path=str(tools_path),
                config_path=str(empty_config),
                apps_path=str(apps_path),
            )

            client = TestClient(app)
            resp = client.post("/tools/plain_tool", json={"val": "hello"})
            assert resp.status_code == 200
            assert resp.json()["result"]["data"]["val"] == "hello"
