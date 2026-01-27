"""Tests for humcp config loader."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from src.humcp.config import (
    ConfigValidationResult,
    FilterConfig,
    ToolsConfig,
    _is_wildcard,
    _matches_filter,
    filter_tools,
    load_config,
    validate_config,
)
from src.humcp.decorator import RegisteredTool


def make_registered_tool(name: str, category: str) -> RegisteredTool:
    """Create a mock RegisteredTool for testing."""
    mock_tool = Mock()
    mock_tool.name = name
    mock_tool.description = f"Description for {name}"
    mock_tool.parameters = {"type": "object", "properties": {}}
    mock_tool.fn = lambda: None
    return RegisteredTool(tool=mock_tool, category=category)


# Test fixtures
@pytest.fixture
def sample_tools() -> list[RegisteredTool]:
    """Create sample tools for testing."""
    return [
        make_registered_tool("calculator_add", "local"),
        make_registered_tool("calculator_subtract", "local"),
        make_registered_tool("shell_run_script", "local"),
        make_registered_tool("read_csv", "data"),
        make_registered_tool("google_sheets_read", "google"),
    ]


class TestFilterConfig:
    """Tests for FilterConfig model."""

    def test_empty_filter(self):
        """Empty filter should report is_empty True."""
        config = FilterConfig()
        assert config.is_empty()

    def test_filter_with_categories(self):
        """Filter with categories should not be empty."""
        config = FilterConfig(categories=["local"])
        assert not config.is_empty()

    def test_filter_with_tools(self):
        """Filter with tools should not be empty."""
        config = FilterConfig(tools=["calculator_add"])
        assert not config.is_empty()


class TestToolsConfig:
    """Tests for ToolsConfig model."""

    def test_default_config(self):
        """Default config should have empty filters."""
        config = ToolsConfig()
        assert config.include.is_empty()
        assert config.exclude.is_empty()

    def test_config_with_include(self):
        """Config with include should parse correctly."""
        config = ToolsConfig(
            include=FilterConfig(categories=["local", "data"]),
        )
        assert config.include.categories == ["local", "data"]
        assert config.exclude.is_empty()

    def test_config_handles_none_values(self):
        """Config should handle None values from YAML."""
        data = {
            "include": None,
            "exclude": {"categories": None, "tools": ["test"]},
        }
        config = ToolsConfig.model_validate(data)
        assert config.include.is_empty()
        assert config.exclude.tools == ["test"]


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_nonexistent_file(self, tmp_path: Path):
        """Should return default config for missing file."""
        config = load_config(tmp_path / "nonexistent.yaml")
        assert config.include.is_empty()
        assert config.exclude.is_empty()

    def test_load_empty_file(self, tmp_path: Path):
        """Should return default config for empty file."""
        config_file = tmp_path / "empty.yaml"
        config_file.write_text("")
        config = load_config(config_file)
        assert config.include.is_empty()
        assert config.exclude.is_empty()

    def test_load_include_categories(self, tmp_path: Path):
        """Should load include categories from YAML."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
include:
  categories:
    - local
    - data
""")
        config = load_config(config_file)
        assert config.include.categories == ["local", "data"]

    def test_load_exclude_tools(self, tmp_path: Path):
        """Should load exclude tools from YAML."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
exclude:
  tools:
    - shell_*
    - dangerous_tool
""")
        config = load_config(config_file)
        assert config.exclude.tools == ["shell_*", "dangerous_tool"]

    def test_load_complex_config(self, tmp_path: Path):
        """Should load complex config with both include and exclude."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
include:
  categories:
    - local
  tools:
    - read_csv
exclude:
  tools:
    - shell_*
