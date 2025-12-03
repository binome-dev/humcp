from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import List

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from fastmcp import FastMCP


async def run_shell_command(
    args: List[str],
    tail: int = 100,
    base_dir: str = "",
    timeout: int = 30,
) -> dict:
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
            return {
                "success": False,
                "error": "Command args cannot be empty"
            }

        # Validate base_dir if provided
        cwd = None
        if base_dir:
            base_path = Path(base_dir)
            if not base_path.exists():
                return {
                    "success": False,
                    "error": f"Base directory does not exist: {base_dir}"
                }
            if not base_path.is_dir():
                return {
                    "success": False,
                    "error": f"Base directory is not a directory: {base_dir}"
                }
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

        return {
            "success": success,
            "data": {
                "command": " ".join(args),
                "return_code": result.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "working_directory": cwd or str(Path.cwd()),
                "output_truncated": tail > 0 and len(result.stdout.split("\n")) > tail if result.stdout else False
            }
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"Command timed out after {timeout} seconds"
        }
    except FileNotFoundError:
        return {
            "success": False,
            "error": f"Command not found: {args[0]}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to run shell command: {str(e)}"
        }


async def run_shell_script(
    script: str,
    shell: str = "/bin/bash",
    base_dir: str = "",
    timeout: int = 30,
) -> dict:
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
            return {
                "success": False,
                "error": "Script content cannot be empty"
            }

        # Validate base_dir if provided
        cwd = None
        if base_dir:
            base_path = Path(base_dir)
            if not base_path.exists():
                return {
                    "success": False,
                    "error": f"Base directory does not exist: {base_dir}"
                }
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

        return {
            "success": success,
            "data": {
                "script": script,
                "shell": shell,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "working_directory": cwd or str(Path.cwd())
            }
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"Script timed out after {timeout} seconds"
        }
    except FileNotFoundError:
        return {
            "success": False,
            "error": f"Shell not found: {shell}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to run shell script: {str(e)}"
        }


async def check_command_exists(command: str) -> dict:
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

        return {
            "success": True,
            "data": {
                "command": command,
                "exists": exists,
                "path": path
            }
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


async def get_environment_variable(variable_name: str) -> dict:
    """
    Get the value of an environment variable.

    Args:
        variable_name: Name of the environment variable

    Returns:
        Value of the environment variable or None if not set
    """
    try:
        import os

        value = os.environ.get(variable_name)

        return {
            "success": True,
            "data": {
                "variable_name": variable_name,
                "value": value,
                "is_set": value is not None
            }
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


async def get_current_directory() -> dict:
    """
    Get the current working directory.

    Returns:
        Current working directory path
    """
    try:
        cwd = str(Path.cwd())

        return {
            "success": True,
            "data": {
                "current_directory": cwd
            }
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


async def get_system_info() -> dict:
    """
    Get basic system information.

    Returns:
        System information including OS, platform, Python version, etc.
    """
    try:
        import os
        import platform

        info = {
            "os": platform.system(),
            "os_version": platform.version(),
            "platform": platform.platform(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "hostname": platform.node(),
            "user": os.environ.get("USER") or os.environ.get("USERNAME"),
        }

        return {
            "success": True,
            "data": info
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def register_tools(mcp: FastMCP) -> None:
    """Register all Shell tools with the MCP server."""

    # Command Execution
    # mcp.tool(name="shell_run_shell_command")(run_shell_command)
    mcp.tool(name="shell_run_shell_script")(run_shell_script)

    # System Information
    mcp.tool(name="shell_check_command_exists")(check_command_exists)
    mcp.tool(name="shell_get_environment_variable")(get_environment_variable)
    mcp.tool(name="shell_get_current_directory")(get_current_directory)
    mcp.tool(name="shell_get_system_info")(get_system_info)