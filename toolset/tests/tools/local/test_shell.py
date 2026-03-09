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
        assert result.success is True
        assert "hello" in result.data.stdout

    @pytest.mark.asyncio
    async def test_run_with_base_dir(self, tmp_path):
        result = await run_shell_command(args=["pwd"], base_dir=str(tmp_path))
        assert result.success is True
        assert str(tmp_path) in result.data.stdout

    @pytest.mark.asyncio
    async def test_run_empty_args(self):
        result = await run_shell_command(args=[])
        assert result.success is False
        assert "empty" in result.error.lower()

    @pytest.mark.asyncio
    async def test_run_nonexistent_command(self):
        result = await run_shell_command(args=["nonexistent_command_xyz"])
        assert result.success is False
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_run_invalid_base_dir(self):
        result = await run_shell_command(
            args=["echo", "test"], base_dir="/nonexistent/path"
        )
        assert result.success is False
        assert "does not exist" in result.error.lower()

    @pytest.mark.asyncio
    async def test_run_with_tail(self):
        result = await run_shell_command(args=["echo", "line1\nline2\nline3"], tail=2)
        assert result.success is True


class TestRunShellScript:
    @pytest.mark.asyncio
    async def test_run_simple_script(self):
        result = await shell_run_shell_script(script="echo 'hello world'")
        assert result.success is True
        assert "hello world" in result.data.stdout

    @pytest.mark.asyncio
    async def test_run_multiline_script(self):
        script = """
        VAR="test"
        echo $VAR
        """
        result = await shell_run_shell_script(script=script)
        assert result.success is True
        assert "test" in result.data.stdout

    @pytest.mark.asyncio
    async def test_run_empty_script(self):
        result = await shell_run_shell_script(script="")
        assert result.success is False
        assert "empty" in result.error.lower()

    @pytest.mark.asyncio
    async def test_run_script_with_base_dir(self, tmp_path):
        result = await shell_run_shell_script(script="pwd", base_dir=str(tmp_path))
        assert result.success is True
        assert str(tmp_path) in result.data.stdout


class TestCheckCommandExists:
    @pytest.mark.asyncio
    async def test_command_exists(self):
        result = await shell_check_command_exists("echo")
        assert result.success is True
        assert result.data.exists is True
        assert result.data.path is not None

    @pytest.mark.asyncio
    async def test_command_not_exists(self):
        result = await shell_check_command_exists("nonexistent_command_xyz")
        assert result.success is True
        assert result.data.exists is False
        assert result.data.path is None


class TestGetEnvironmentVariable:
    @pytest.mark.asyncio
    async def test_get_existing_var(self):
        result = await shell_get_environment_variable("PATH")
        assert result.success is True
        assert result.data.is_set is True
        assert result.data.value is not None

    @pytest.mark.asyncio
    async def test_get_allowlisted_var_home(self):
        result = await shell_get_environment_variable("HOME")
        assert result.success is True
        # HOME might or might not be set depending on environment
        assert result.data.is_set is not None

    @pytest.mark.asyncio
    async def test_get_blocked_var(self):
        """Test that access to non-allowlisted variables is blocked."""
        result = await shell_get_environment_variable("NONEXISTENT_VAR_XYZ_123")
        assert result.success is False
        assert "not allowed" in result.error

    @pytest.mark.asyncio
    async def test_get_sensitive_var_blocked(self):
        """Test that access to potentially sensitive variables is blocked."""
        # API keys and secrets should not be accessible
        for var in ["API_KEY", "SECRET_KEY", "DATABASE_URL", "AWS_SECRET_ACCESS_KEY"]:
            result = await shell_get_environment_variable(var)
            assert result.success is False
            assert "not allowed" in result.error


class TestGetCurrentDirectory:
    @pytest.mark.asyncio
    async def test_get_current_directory(self):
        result = await shell_get_current_directory()
        assert result.success is True
        assert result.data.current_directory is not None
        assert len(result.data.current_directory) > 0


class TestGetSystemInfo:
    @pytest.mark.asyncio
    async def test_get_system_info(self):
        result = await shell_get_system_info()
        assert result.success is True
        assert result.data.os is not None
        assert result.data.platform is not None
        assert result.data.python_version is not None
        assert result.data.architecture is not None
