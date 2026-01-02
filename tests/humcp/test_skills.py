"""Tests for humcp skill loader."""

from pathlib import Path

import pytest

from src.humcp.skills import (
    Skill,
    _parse_frontmatter,
    discover_skills,
    get_skill_content,
    get_skills_by_category,
)


class TestParseFrontmatter:
    """Tests for YAML frontmatter parsing."""

    def test_parse_valid_frontmatter(self):
        """Should parse valid YAML frontmatter."""
        text = """---
name: test-skill
description: A test skill
---

# Test Content

This is the content."""
        frontmatter, content = _parse_frontmatter(text)
        assert frontmatter["name"] == "test-skill"
        assert frontmatter["description"] == "A test skill"
        assert "# Test Content" in content

    def test_parse_empty_frontmatter(self):
        """Should handle empty frontmatter."""
        text = """---
---

# Content"""
        frontmatter, content = _parse_frontmatter(text)
        assert frontmatter == {}
        assert "# Content" in content

    def test_parse_no_frontmatter(self):
        """Should handle text without frontmatter."""
        text = """# Just Content

No frontmatter here."""
        frontmatter, content = _parse_frontmatter(text)
        assert frontmatter == {}
        assert content == text

    def test_parse_multiline_description(self):
        """Should handle multi-value frontmatter."""
        text = """---
name: multi-skill
category: test
version: 1.0
---

Content here."""
        frontmatter, content = _parse_frontmatter(text)
        assert frontmatter["name"] == "multi-skill"
        assert frontmatter["category"] == "test"
        assert frontmatter["version"] == "1.0"


class TestDiscoverSkills:
    """Tests for skill discovery."""

    def test_discover_skills_from_tools_path(self, tmp_path: Path):
        """Should discover SKILL.md files in tool directories."""
        # Create test structure
        tool_dir = tmp_path / "test_tool"
        tool_dir.mkdir()
        skill_file = tool_dir / "SKILL.md"
        skill_file.write_text("""---
name: test-tool-skill
description: A tool for testing
---

# Test Tool

Documentation here.""")

        skills = discover_skills(tmp_path)
        assert "test_tool" in skills
        skill = skills["test_tool"]
        assert skill.name == "test-tool-skill"
        assert skill.description == "A tool for testing"
        assert skill.category == "test_tool"
        assert "# Test Tool" in skill.content

    def test_discover_multiple_skills(self, tmp_path: Path):
        """Should discover multiple SKILL.md files."""
        # Create first tool
        tool1 = tmp_path / "tool_one"
        tool1.mkdir()
        (tool1 / "SKILL.md").write_text("""---
name: skill-one
description: First skill
---
Content one.""")

        # Create second tool
        tool2 = tmp_path / "tool_two"
        tool2.mkdir()
        (tool2 / "SKILL.md").write_text("""---
name: skill-two
description: Second skill
---
Content two.""")

        skills = discover_skills(tmp_path)
        assert len(skills) == 2
        assert "tool_one" in skills
        assert "tool_two" in skills

    def test_discover_nested_skills(self, tmp_path: Path):
        """Should discover SKILL.md in nested directories."""
        nested = tmp_path / "category" / "nested_tool"
        nested.mkdir(parents=True)
        (nested / "SKILL.md").write_text("""---
name: nested-skill
description: Nested skill
---
Nested content.""")

        skills = discover_skills(tmp_path)
        assert "nested_tool" in skills
        assert skills["nested_tool"].name == "nested-skill"

    def test_discover_nonexistent_path(self, tmp_path: Path):
        """Should return empty dict for nonexistent path."""
        nonexistent = tmp_path / "nonexistent"
        skills = discover_skills(nonexistent)
        assert skills == {}

    def test_discover_empty_directory(self, tmp_path: Path):
        """Should return empty dict for directory without SKILL.md files."""
        skills = discover_skills(tmp_path)
        assert skills == {}

    def test_discover_skill_without_frontmatter(self, tmp_path: Path):
        """Should use defaults when frontmatter is missing."""
        tool_dir = tmp_path / "no_frontmatter"
        tool_dir.mkdir()
        (tool_dir / "SKILL.md").write_text("""# No Frontmatter

Just content here.""")

        skills = discover_skills(tmp_path)
        assert "no_frontmatter" in skills
        skill = skills["no_frontmatter"]
        assert skill.name == "no_frontmatter"  # Falls back to category
        assert skill.description == ""


class TestGetSkillsByCategory:
    """Tests for get_skills_by_category."""

    def test_get_skills_metadata(self, tmp_path: Path):
        """Should return skills metadata grouped by category."""
        tool_dir = tmp_path / "test_cat"
        tool_dir.mkdir()
        (tool_dir / "SKILL.md").write_text("""---
name: metadata-skill
description: Skill with metadata
---
Content.""")

        result = get_skills_by_category(tmp_path)
        assert "test_cat" in result
        assert result["test_cat"]["name"] == "metadata-skill"
        assert result["test_cat"]["description"] == "Skill with metadata"
        # Should not include content in metadata
        assert "content" not in result["test_cat"]


class TestGetSkillContent:
    """Tests for get_skill_content."""

    def test_get_content_for_existing_category(self, tmp_path: Path):
        """Should return content for existing category."""
        tool_dir = tmp_path / "content_cat"
        tool_dir.mkdir()
        (tool_dir / "SKILL.md").write_text("""---
name: content-skill
description: Has content
---

# Content Section

Details here.""")

        content = get_skill_content(tmp_path, "content_cat")
        assert content is not None
        assert "# Content Section" in content
        assert "Details here." in content

    def test_get_content_for_nonexistent_category(self, tmp_path: Path):
        """Should return None for nonexistent category."""
        content = get_skill_content(tmp_path, "nonexistent")
        assert content is None


class TestSkillDataclass:
    """Tests for Skill dataclass."""

    def test_skill_creation(self):
        """Should create Skill with all fields."""
        skill = Skill(
            name="test",
            description="A test skill",
            content="# Content",
            category="test_cat",
        )
        assert skill.name == "test"
        assert skill.description == "A test skill"
        assert skill.content == "# Content"
        assert skill.category == "test_cat"

    def test_skill_equality(self):
        """Skills with same values should be equal."""
        skill1 = Skill("a", "b", "c", "d")
        skill2 = Skill("a", "b", "c", "d")
        assert skill1 == skill2


class TestRealSkills:
    """Tests for actual SKILL.md files in the codebase."""

    @pytest.fixture
    def tools_path(self) -> Path:
        """Get path to actual tools directory."""
        return Path(__file__).parent.parent.parent / "src" / "tools"

    def test_discover_real_skills(self, tools_path: Path):
        """Should discover SKILL.md files from actual tools directory."""
        if not tools_path.exists():
            pytest.skip("Tools directory not found")

        skills = discover_skills(tools_path)
        # We expect at least some skills to be found
        assert len(skills) > 0

    def test_real_skills_have_required_fields(self, tools_path: Path):
        """Real skills should have name and description."""
        if not tools_path.exists():
            pytest.skip("Tools directory not found")

        skills = discover_skills(tools_path)
        for category, skill in skills.items():
            assert skill.name, f"Skill in {category} missing name"
            assert skill.description, f"Skill in {category} missing description"
