import pytest

from src.tools.local.shell import (
    run_shell_command,
    shell_check_command_exists,
    shell_get_current_directory,
    shell_get_environment_variable,
    shell_get_system_info,
    shell_run_shell_script,
)


class TestRunShellCommand:
    @pytest.mark.asyncio
    async def test_run_echo(self):
        result = await run_shell_command(args=["echo", "hello"])
        assert result["success"] is True
        assert "hello" in result["data"]["stdout"]

    @pytest.mark.asyncio
    async def test_run_with_base_dir(self, tmp_path):
        result = await run_shell_command(args=["pwd"], base_dir=str(tmp_path))
        assert result["success"] is True
        assert str(tmp_path) in result["data"]["stdout"]

    @pytest.mark.asyncio
    async def test_run_empty_args(self):
        result = await run_shell_command(args=[])
        assert result["success"] is False
        assert "empty" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_run_nonexistent_command(self):
        result = await run_shell_command(args=["nonexistent_command_xyz"])
        assert result["success"] is False
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_run_invalid_base_dir(self):
        result = await run_shell_command(
            args=["echo", "test"], base_dir="/nonexistent/path"
        )
        assert result["success"] is False
        assert "does not exist" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_run_with_tail(self):
        result = await run_shell_command(args=["echo", "line1\nline2\nline3"], tail=2)
        assert result["success"] is True


class TestRunShellScript:
    @pytest.mark.asyncio
    async def test_run_simple_script(self):
        result = await shell_run_shell_script(script="echo 'hello world'")
        assert result["success"] is True
        assert "hello world" in result["data"]["stdout"]

    @pytest.mark.asyncio
    async def test_run_multiline_script(self):
        script = """
        VAR="test"
        echo $VAR
        """
        result = await shell_run_shell_script(script=script)
        assert result["success"] is True
        assert "test" in result["data"]["stdout"]

    @pytest.mark.asyncio
    async def test_run_empty_script(self):
        result = await shell_run_shell_script(script="")
        assert result["success"] is False
        assert "empty" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_run_script_with_base_dir(self, tmp_path):
        result = await shell_run_shell_script(script="pwd", base_dir=str(tmp_path))
        assert result["success"] is True
        assert str(tmp_path) in result["data"]["stdout"]


class TestCheckCommandExists:
    @pytest.mark.asyncio
    async def test_command_exists(self):
        result = await shell_check_command_exists("echo")
        assert result["success"] is True
        assert result["data"]["exists"] is True
        assert result["data"]["path"] is not None

    @pytest.mark.asyncio
    async def test_command_not_exists(self):
        result = await shell_check_command_exists("nonexistent_command_xyz")
        assert result["success"] is True
        assert result["data"]["exists"] is False
        assert result["data"]["path"] is None


class TestGetEnvironmentVariable:
    @pytest.mark.asyncio
    async def test_get_existing_var(self):
        result = await shell_get_environment_variable("PATH")
        assert result["success"] is True
        assert result["data"]["is_set"] is True
        assert result["data"]["value"] is not None

    @pytest.mark.asyncio
    async def test_get_nonexistent_var(self):
        result = await shell_get_environment_variable("NONEXISTENT_VAR_XYZ_123")
        assert result["success"] is True
        assert result["data"]["is_set"] is False
        assert result["data"]["value"] is None


class TestGetCurrentDirectory:
    @pytest.mark.asyncio
    async def test_get_current_directory(self):
        result = await shell_get_current_directory()
        assert result["success"] is True
        assert "current_directory" in result["data"]
        assert len(result["data"]["current_directory"]) > 0


class TestGetSystemInfo:
    @pytest.mark.asyncio
    async def test_get_system_info(self):
        result = await shell_get_system_info()
        assert result["success"] is True
        assert "os" in result["data"]
        assert "platform" in result["data"]
        assert "python_version" in result["data"]
        assert "architecture" in result["data"]
