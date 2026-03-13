"""Pydantic output schemas for local tools (calculator, shell, filesystem)."""

from pydantic import BaseModel, Field

from src.humcp.schemas import ToolResponse

# =============================================================================
# Calculator Tool Schemas
# =============================================================================


class BinaryOperationData(BaseModel):
    """Output data for binary arithmetic operations (add, subtract, multiply, divide, etc.)."""

    operation: str = Field(..., description="Name of the operation performed")
    a: float = Field(..., description="First operand")
    b: float = Field(..., description="Second operand")
    result: float = Field(..., description="Result of the operation")


class FactorialData(BaseModel):
    """Output data for factorial operation."""

    operation: str = Field("factorial", description="Name of the operation")
    n: int = Field(..., description="Input number")
    result: int = Field(..., description="Factorial result")


class IsPrimeData(BaseModel):
    """Output data for is_prime check."""

    n: int = Field(..., description="Number that was checked")
    is_prime: bool = Field(..., description="Whether the number is prime")
    divisible_by: int | None = Field(
        None, description="First divisor found (if not prime)"
    )


class UnaryOperationData(BaseModel):
    """Output data for unary operations (sqrt, abs)."""

    operation: str = Field(..., description="Name of the operation")
    n: float = Field(..., description="Input number")
    result: float = Field(..., description="Result of the operation")


class LogarithmData(BaseModel):
    """Output data for logarithm operation."""

    operation: str = Field(
        ..., description="'ln' for natural log, 'log' for custom base"
    )
    n: float = Field(..., description="Input number")
    base: float | None = Field(
        None, description="Logarithm base (None for natural log)"
    )
    result: float = Field(..., description="Logarithm result")


# =============================================================================
# Shell Tool Schemas
# =============================================================================


class ShellCommandData(BaseModel):
    """Output data for shell command execution."""

    command: str = Field(..., description="Command that was executed")
    return_code: int = Field(..., description="Process return code (0 = success)")
    stdout: str = Field("", description="Standard output")
    stderr: str = Field("", description="Standard error output")
    working_directory: str = Field(..., description="Directory where command was run")
    output_truncated: bool = Field(False, description="Whether output was truncated")


class ShellScriptData(BaseModel):
    """Output data for shell script execution."""

    script: str = Field(..., description="Script that was executed")
    shell: str = Field(..., description="Shell interpreter used")
    return_code: int = Field(..., description="Process return code")
    stdout: str = Field("", description="Standard output")
    stderr: str = Field("", description="Standard error output")
    working_directory: str = Field(..., description="Directory where script was run")


class CommandExistsData(BaseModel):
    """Output data for command existence check."""

    command: str = Field(..., description="Command that was checked")
    exists: bool = Field(..., description="Whether the command exists")
    path: str | None = Field(None, description="Full path to command if found")


class EnvironmentVariableData(BaseModel):
    """Output data for environment variable retrieval."""

    variable_name: str = Field(..., description="Name of the environment variable")
    value: str | None = Field(None, description="Value of the variable")
    is_set: bool = Field(..., description="Whether the variable is set")


class CurrentDirectoryData(BaseModel):
    """Output data for current directory retrieval."""

    current_directory: str = Field(..., description="Current working directory path")


class SystemInfoData(BaseModel):
    """Output data for system information."""

    os: str = Field(..., description="Operating system name")
    os_version: str = Field(..., description="Operating system version")
    platform: str = Field(..., description="Platform identifier")
    architecture: str = Field(..., description="Machine architecture")
    processor: str = Field(..., description="Processor type")
    python_version: str = Field(..., description="Python version")
    hostname: str = Field(..., description="Machine hostname")
    user: str | None = Field(None, description="Current user")


# =============================================================================
# Filesystem Tool Schemas
# =============================================================================


class WriteFileData(BaseModel):
    """Output data for file write operation."""

    message: str = Field(..., description="Success message")
    file_path: str = Field(..., description="Full path to the created file")
    filename: str = Field(..., description="Name of the file")
    directory: str = Field(..., description="Directory containing the file")
    size_bytes: int = Field(..., description="Size of written content in bytes")


class ReadFileData(BaseModel):
    """Output data for file read operation."""

    content: str = Field(..., description="File content")
    file_path: str = Field(..., description="Full path to the file")
    filename: str = Field(..., description="Name of the file")
    size_bytes: int = Field(..., description="File size in bytes")


