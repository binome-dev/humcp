"""Tool configuration loader with include/exclude filtering."""

import fnmatch
import logging
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, model_validator

from src.humcp.decorator import RegisteredTool

logger = logging.getLogger("humcp.config")

# Default config path
DEFAULT_CONFIG_PATH = Path("config/tools.yaml")


class FilterConfig(BaseModel):
    """Configuration for include or exclude filters."""

    categories: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)

    def is_empty(self) -> bool:
        """Check if filter has no entries."""
        return not self.categories and not self.tools


class ToolsConfig(BaseModel):
    """Configuration for tool filtering."""

    include: FilterConfig = Field(default_factory=FilterConfig)
    exclude: FilterConfig = Field(default_factory=FilterConfig)

    @model_validator(mode="before")
    @classmethod
    def handle_none_values(cls, data: dict) -> dict:
        """Handle None values in config (e.g., empty YAML sections)."""
        if not isinstance(data, dict):
            return data
        if data.get("include") is None:
            data["include"] = {}
        if data.get("exclude") is None:
            data["exclude"] = {}
        # Handle None in nested dicts
        for key in ["include", "exclude"]:
            if isinstance(data.get(key), dict):
                if data[key].get("categories") is None:
                    data[key]["categories"] = []
                if data[key].get("tools") is None:
                    data[key]["tools"] = []
        return data


class ConfigValidationResult(BaseModel):
    """Result of config validation."""

    valid: bool
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


def load_config(config_path: Path | None = None) -> ToolsConfig:
    """Load tool configuration from YAML file.

    Args:
        config_path: Path to config file. If None, uses default path.

    Returns:
        ToolsConfig object. Returns default (load all) if file doesn't exist.
    """
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH

    if not config_path.exists():
        logger.debug("Config file not found at %s, loading all tools", config_path)
        return ToolsConfig()

    try:
        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if data is None:
            # Empty YAML file
            return ToolsConfig()

        config = ToolsConfig.model_validate(data)
        logger.info("Loaded tool config from %s", config_path)
        return config

    except yaml.YAMLError as e:
        logger.error("Failed to parse YAML config at %s: %s", config_path, e)
        raise ValueError(f"Invalid YAML in config file: {e}") from e
    except Exception as e:
        logger.error("Failed to load config from %s: %s", config_path, e)
        raise


def validate_config(
    config: ToolsConfig,
    available_categories: set[str],
    available_tools: set[str],
) -> ConfigValidationResult:
    """Validate config against available categories and tools.

    Args:
        config: The config to validate.
        available_categories: Set of valid category names.
        available_tools: Set of valid tool names.

    Returns:
        ConfigValidationResult with warnings and errors.
    """
    warnings: list[str] = []
    errors: list[str] = []

    # Validate categories (exact match required)
    for section_name, section in [
        ("include", config.include),
        ("exclude", config.exclude),
    ]:
        for category in section.categories:
            if category not in available_categories:
                errors.append(
                    f"{section_name}.categories: Unknown category '{category}'. "
                    f"Available: {sorted(available_categories)}"
                )

    # Validate tools (support wildcards)
    for section_name, section in [
        ("include", config.include),
        ("exclude", config.exclude),
    ]:
        for tool_pattern in section.tools:
            if _is_wildcard(tool_pattern):
                # Check if pattern matches at least one tool
                matches = [
                    t for t in available_tools if fnmatch.fnmatch(t, tool_pattern)
                ]
                if not matches:
                    warnings.append(
                        f"{section_name}.tools: Pattern '{tool_pattern}' matches no tools"
                    )
                else:
                    logger.debug(
                        "Pattern '%s' matches %d tools: %s",
                        tool_pattern,
                        len(matches),
                        matches,
                    )
            else:
                # Exact match required
                if tool_pattern not in available_tools:
                    errors.append(
                        f"{section_name}.tools: Unknown tool '{tool_pattern}'"
                    )

    return ConfigValidationResult(
        valid=len(errors) == 0,
        warnings=warnings,
        errors=errors,
    )


def filter_tools(
    config: ToolsConfig,
    tools: list[RegisteredTool],
    validate: bool = True,
) -> list[RegisteredTool]:
    """Filter tools based on config include/exclude rules.

    Args:
        config: The filtering configuration.
        tools: List of tools to filter.
        validate: Whether to validate config and raise on errors.

    Returns:
        Filtered list of ToolRegistration objects.

    Raises:
        ValueError: If validate=True and config has validation errors.
    """
    if not tools:
        return []

    # Validate config if requested
    if validate:
        available_categories = {reg.category for reg in tools}
        available_tools = {reg.tool.name for reg in tools}
        result = validate_config(config, available_categories, available_tools)

        for warning in result.warnings:
            logger.warning("Config warning: %s", warning)

        if not result.valid:
            error_msg = "Config validation failed:\n" + "\n".join(
                f"  - {e}" for e in result.errors
            )
            raise ValueError(error_msg)

    # Step 1: Apply include filter
    if config.include.is_empty():
        # No include filter = include all
        filtered = tools
    else:
        filtered = [reg for reg in tools if _matches_filter(reg, config.include)]

    # Step 2: Apply exclude filter
    if not config.exclude.is_empty():
        filtered = [reg for reg in filtered if not _matches_filter(reg, config.exclude)]

    logger.info(
        "Filtered tools: %d/%d (include: %s, exclude: %s)",
        len(filtered),
        len(tools),
        "all"
        if config.include.is_empty()
        else f"{len(config.include.categories)} categories, {len(config.include.tools)} tools",
        "none"
        if config.exclude.is_empty()
        else f"{len(config.exclude.categories)} categories, {len(config.exclude.tools)} tools",
    )

    return filtered


def _is_wildcard(pattern: str) -> bool:
    """Check if pattern contains wildcard characters."""
    return "*" in pattern or "?" in pattern or "[" in pattern


def _matches_filter(reg: RegisteredTool, filter_config: FilterConfig) -> bool:
    """Check if a tool matches the filter criteria.

    A tool matches if:
    - Its category is in the categories list, OR
    - Its name matches any pattern in the tools list (supports wildcards)
    """
    # Check category match
    if reg.category in filter_config.categories:
        return True

    # Check tool name match (with wildcard support)
    for pattern in filter_config.tools:
        if _is_wildcard(pattern):
            if fnmatch.fnmatch(reg.tool.name, pattern):
                return True
        elif reg.tool.name == pattern:
            return True

    return False


def get_filtered_tools(
    tools: list[RegisteredTool],
    config_path: Path | None = None,
) -> list[RegisteredTool]:
    """Convenience function to load config and filter tools in one step.

    Args:
        tools: List of tools to filter.
        config_path: Path to config file. If None, uses default path.

    Returns:
        Filtered list of ToolRegistration objects.
    """
    config = load_config(config_path)
    return filter_tools(config, tools)