""")
        config = load_config(config_file)
        assert config.include.categories == ["local"]
        assert config.include.tools == ["read_csv"]
        assert config.exclude.tools == ["shell_*"]

    def test_load_invalid_yaml(self, tmp_path: Path):
        """Should raise error for invalid YAML."""
        config_file = tmp_path / "invalid.yaml"
        config_file.write_text("{ invalid yaml [")
        with pytest.raises(ValueError, match="Invalid YAML"):
            load_config(config_file)


class TestValidateConfig:
    """Tests for validate_config function."""

    def test_valid_config(self, sample_tools: list[RegisteredTool]):
        """Valid config should pass validation."""
        config = ToolsConfig(
            include=FilterConfig(categories=["local"]),
        )
        available_categories = {t.category for t in sample_tools}
        available_tools = {t.tool.name for t in sample_tools}

        result = validate_config(config, available_categories, available_tools)
        assert result.valid
        assert not result.errors
        assert not result.warnings

    def test_invalid_category(self, sample_tools: list[RegisteredTool]):
        """Unknown category should cause validation error."""
        config = ToolsConfig(
            include=FilterConfig(categories=["nonexistent"]),
        )
        available_categories = {t.category for t in sample_tools}
        available_tools = {t.tool.name for t in sample_tools}

        result = validate_config(config, available_categories, available_tools)
        assert not result.valid
        assert any("nonexistent" in e for e in result.errors)

    def test_invalid_tool(self, sample_tools: list[RegisteredTool]):
        """Unknown tool should cause validation error."""
        config = ToolsConfig(
            include=FilterConfig(tools=["nonexistent_tool"]),
        )
        available_categories = {t.category for t in sample_tools}
        available_tools = {t.tool.name for t in sample_tools}

        result = validate_config(config, available_categories, available_tools)
        assert not result.valid
        assert any("nonexistent_tool" in e for e in result.errors)

    def test_wildcard_no_match_warning(self, sample_tools: list[RegisteredTool]):
        """Wildcard matching no tools should cause warning."""
        config = ToolsConfig(
            exclude=FilterConfig(tools=["xyz_*"]),
        )
        available_categories = {t.category for t in sample_tools}
        available_tools = {t.tool.name for t in sample_tools}

        result = validate_config(config, available_categories, available_tools)
        assert result.valid  # Still valid, just warning
        assert any("xyz_*" in w for w in result.warnings)

    def test_wildcard_with_matches(self, sample_tools: list[RegisteredTool]):
        """Wildcard matching tools should pass validation."""
        config = ToolsConfig(
            exclude=FilterConfig(tools=["calculator_*"]),
        )
        available_categories = {t.category for t in sample_tools}
        available_tools = {t.tool.name for t in sample_tools}

        result = validate_config(config, available_categories, available_tools)
        assert result.valid
        assert not result.warnings


class TestIsWildcard:
    """Tests for _is_wildcard function."""

    def test_asterisk(self):
        assert _is_wildcard("shell_*")

    def test_question_mark(self):
        assert _is_wildcard("tool_?")

    def test_bracket(self):
        assert _is_wildcard("tool_[abc]")

    def test_no_wildcard(self):
        assert not _is_wildcard("calculator_add")


class TestMatchesFilter:
    """Tests for _matches_filter function."""

    def test_match_by_category(self):
        """Tool should match if category is in filter."""
        reg = make_registered_tool("test", "local")
        filter_config = FilterConfig(categories=["local"])
        assert _matches_filter(reg, filter_config)

    def test_no_match_by_category(self):
        """Tool should not match if category not in filter."""
        reg = make_registered_tool("test", "data")
        filter_config = FilterConfig(categories=["local"])
        assert not _matches_filter(reg, filter_config)

    def test_match_by_exact_tool_name(self):
        """Tool should match by exact name."""
        reg = make_registered_tool("calculator_add", "local")
        filter_config = FilterConfig(tools=["calculator_add"])
        assert _matches_filter(reg, filter_config)

    def test_match_by_wildcard(self):
        """Tool should match by wildcard pattern."""
        reg = make_registered_tool("calculator_add", "local")
        filter_config = FilterConfig(tools=["calculator_*"])
        assert _matches_filter(reg, filter_config)

    def test_no_match_by_wildcard(self):
        """Tool should not match if wildcard doesn't match."""
        reg = make_registered_tool("shell_run", "local")
        filter_config = FilterConfig(tools=["calculator_*"])
        assert not _matches_filter(reg, filter_config)


