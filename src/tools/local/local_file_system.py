from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from src.tools import tool


@tool("filesystem_write_file")
async def write_file(
    content: str,
    filename: str = "",
    directory: str = "",
    extension: str = "",
) -> dict:
    """
    Write content to a local file.

    Args:
        content: Content to write to the file
        filename: Name of the file (defaults to UUID if not provided)
        directory: Directory to write file to (defaults to current working directory)
        extension: File extension (defaults to 'txt' if not provided)

    Returns:
        Path to the created file or error message

    Examples:
        - Write with filename: {"content": "Hello", "filename": "test.txt"}
        - Write with UUID: {"content": "Hello", "extension": "txt"}
        - Write to directory: {"content": "Hello", "filename": "test.txt", "directory": "/tmp"}
    """
    try:
        # Generate filename if not provided
        filename = filename if filename else str(uuid4())

        # Extract extension from filename if present
        if filename and "." in filename:
            path_obj = Path(filename)
            filename = path_obj.stem
            extension = extension or path_obj.suffix.lstrip(".")

        # Use defaults
        directory = directory if directory else str(Path.cwd())
        extension = (extension if extension else "txt").lstrip(".")

        # Create directory if it doesn't exist
        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)

        # Construct full filename with extension
        full_filename = f"{filename}.{extension}"
        file_path = dir_path / full_filename

        # Write content to file
        file_path.write_text(content, encoding="utf-8")

        return {
            "success": True,
            "data": {
                "message": "Successfully wrote file",
                "file_path": str(file_path),
                "filename": full_filename,
                "directory": str(dir_path),
                "size_bytes": len(content),
            },
        }

    except Exception as e:
        return {"success": False, "error": f"Failed to write file: {str(e)}"}


@tool("filesystem_read_file")
async def read_file(
    filename: str,
    directory: str = "",
) -> dict:
    """
    Read content from a local file.

    Args:
        filename: Name of the file to read
        directory: Directory containing the file (defaults to current working directory)

    Returns:
        File content and metadata
    """
    try:
        directory = directory if directory else str(Path.cwd())
        file_path = Path(directory) / filename

        if not file_path.exists():
            return {"success": False, "error": f"File not found: {file_path}"}

        if not file_path.is_file():
            return {"success": False, "error": f"Path is not a file: {file_path}"}

        content = file_path.read_text(encoding="utf-8")

        return {
            "success": True,
            "data": {
                "content": content,
                "file_path": str(file_path),
                "filename": filename,
                "size_bytes": file_path.stat().st_size,
            },
        }

    except Exception as e:
        return {"success": False, "error": f"Failed to read file: {str(e)}"}


@tool("filesystem_list_files")
async def list_files(
    directory: str = "",
    pattern: str = "*",
    recursive: bool = False,
) -> dict:
    """
    List files in a directory with optional pattern matching.

    Args:
        directory: Directory to list files from (defaults to current working directory)
        pattern: Glob pattern to filter files (e.g., "*.txt", "*.py")
        recursive: If True, search recursively in subdirectories

    Returns:
        List of files matching the pattern
    """
    try:
        directory = directory if directory else str(Path.cwd())
        dir_path = Path(directory)

        if not dir_path.exists():
            return {"success": False, "error": f"Directory not found: {dir_path}"}

        if not dir_path.is_dir():
            return {"success": False, "error": f"Path is not a directory: {dir_path}"}

        # Get files based on recursive flag
        if recursive:
            files = list(dir_path.rglob(pattern))
        else:
            files = list(dir_path.glob(pattern))

        # Filter to only include files (not directories)
        files = [f for f in files if f.is_file()]

        file_list = [
            {
                "name": f.name,
                "path": str(f),
                "size_bytes": f.stat().st_size,
                "extension": f.suffix.lstrip(".") if f.suffix else None,
                "modified_time": f.stat().st_mtime,
            }
            for f in sorted(files)
        ]

        return {
            "success": True,
            "data": file_list,
            "count": len(file_list),
            "directory": str(dir_path),
        }

    except Exception as e:
        return {"success": False, "error": f"Failed to list files: {str(e)}"}


@tool("filesystem_delete_file")
async def delete_file(
    filename: str,
    directory: str = "",
) -> dict:
    """
    Delete a file from the local file system.

    Args:
        filename: Name of the file to delete
        directory: Directory containing the file (defaults to current working directory)

    Returns:
        Confirmation of deletion
    """
    try:
        directory = directory if directory else str(Path.cwd())
        file_path = Path(directory) / filename

        if not file_path.exists():
            return {"success": False, "error": f"File not found: {file_path}"}

        if not file_path.is_file():
            return {"success": False, "error": f"Path is not a file: {file_path}"}

        file_path.unlink()

        return {
            "success": True,
            "data": {
                "message": "Successfully deleted file",
                "file_path": str(file_path),
                "filename": filename,
            },
        }

    except Exception as e:
        return {"success": False, "error": f"Failed to delete file: {str(e)}"}