class FileInfo(BaseModel):
    """Information about a single file."""

    name: str = Field(..., description="File name")
    path: str = Field(..., description="Full file path")
    size_bytes: int = Field(..., description="File size in bytes")
    extension: str | None = Field(None, description="File extension")
    modified_time: float = Field(..., description="Last modification timestamp")


class ListFilesData(BaseModel):
    """Output data for list files operation."""

    files: list[FileInfo] = Field(default_factory=list, description="List of files")
    count: int = Field(..., description="Number of files found")
    directory: str = Field(..., description="Directory that was listed")


class DeleteFileData(BaseModel):
    """Output data for file deletion."""

    message: str = Field(..., description="Success message")
    file_path: str = Field(..., description="Path of deleted file")
    filename: str = Field(..., description="Name of deleted file")


class CreateDirectoryData(BaseModel):
    """Output data for directory creation."""

    message: str = Field(..., description="Success message")
    directory: str = Field(..., description="Path of created directory")


class FileExistsData(BaseModel):
    """Output data for file existence check."""

    exists: bool = Field(..., description="Whether the file exists")
    file_path: str = Field(..., description="Full path to the file")
    filename: str = Field(..., description="Name of the file")
    size_bytes: int | None = Field(None, description="File size if exists")
    modified_time: float | None = Field(None, description="Modification time if exists")


class FileInfoDetailedData(BaseModel):
    """Output data for detailed file information."""

    name: str = Field(..., description="File name")
    path: str = Field(..., description="Full file path")
    size_bytes: int = Field(..., description="File size in bytes")
    extension: str | None = Field(None, description="File extension")
    created_time: float = Field(..., description="Creation timestamp")
    modified_time: float = Field(..., description="Modification timestamp")
    accessed_time: float = Field(..., description="Last access timestamp")
    is_symlink: bool = Field(False, description="Whether file is a symbolic link")


class AppendFileData(BaseModel):
    """Output data for file append operation."""

    message: str = Field(..., description="Success message")
    file_path: str = Field(..., description="Full path to the file")
    appended_bytes: int = Field(..., description="Number of bytes appended")
    new_size_bytes: int = Field(..., description="New total file size")


class CopyFileData(BaseModel):
    """Output data for file copy operation."""

    message: str = Field(..., description="Success message")
    source_path: str = Field(..., description="Source file path")
    destination_path: str = Field(..., description="Destination file path")
    size_bytes: int = Field(..., description="Size of copied file")


# =============================================================================
# Response Wrappers (inheriting from ToolResponse[T])
# =============================================================================


# Calculator Responses
class CalculatorResponse(
    ToolResponse[
        BinaryOperationData
        | FactorialData
        | IsPrimeData
        | UnaryOperationData
        | LogarithmData
    ]
):
    """Generic response for calculator operations."""

    pass


# Shell Responses
class ShellCommandResponse(ToolResponse[ShellCommandData]):
    """Response for shell command execution."""

    pass


class ShellScriptResponse(ToolResponse[ShellScriptData]):
    """Response for shell script execution."""

    pass


class CommandExistsResponse(ToolResponse[CommandExistsData]):
    """Response for command existence check."""

    pass


class EnvironmentVariableResponse(ToolResponse[EnvironmentVariableData]):
    """Response for environment variable retrieval."""

    pass


class CurrentDirectoryResponse(ToolResponse[CurrentDirectoryData]):
    """Response for current directory retrieval."""

    pass


class SystemInfoResponse(ToolResponse[SystemInfoData]):
    """Response for system information."""

    pass


# Filesystem Responses
class WriteFileResponse(ToolResponse[WriteFileData]):
    """Response for file write operation."""

    pass


class ReadFileResponse(ToolResponse[ReadFileData]):
    """Response for file read operation."""

    pass


class ListFilesResponse(ToolResponse[ListFilesData]):
    """Response for list files operation."""

    pass


class DeleteFileResponse(ToolResponse[DeleteFileData]):
    """Response for file deletion."""

    pass


class CreateDirectoryResponse(ToolResponse[CreateDirectoryData]):
    """Response for directory creation."""

    pass


class FileExistsResponse(ToolResponse[FileExistsData]):
    """Response for file existence check."""

    pass


class FileInfoResponse(ToolResponse[FileInfoDetailedData]):
    """Response for file information."""

    pass


class AppendFileResponse(ToolResponse[AppendFileData]):
    """Response for file append operation."""

    pass


class CopyFileResponse(ToolResponse[CopyFileData]):
    """Response for file copy operation."""

    pass
