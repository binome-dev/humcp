"""E2B tools for running code, commands, and managing files in cloud sandboxes.

E2B provides secure, isolated sandbox environments for executing untrusted
code.  Each tool call creates a fresh sandbox that is destroyed after use.

Environment variables:
    E2B_API_KEY: API key for the E2B service.
"""

from __future__ import annotations

import logging

from src.humcp.credentials import resolve_credential
from src.humcp.decorator import tool
from src.tools.cloud.schemas import (
    E2BDownloadFileData,
    E2BDownloadFileResponse,
    E2BListFilesData,
    E2BListFilesResponse,
    E2BRunCodeData,
    E2BRunCodeResponse,
    E2BRunCommandData,
    E2BRunCommandResponse,
    E2BUploadFileData,
    E2BUploadFileResponse,
)

try:
    from e2b_code_interpreter import Sandbox
except ImportError as err:
    raise ImportError(
        "e2b-code-interpreter is required for E2B tools. "
        "Install with: pip install e2b-code-interpreter"
    ) from err

logger = logging.getLogger("humcp.tools.e2b")


@tool()
async def e2b_run_code(
    code: str,
    language: str = "python",
    timeout: int = 300,
) -> E2BRunCodeResponse:
    """Run code in an isolated E2B cloud sandbox.

    Executes source code in a disposable sandbox environment.  The sandbox
    is automatically destroyed after execution completes.

    Args:
        code: Source code to execute.
        language: Programming language. Defaults to 'python'.
        timeout: Sandbox timeout in seconds. Defaults to 300.

    Returns:
        Execution output including stdout, generated results, and any errors.
    """
    try:
        api_key = await resolve_credential("E2B_API_KEY")
        if not api_key:
            return E2BRunCodeResponse(
                success=False, error="E2B API key not configured. Set E2B_API_KEY."
            )

        logger.info(
            "Running code in E2B sandbox language=%s timeout=%d", language, timeout
        )
        sandbox = Sandbox.create(api_key=api_key, timeout=timeout)

        try:
            execution = sandbox.run_code(code)

            error_text = None
            if execution.error:
                error_text = (
                    f"{execution.error.name}: {execution.error.value}\n"
                    f"{execution.error.traceback}"
                )

            results: list[str] = []
            if hasattr(execution, "logs") and execution.logs:
                results.append(str(execution.logs))

            for result in execution.results:
                if hasattr(result, "text") and result.text:
                    results.append(result.text)
                elif hasattr(result, "png") and result.png:
                    results.append("[PNG image generated]")

            output = "\n".join(results) if results else "Code executed with no output."

            data = E2BRunCodeData(
                output=output,
                language=language,
                error=error_text,
            )

            logger.info("E2B code execution complete")
            return E2BRunCodeResponse(success=True, data=data)
        finally:
            try:
                sandbox.kill()
            except Exception:
                logger.warning("Failed to clean up E2B sandbox")
    except Exception as e:
        logger.exception("Failed to run code in E2B sandbox")
        return E2BRunCodeResponse(
            success=False, error=f"E2B execution failed: {str(e)}"
        )


@tool()
async def e2b_run_command(
    command: str,
    timeout: int = 300,
) -> E2BRunCommandResponse:
    """Run a shell command in an isolated E2B cloud sandbox.

    Executes a shell command in a disposable sandbox and returns stdout,
    stderr, and exit code.  The sandbox is automatically destroyed afterward.

    Args:
        command: Shell command to execute.
        timeout: Sandbox timeout in seconds. Defaults to 300.

    Returns:
        Command stdout, stderr, and exit code.
    """
    try:
        api_key = await resolve_credential("E2B_API_KEY")
        if not api_key:
            return E2BRunCommandResponse(
                success=False, error="E2B API key not configured. Set E2B_API_KEY."
            )

        logger.info("Running command in E2B sandbox command=%s", command[:100])
        sandbox = Sandbox.create(api_key=api_key, timeout=timeout)

        try:
            result = sandbox.commands.run(command)

            stdout = getattr(result, "stdout", "") or ""
            stderr = getattr(result, "stderr", "") or ""
            exit_code = getattr(result, "exit_code", None)

            data = E2BRunCommandData(
                stdout=stdout,
                stderr=stderr,
                exit_code=exit_code,
            )

            logger.info("E2B command complete exit_code=%s", exit_code)
            return E2BRunCommandResponse(success=True, data=data)
        finally:
            try:
                sandbox.kill()
            except Exception:
                logger.warning("Failed to clean up E2B sandbox")
    except Exception as e:
        logger.exception("Failed to run command in E2B sandbox")
        return E2BRunCommandResponse(
            success=False, error=f"E2B command failed: {str(e)}"
        )