@tool("filesystem_create_directory")
async def create_directory(
    directory: str,
    parents: bool = True,
) -> dict:
    """
    Create a new directory.

    Args:
        directory: Path of the directory to create
        parents: If True, create parent directories as needed

    Returns:
        Confirmation of directory creation
    """
    try:
        dir_path = Path(directory)

        if dir_path.exists():
            if dir_path.is_dir():
                return {
                    "success": False,
                    "error": f"Directory already exists: {dir_path}",
                }
            else:
                return {
                    "success": False,
                    "error": f"Path exists but is not a directory: {dir_path}",
                }

        dir_path.mkdir(parents=parents, exist_ok=False)

        return {
            "success": True,
            "data": {
                "message": "Successfully created directory",
                "directory": str(dir_path),
            },
        }

    except Exception as e:
        return {"success": False, "error": f"Failed to create directory: {str(e)}"}


@tool("filesystem_file_exists")
async def file_exists(
    filename: str,
    directory: str = "",
) -> dict:
    """
    Check if a file exists.

    Args:
        filename: Name of the file to check
        directory: Directory to check in (defaults to current working directory)

    Returns:
        Boolean indicating whether the file exists
    """
    try:
        directory = directory if directory else str(Path.cwd())
        file_path = Path(directory) / filename

        exists = file_path.exists() and file_path.is_file()

        result = {"exists": exists, "file_path": str(file_path), "filename": filename}

        if exists:
            result["size_bytes"] = file_path.stat().st_size
            result["modified_time"] = file_path.stat().st_mtime

        return {"success": True, "data": result}

    except Exception as e:
        return {"success": False, "error": str(e)}


@tool("filesystem_get_file_info")
async def get_file_info(
    filename: str,
    directory: str = "",
) -> dict:
    """
    Get detailed information about a file.

    Args:
        filename: Name of the file
        directory: Directory containing the file (defaults to current working directory)

    Returns:
        Detailed file information including size, timestamps, etc.
    """
    try:
        directory = directory if directory else str(Path.cwd())
        file_path = Path(directory) / filename

        if not file_path.exists():
            return {"success": False, "error": f"File not found: {file_path}"}

        if not file_path.is_file():
            return {"success": False, "error": f"Path is not a file: {file_path}"}

        stat = file_path.stat()

        return {
            "success": True,
            "data": {
                "name": file_path.name,
                "path": str(file_path),
                "size_bytes": stat.st_size,
                "extension": file_path.suffix.lstrip(".") if file_path.suffix else None,
                "created_time": stat.st_ctime,
                "modified_time": stat.st_mtime,
                "accessed_time": stat.st_atime,
                "is_symlink": file_path.is_symlink(),
            },
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@tool("filesystem_append_to_file")
async def append_to_file(
    content: str,
    filename: str,
    directory: str = "",
) -> dict:
    """
    Append content to an existing file.

    Args:
        content: Content to append to the file
        filename: Name of the file
        directory: Directory containing the file (defaults to current working directory)

    Returns:
        Confirmation of append operation
    """
    try:
        directory = directory if directory else str(Path.cwd())
        file_path = Path(directory) / filename

        if not file_path.exists():
            return {"success": False, "error": f"File not found: {file_path}"}

        with open(file_path, "a", encoding="utf-8") as f:
            f.write(content)

        return {
            "success": True,
            "data": {
                "message": "Successfully appended to file",
                "file_path": str(file_path),
                "appended_bytes": len(content),
                "new_size_bytes": file_path.stat().st_size,
            },
        }

    except Exception as e:
        return {"success": False, "error": f"Failed to append to file: {str(e)}"}


@tool("filesystem_copy_file")
async def copy_file(
    source_filename: str,
    destination_filename: str,
    source_directory: str = "",
    destination_directory: str = "",
) -> dict:
    """
    Copy a file from source to destination.

    Args:
        source_filename: Name of the source file
        destination_filename: Name of the destination file
        source_directory: Directory containing the source file
        destination_directory: Directory for the destination file

    Returns:
        Confirmation of copy operation
    """
    try:
        import shutil

        source_directory = source_directory if source_directory else str(Path.cwd())
        destination_directory = (
            destination_directory if destination_directory else str(Path.cwd())
        )

        source_path = Path(source_directory) / source_filename
        dest_path = Path(destination_directory) / destination_filename

        if not source_path.exists():
            return {"success": False, "error": f"Source file not found: {source_path}"}

        # Create destination directory if it doesn't exist
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(source_path, dest_path)

        return {
            "success": True,
            "data": {
                "message": "Successfully copied file",
                "source_path": str(source_path),
                "destination_path": str(dest_path),
                "size_bytes": dest_path.stat().st_size,
            },
        }

    except Exception as e:
        return {"success": False, "error": f"Failed to copy file: {str(e)}"}