class TestFilterTools:
    """Tests for filter_tools function."""

    def test_empty_config_returns_all(self, sample_tools: list[RegisteredTool]):
        """Empty config should return all tools."""
        config = ToolsConfig()
        result = filter_tools(config, sample_tools, validate=False)
        assert len(result) == len(sample_tools)

    def test_include_category(self, sample_tools: list[RegisteredTool]):
        """Include category should filter to that category."""
        config = ToolsConfig(
            include=FilterConfig(categories=["local"]),
        )
        result = filter_tools(config, sample_tools, validate=False)
        assert len(result) == 3  # calculator_add, calculator_subtract, shell_run_script
        assert all(r.category == "local" for r in result)

    def test_include_multiple_categories(self, sample_tools: list[RegisteredTool]):
        """Include multiple categories should filter to those categories."""
        config = ToolsConfig(
            include=FilterConfig(categories=["local", "data"]),
        )
        result = filter_tools(config, sample_tools, validate=False)
        assert len(result) == 4
        assert all(r.category in ["local", "data"] for r in result)

    def test_include_specific_tools(self, sample_tools: list[RegisteredTool]):
        """Include specific tools should filter to those tools."""
        config = ToolsConfig(
            include=FilterConfig(tools=["calculator_add", "read_csv"]),
        )
        result = filter_tools(config, sample_tools, validate=False)
        assert len(result) == 2
        assert {r.tool.name for r in result} == {"calculator_add", "read_csv"}

    def test_exclude_category(self, sample_tools: list[RegisteredTool]):
        """Exclude category should remove that category."""
        config = ToolsConfig(
            exclude=FilterConfig(categories=["google"]),
        )
        result = filter_tools(config, sample_tools, validate=False)
        assert len(result) == 4
        assert all(r.category != "google" for r in result)

    def test_exclude_tools_wildcard(self, sample_tools: list[RegisteredTool]):
        """Exclude with wildcard should remove matching tools."""
        config = ToolsConfig(
            exclude=FilterConfig(tools=["calculator_*"]),
        )
        result = filter_tools(config, sample_tools, validate=False)
        assert len(result) == 3
        assert all(not r.tool.name.startswith("calculator_") for r in result)

    def test_include_and_exclude(self, sample_tools: list[RegisteredTool]):
        """Include and exclude should work together."""
        config = ToolsConfig(
            include=FilterConfig(categories=["local"]),
            exclude=FilterConfig(tools=["shell_*"]),
        )
        result = filter_tools(config, sample_tools, validate=False)
        assert len(result) == 2  # calculator_add, calculator_subtract
        assert all(r.category == "local" for r in result)
        assert all(not r.tool.name.startswith("shell_") for r in result)

    def test_include_category_and_tool(self, sample_tools: list[RegisteredTool]):
        """Include category OR tool should work (union)."""
        config = ToolsConfig(
            include=FilterConfig(categories=["local"], tools=["read_csv"]),
        )
        result = filter_tools(config, sample_tools, validate=False)
        assert len(result) == 4  # 3 local + read_csv

    def test_validation_error_raises(self, sample_tools: list[RegisteredTool]):
        """Validation errors should raise ValueError."""
        config = ToolsConfig(
            include=FilterConfig(categories=["nonexistent"]),
        )
        with pytest.raises(ValueError, match="Config validation failed"):
            filter_tools(config, sample_tools, validate=True)

    def test_empty_tools_list(self):
        """Should handle empty tools list."""
        config = ToolsConfig()
        result = filter_tools(config, [], validate=False)
        assert result == []


class TestConfigValidationResult:
    """Tests for ConfigValidationResult model."""

    def test_valid_result(self):
        result = ConfigValidationResult(valid=True)
        assert result.valid
        assert result.warnings == []
        assert result.errors == []

    def test_invalid_result_with_errors(self):
        result = ConfigValidationResult(
            valid=False,
            errors=["Error 1", "Error 2"],
        )
        assert not result.valid
        assert len(result.errors) == 2

    def test_valid_result_with_warnings(self):
        result = ConfigValidationResult(
            valid=True,
            warnings=["Warning 1"],
        )
        assert result.valid
        assert len(result.warnings) == 1
