"""Storage path utilities for resolving minio:// URLs to local files.

This module provides utilities to parse and resolve storage paths in the format:
    minio://bucket/path/to/object

Tools can use these utilities to transparently support both local files and
storage objects as input parameters.

Example:
    >>> from src.humcp.storage_path import resolve_path, is_storage_path
    >>>
    >>> # Check if path is a storage URL
    >>> is_storage_path("minio://datasets/data.csv")  # True
    >>> is_storage_path("/local/path/data.csv")       # False
    >>>
    >>> # Resolve path (downloads storage files to temp)
    >>> async with resolve_path("minio://datasets/data.csv") as local_path:
    ...     with open(local_path) as f:
    ...         data = f.read()
    >>> # Temp file is automatically cleaned up
"""

import logging
import os
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

STORAGE_SCHEME = "minio"


def is_storage_path(path: str) -> bool:
    """Check if a path is a storage URL.

    Args:
        path: Path string to check.

    Returns:
        True if path starts with 'minio://', False otherwise.
    """
    return path.startswith(f"{STORAGE_SCHEME}://")


def parse_storage_path(path: str) -> tuple[str, str]:
    """Parse a storage URL into bucket and object name.

    Args:
        path: Storage URL in format 'minio://bucket/path/to/object'.

    Returns:
        Tuple of (bucket, object_name).

    Raises:
        ValueError: If path is not a valid storage URL.

    Example:
        >>> parse_storage_path("minio://my-bucket/data/file.csv")
        ('my-bucket', 'data/file.csv')
    """
    if not is_storage_path(path):
        raise ValueError(f"Not a storage path: {path}")

    parsed = urlparse(path)
    bucket = parsed.netloc
    # Remove leading slash from path
    object_name = parsed.path.lstrip("/")

    if not bucket:
        raise ValueError(f"Invalid storage path (no bucket): {path}")
    if not object_name:
        raise ValueError(f"Invalid storage path (no object): {path}")

    return bucket, object_name


def get_storage_path(bucket: str, object_name: str) -> str:
    """Construct a storage URL from bucket and object name.

    Args:
        bucket: Bucket name.
        object_name: Object path within the bucket.

    Returns:
        Storage URL string.

    Example:
        >>> get_storage_path("my-bucket", "data/file.csv")
        'minio://my-bucket/data/file.csv'
    """
    return f"{STORAGE_SCHEME}://{bucket}/{object_name}"


async def download_to_temp(bucket: str, object_name: str) -> str:
    """Download a storage object to a temporary file.

    Args:
        bucket: Bucket name.
        object_name: Object path within the bucket.

    Returns:
        Path to the temporary file.

    Raises:
        ValueError: If storage client is not configured.
        Exception: If download fails.
    """
    # Import here to avoid circular imports
    from src.tools.storage.tools import get_client, validate_bucket

    # Validate bucket access
    if error := validate_bucket(bucket):
        raise ValueError(error)

    client = get_client()

    # Get file extension from object name for proper temp file naming
    ext = Path(object_name).suffix or ""

    # Create temp file with same extension
    fd, temp_path = tempfile.mkstemp(suffix=ext)
    os.close(fd)

    try:
        logger.info(
            "Downloading storage object bucket=%s object=%s", bucket, object_name
        )
        client.fget_object(bucket, object_name, temp_path)
        logger.info("Downloaded to temp file path=%s", temp_path)
        return temp_path
    except Exception:
        # Clean up temp file on error
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise


@asynccontextmanager
async def resolve_path(path: str):
    """Context manager that resolves a path, downloading from storage if needed.

    For local paths, yields the path unchanged. For storage paths, downloads
    the object to a temporary file, yields the temp path, then cleans up.

    Args:
        path: Local file path or storage URL (minio://bucket/object).

    Yields:
        Local file path (either original or temp file).

    Example:
        >>> async with resolve_path("minio://datasets/data.csv") as local_path:
        ...     with open(local_path) as f:
        ...         data = f.read()
        >>> # Temp file is automatically cleaned up

        >>> async with resolve_path("/local/data.csv") as local_path:
        ...     # local_path is "/local/data.csv" unchanged
        ...     with open(local_path) as f:
        ...         data = f.read()
    """
    if not is_storage_path(path):
        # Local path - yield unchanged
        yield path
        return

    # Storage path - download to temp
    bucket, object_name = parse_storage_path(path)
    temp_path = await download_to_temp(bucket, object_name)

    try:
        yield temp_path
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            logger.debug("Cleaning up temp file path=%s", temp_path)
            os.unlink(temp_path)


async def resolve_path_simple(path: str) -> str:
    """Resolve a path without context manager (caller must clean up).

    For local paths, returns the path unchanged. For storage paths, downloads
    the object to a temporary file and returns the temp path.

    WARNING: When using storage paths, the caller is responsible for cleaning
    up the temporary file. Prefer using resolve_path() context manager instead.

    Args:
        path: Local file path or storage URL.

    Returns:
        Local file path (either original or temp file).
    """
    if not is_storage_path(path):
        return path

    bucket, object_name = parse_storage_path(path)
    return await download_to_temp(bucket, object_name)