@tool()
async def e2b_upload_file(
    path: str,
    content: str,
    timeout: int = 300,
) -> E2BUploadFileResponse:
    """Upload a text file to an E2B cloud sandbox.

    Creates a file at the specified path within a sandbox environment.
    The sandbox is destroyed after the operation.

    Args:
        path: Destination path in the sandbox (e.g. '/home/user/data.txt').
        content: Text content to write to the file.
        timeout: Sandbox timeout in seconds. Defaults to 300.

    Returns:
        Confirmation with the file path in the sandbox.
    """
    try:
        api_key = await resolve_credential("E2B_API_KEY")
        if not api_key:
            return E2BUploadFileResponse(
                success=False, error="E2B API key not configured. Set E2B_API_KEY."
            )

        logger.info("Uploading file to E2B sandbox path=%s", path)
        sandbox = Sandbox.create(api_key=api_key, timeout=timeout)

        try:
            sandbox.files.write(path, content)

            data = E2BUploadFileData(
                path=path,
                message=f"File uploaded to {path}",
            )

            logger.info("E2B file upload complete path=%s", path)
            return E2BUploadFileResponse(success=True, data=data)
        finally:
            try:
                sandbox.kill()
            except Exception:
                logger.warning("Failed to clean up E2B sandbox")
    except Exception as e:
        logger.exception("Failed to upload file to E2B sandbox")
        return E2BUploadFileResponse(
            success=False, error=f"E2B file upload failed: {str(e)}"
        )


@tool()
async def e2b_download_file(
    path: str,
    timeout: int = 300,
) -> E2BDownloadFileResponse:
    """Download a text file from an E2B cloud sandbox.

    Reads the content of a file at the specified path.  Only suitable for
    text files; binary files will produce garbled output.

    Args:
        path: Path of the file in the sandbox (e.g. '/home/user/output.txt').
        timeout: Sandbox timeout in seconds. Defaults to 300.

    Returns:
        File content and size.
    """
    try:
        api_key = await resolve_credential("E2B_API_KEY")
        if not api_key:
            return E2BDownloadFileResponse(
                success=False, error="E2B API key not configured. Set E2B_API_KEY."
            )

        logger.info("Downloading file from E2B sandbox path=%s", path)
        sandbox = Sandbox.create(api_key=api_key, timeout=timeout)

        try:
            content = sandbox.files.read(path)
            content_str = (
                content
                if isinstance(content, str)
                else content.decode("utf-8", errors="replace")
            )

            data = E2BDownloadFileData(
                path=path,
                content=content_str,
                size=len(content_str),
            )

            logger.info(
                "E2B file download complete path=%s size=%d", path, len(content_str)
            )
            return E2BDownloadFileResponse(success=True, data=data)
        finally:
            try:
                sandbox.kill()
            except Exception:
                logger.warning("Failed to clean up E2B sandbox")
    except Exception as e:
        logger.exception("Failed to download file from E2B sandbox")
        return E2BDownloadFileResponse(
            success=False, error=f"E2B file download failed: {str(e)}"
        )


@tool()
async def e2b_list_files(
    path: str = "/home/user",
    timeout: int = 300,
) -> E2BListFilesResponse:
    """List files and directories in an E2B cloud sandbox.

    Lists the contents of a directory at the specified path in the sandbox.

    Args:
        path: Directory path to list. Defaults to '/home/user'.
        timeout: Sandbox timeout in seconds. Defaults to 300.

    Returns:
        List of file and directory names in the specified path.
    """
    try:
        api_key = await resolve_credential("E2B_API_KEY")
        if not api_key:
            return E2BListFilesResponse(
                success=False, error="E2B API key not configured. Set E2B_API_KEY."
            )

        logger.info("Listing files in E2B sandbox path=%s", path)
        sandbox = Sandbox.create(api_key=api_key, timeout=timeout)

        try:
            entries = sandbox.files.list(path)
            file_names = [getattr(entry, "name", str(entry)) for entry in entries]

            data = E2BListFilesData(
                path=path,
                files=file_names,
                count=len(file_names),
            )

            logger.info(
                "E2B list files complete path=%s count=%d", path, len(file_names)
            )
            return E2BListFilesResponse(success=True, data=data)
        finally:
            try:
                sandbox.kill()
            except Exception:
                logger.warning("Failed to clean up E2B sandbox")
    except Exception as e:
        logger.exception("Failed to list files in E2B sandbox")
        return E2BListFilesResponse(
            success=False, error=f"E2B list files failed: {str(e)}"
        )
