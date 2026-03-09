"""Shell command execution tools.

Security Warning:
    These tools allow arbitrary shell command execution. They are intended for
    trusted internal use cases only. In production environments, consider:

    1. Restricting which commands can be executed via an allowlist
    2. Running the server in a sandboxed environment (container, VM)
    3. Using proper authentication and authorization
    4. Monitoring and logging all command executions

    The run_shell_command function is an internal helper and is not exposed
    as an MCP tool directly.
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from src.humcp.decorator import tool
from src.tools.local.schemas import (
    CommandExistsData,
    CommandExistsResponse,
    CurrentDirectoryData,
    CurrentDirectoryResponse,
    EnvironmentVariableData,
    EnvironmentVariableResponse,
    ShellCommandData,
    ShellCommandResponse,
    ShellScriptData,
    ShellScriptResponse,
    SystemInfoData,
    SystemInfoResponse,
)

logger = logging.getLogger("humcp.tools.shell")

# Shell execution defaults
DEFAULT_SHELL_TIMEOUT = 30  # seconds
DEFAULT_OUTPUT_TAIL_LINES = 100  # lines to return from output
MAX_SCRIPT_SIZE = 100_000  # 100KB max script size to prevent memory exhaustion

# Allowlist of permitted shell interpreters for security
# Prevents arbitrary executable paths from being used
ALLOWED_SHELLS = frozenset(
    {
        "/bin/bash",
        "/bin/sh",
        "/bin/zsh",
        "/usr/bin/bash",
        "/usr/bin/sh",
        "/usr/bin/zsh",
        "/usr/local/bin/bash",
        "/usr/local/bin/zsh",
        "bash",
        "sh",
        "zsh",
    }
)


async def run_shell_command(
    args: list[str],
    tail: int = DEFAULT_OUTPUT_TAIL_LINES,
    base_dir: str = "",
    timeout: int = DEFAULT_SHELL_TIMEOUT,
) -> ShellCommandResponse:
    """
    Run a shell command and return the output or error.

    Args:
        args: The command to run as a list of strings (e.g., ["ls", "-la"])
        tail: Number of lines to return from the output (None for all lines)
        base_dir: Working directory to run the command in (defaults to current directory)
        timeout: Maximum time in seconds to wait for command completion

    Returns:
        Command output, error, and return code

    Examples:
        - List files: {"args": ["ls", "-la"]}
        - Check Git status: {"args": ["git", "status"]}
        - Run Python script: {"args": ["python", "script.py"], "base_dir": "/path/to/project"}
    """
    try:
        if not args or len(args) == 0:
            return ShellCommandResponse(
                success=False, error="Command args cannot be empty"
            )
        logger.info(
            "Shell command requested cmd=%s cwd=%s", args[0], base_dir or Path.cwd()
        )

        # Validate base_dir if provided
        cwd = None
        if base_dir:
            base_path = Path(base_dir)
            if not base_path.exists():
                return ShellCommandResponse(
                    success=False,
                    error=f"Base directory does not exist: {base_dir}",
                )
            if not base_path.is_dir():
                return ShellCommandResponse(
                    success=False,
                    error=f"Base directory is not a directory: {base_dir}",
                )
            cwd = str(base_path)

        # Run the command
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=timeout,
        )

        # Process output
        stdout_lines = result.stdout.split("\n") if result.stdout else []
        stderr_lines = result.stderr.split("\n") if result.stderr else []

        # Apply tail limit if specified
        if tail > 0:
            stdout_lines = stdout_lines[-tail:]
            stderr_lines = stderr_lines[-tail:]

        stdout = "\n".join(stdout_lines)
        stderr = "\n".join(stderr_lines)

        # Determine success based on return code
        success = result.returncode == 0
        if success:
            logger.info(
                "Shell command succeeded cmd=%s return_code=%s",
                args[0],
                result.returncode,
            )
        else:
            logger.warning(
                "Shell command failed cmd=%s return_code=%s", args[0], result.returncode
            )

        return ShellCommandResponse(
            success=success,
            data=ShellCommandData(
                command=" ".join(args),
                return_code=result.returncode,
                stdout=stdout,
                stderr=stderr,
                working_directory=cwd or str(Path.cwd()),
                output_truncated=(
                    tail > 0 and len(result.stdout.split("\n")) > tail
                    if result.stdout
                    else False
                ),
            ),
        )

    except subprocess.TimeoutExpired:
        logger.warning(
            "Shell command timed out cmd=%s timeout=%s",
            args[0] if args else "",
            timeout,
        )
        return ShellCommandResponse(
            success=False, error=f"Command timed out after {timeout} seconds"
        )
    except FileNotFoundError:
        logger.warning("Shell command not found cmd=%s", args[0] if args else "")
        return ShellCommandResponse(
            success=False, error=f"Command not found: {args[0]}"
        )
    except Exception as e:
        logger.exception("Failed to run shell command cmd=%s", args[0] if args else "")
        return ShellCommandResponse(
            success=False, error=f"Failed to run shell command: {str(e)}"
        )


@tool()
async def shell_run_shell_script(
    script: str,
    shell: str = "/bin/bash",
    base_dir: str = "",
    timeout: int = DEFAULT_SHELL_TIMEOUT,
) -> ShellScriptResponse:
    """
    Run a shell script (multiple commands) and return the output.

    Args:
        script: Shell script content to execute
        shell: Shell interpreter to use (defaults to /bin/bash)
        base_dir: Working directory to run the script in
        timeout: Maximum time in seconds to wait for script completion

    Returns:
        Script output, error, and return code

    Examples:
        - Simple script: {"script": "echo 'Hello'\nls -la"}
        - Multi-line: {"script": "cd /tmp\ntouch test.txt\nls test.txt"}
    """
    try:
        if not script or script.strip() == "":
            return ShellScriptResponse(
                success=False, error="Script content cannot be empty"
            )

        # Validate script size to prevent memory exhaustion
        if len(script) > MAX_SCRIPT_SIZE:
            return ShellScriptResponse(
                success=False,
                error=f"Script exceeds maximum size of {MAX_SCRIPT_SIZE // 1024}KB",
            )

        # Validate shell is in the allowlist to prevent arbitrary executable execution
        if shell not in ALLOWED_SHELLS:
            logger.warning(
                "Blocked shell script execution with disallowed shell: %s", shell
            )
            return ShellScriptResponse(
                success=False,
                error=f"Shell '{shell}' is not allowed. Permitted shells: "
                f"{', '.join(sorted(s for s in ALLOWED_SHELLS if s.startswith('/')))}",
            )

        logger.info(
            "Shell script requested length=%d cwd=%s shell=%s",
            len(script),
            base_dir or Path.cwd(),
            shell,
        )

        # Validate base_dir if provided
        cwd = None
        if base_dir:
            base_path = Path(base_dir)
            if not base_path.exists():
                return ShellScriptResponse(
                    success=False,
                    error=f"Base directory does not exist: {base_dir}",
                )
            cwd = str(base_path)

        # Run the script
        result = subprocess.run(
            [shell, "-c", script],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=timeout,
        )

        success = result.returncode == 0
        if success:
            logger.info("Shell script succeeded return_code=%s", result.returncode)
        else:
            logger.warning("Shell script failed return_code=%s", result.returncode)

        return ShellScriptResponse(
            success=success,
            data=ShellScriptData(
                script=script,
                shell=shell,
                return_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                working_directory=cwd or str(Path.cwd()),
            ),
        )

    except subprocess.TimeoutExpired:
        logger.warning("Shell script timed out timeout=%s", timeout)
        return ShellScriptResponse(
            success=False, error=f"Script timed out after {timeout} seconds"
        )
    except FileNotFoundError:
        logger.warning("Shell not found shell=%s", shell)
        return ShellScriptResponse(success=False, error=f"Shell not found: {shell}")
    except Exception as e:
        logger.exception("Failed to run shell script")
        return ShellScriptResponse(
            success=False, error=f"Failed to run shell script: {str(e)}"
        )


@tool()
async def shell_check_command_exists(command: str) -> CommandExistsResponse:
    """
    Check if a command exists in the system PATH.

    Args:
        command: Name of the command to check (e.g., "git", "python", "node")

    Returns:
        Boolean indicating whether the command exists and its path if found
    """
    try:
        result = subprocess.run(
            ["which", command],
            capture_output=True,
            text=True,
            timeout=5,
        )

        exists = result.returncode == 0
        path = result.stdout.strip() if exists else None

        logger.info("Checked command exists cmd=%s exists=%s", command, exists)
        return CommandExistsResponse(
            success=True,
            data=CommandExistsData(command=command, exists=exists, path=path),
        )

    except Exception as e:
        logger.exception("Failed checking command exists cmd=%s", command)
        return CommandExistsResponse(success=False, error=str(e))


# Allowlist of safe environment variables that can be exposed
# Sensitive variables like API keys, secrets, and credentials are excluded
_SAFE_ENV_VARS = frozenset(
    {
        "PATH",
        "HOME",
        "USER",
        "SHELL",
        "LANG",
        "LC_ALL",
        "TERM",
        "PWD",
        "HOSTNAME",
        "TZ",
        "PYTHONPATH",
        "NODE_PATH",
        "VIRTUAL_ENV",
        "CONDA_DEFAULT_ENV",
    }
)


@tool()
async def shell_get_environment_variable(
    variable_name: str,
) -> EnvironmentVariableResponse:
    """
    Get the value of a safe environment variable.

    Only allows access to a predefined list of non-sensitive environment variables
    for security reasons. Sensitive variables like API keys, secrets, and credentials
    are not accessible through this tool.

    Args:
        variable_name: Name of the environment variable

    Returns:
        Value of the environment variable or error if not allowed
    """
    try:
        import os

        # Check if the variable is in the safe allowlist
        if variable_name not in _SAFE_ENV_VARS:
            logger.warning(
                "Blocked access to environment variable name=%s (not in allowlist)",
                variable_name,
            )
            return EnvironmentVariableResponse(
                success=False,
                error=f"Access to environment variable '{variable_name}' is not allowed. "
                f"Only these variables are accessible: {', '.join(sorted(_SAFE_ENV_VARS))}",
            )

        value = os.environ.get(variable_name)

        logger.info(
            "Fetched environment variable name=%s is_set=%s",
            variable_name,
            value is not None,
        )
        return EnvironmentVariableResponse(
            success=True,
            data=EnvironmentVariableData(
                variable_name=variable_name,
                value=value,
                is_set=value is not None,
            ),
        )

    except Exception as e:
        logger.exception("Failed fetching environment variable name=%s", variable_name)
        return EnvironmentVariableResponse(success=False, error=str(e))


@tool()
async def shell_get_current_directory() -> CurrentDirectoryResponse:
    """
    Get the current working directory.

    Returns:
        Current working directory path
    """
    try:
        cwd = str(Path.cwd())

        logger.info("Retrieved current directory cwd=%s", cwd)
        return CurrentDirectoryResponse(
            success=True, data=CurrentDirectoryData(current_directory=cwd)
        )

    except Exception as e:
        logger.exception("Failed to get current directory")
        return CurrentDirectoryResponse(success=False, error=str(e))


@tool()
async def shell_get_system_info() -> SystemInfoResponse:
    """
    Get basic system information.

    Returns:
        System information including OS, platform, Python version, etc.
    """
    try:
        import os
        import platform

        logger.info("Retrieved system info")
        return SystemInfoResponse(
            success=True,
            data=SystemInfoData(
                os=platform.system(),
                os_version=platform.version(),
                platform=platform.platform(),
                architecture=platform.machine(),
                processor=platform.processor(),
                python_version=platform.python_version(),
                hostname=platform.node(),
                user=os.environ.get("USER") or os.environ.get("USERNAME"),
            ),
        )

    except Exception as e:
        logger.exception("Failed to get system info")
        return SystemInfoResponse(success=False, error=str(e))
