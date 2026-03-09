"""Skill loader for discovering and parsing SKILL.md files."""

import logging
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger("humcp.skills")


@dataclass
class Skill:
    """Represents a skill loaded from a SKILL.md file."""

    name: str
    description: str
    content: str
    category: str


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Parse YAML frontmatter from markdown text.

    Args:
        text: Full markdown text with optional YAML frontmatter.

    Returns:
        Tuple of (frontmatter dict, remaining content).
    """
    # Match YAML frontmatter: starts with ---, ends with ---
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)
    if not match:
        return {}, text

    frontmatter_text = match.group(1)
    content = match.group(2).strip()

    # Simple YAML parsing (key: value pairs)
    frontmatter: dict[str, str] = {}
    for line in frontmatter_text.split("\n"):
        line = line.strip()
        if ":" in line:
            key, value = line.split(":", 1)
            frontmatter[key.strip()] = value.strip()

    return frontmatter, content


@lru_cache(maxsize=100)
def discover_skills(tools_path: Path) -> dict[str, Skill]:
    """Discover all SKILL.md files in tool directories.

    Results are cached to avoid repeated filesystem scans.

    Args:
        tools_path: Path to the tools directory.

    Returns:
        Dictionary mapping category name to Skill object.
    """
    skills: dict[str, Skill] = {}

    if not tools_path.exists():
        logger.warning("Tools path does not exist: %s", tools_path)
        return skills

    # Find all SKILL.md files
    for skill_file in tools_path.rglob("SKILL.md"):
        try:
            text = skill_file.read_text(encoding="utf-8")
            frontmatter, content = _parse_frontmatter(text)

            # Get category from parent directory name
            category = skill_file.parent.name

            # Extract metadata from frontmatter
            name = frontmatter.get("name", category)
            description = frontmatter.get("description", "")

            skill = Skill(
                name=name,
                description=description,
                content=content,
                category=category,
            )
            skills[category] = skill
            logger.debug("Loaded skill '%s' from %s", name, skill_file)

        except Exception as e:
            logger.warning("Failed to load skill from %s: %s", skill_file, e)

    logger.info("Discovered %d skills", len(skills))
    return skills


def get_skills_by_category(tools_path: Path) -> dict[str, dict[str, str]]:
    """Get skills metadata grouped by category.

    Args:
        tools_path: Path to the tools directory.

    Returns:
        Dictionary mapping category to skill metadata (name, description).
    """
    skills = discover_skills(tools_path)
    return {
        category: {
            "name": skill.name,
            "description": skill.description,
        }
        for category, skill in skills.items()
    }


def get_skill_content(tools_path: Path, category: str) -> str | None:
    """Get skill content for a specific category.

    Args:
        tools_path: Path to the tools directory.
        category: Category name to get skill content for.

    Returns:
        Skill content as string, or None if not found.
    """
    skills = discover_skills(tools_path)
    skill = skills.get(category)
    return skill.content if skill else None
