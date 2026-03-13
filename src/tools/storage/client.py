"""S3-compatible storage client setup and validation utilities.

This module provides the MinIO client singleton, bucket validation,
object name validation, and local path validation for the storage tools.

Environment Variables:
    STORAGE_ENDPOINT: Storage server address (default: "minio:9000")
    STORAGE_ACCESS_KEY: Access key for authentication (required)
    STORAGE_SECRET_KEY: Secret key for authentication (required)
    STORAGE_SECURE: Use HTTPS connection (default: "false")
    STORAGE_REGION: Region for the storage service (optional, needed for AWS S3/GCS)
    STORAGE_ALLOWED_BUCKETS: Comma-separated list of allowed bucket names (optional)
    STORAGE_ALLOW_ABSOLUTE_PATHS: Allow absolute paths for downloads (default: "false")
"""

import asyncio
import logging
import os
from functools import partial
from pathlib import Path

from minio import Minio

logger = logging.getLogger(__name__)

# Singleton S3-compatible client
_client: Minio | None = None
_allowed_buckets: set[str] | None = None


async def run_sync[T](func: partial[T]) -> T:
    """Run a synchronous function in a thread pool to avoid blocking the event loop.

    The S3 client uses synchronous HTTP calls. This helper runs those calls
    in a thread pool executor to maintain async compatibility.

    Args:
        func: A partial function wrapping the sync call.

    Returns:
        The result of the synchronous function.

    Example:
        result = await run_sync(partial(client.list_buckets))
    """
    return await asyncio.to_thread(func)


def get_client() -> Minio:
    """Get or create the S3-compatible client singleton.

    Creates an S3-compatible client using environment variables for configuration.
    The client is cached as a singleton for reuse across requests.

    Returns:
        Minio: Configured S3-compatible client instance.

    Raises:
        ValueError: If STORAGE_ACCESS_KEY or STORAGE_SECRET_KEY is not set.
    """
    global _client
    if _client is None:
        endpoint = os.getenv("STORAGE_ENDPOINT", "minio:9000")
        access_key = os.getenv("STORAGE_ACCESS_KEY")
        secret_key = os.getenv("STORAGE_SECRET_KEY")
        secure = os.getenv("STORAGE_SECURE", "false").lower() == "true"
        region = os.getenv("STORAGE_REGION") or None

        if not access_key or not secret_key:
            raise ValueError("STORAGE_ACCESS_KEY and STORAGE_SECRET_KEY must be set")

        _client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
            region=region,
        )
    return _client


def get_allowed_buckets() -> set[str]:
    """Get the set of allowed bucket names from environment.

    Parses STORAGE_ALLOWED_BUCKETS environment variable as a comma-separated
    list of bucket names. If not set, returns an empty set (all buckets allowed).

    Returns:
        set[str]: Set of allowed bucket names, or empty set if no restrictions.
    """
    global _allowed_buckets
    if _allowed_buckets is None:
        buckets_str = os.getenv("STORAGE_ALLOWED_BUCKETS", "")
        _allowed_buckets = {b.strip() for b in buckets_str.split(",") if b.strip()}
    return _allowed_buckets


def reset_client() -> None:
    """Reset the client singleton and cached configuration.

    Clears the cached S3 client and allowed buckets set. Primarily used
    for testing to ensure a fresh client state between tests.
    """
    global _client, _allowed_buckets
    _client = None
    _allowed_buckets = None


def validate_bucket(bucket: str) -> str | None:
    """Validate that a bucket is in the allowed list.

    Checks if the given bucket name is permitted according to the
    STORAGE_ALLOWED_BUCKETS configuration. If no allowlist is configured,
    all buckets are permitted.

    Args:
        bucket: Name of the bucket to validate.

    Returns:
        str | None: Error message if bucket is not allowed, None if permitted.
    """
    allowed = get_allowed_buckets()
    if allowed and bucket not in allowed:
        return f"Bucket '{bucket}' not in allowed list. Allowed: {sorted(allowed)}"
    return None


def validate_object_name(object_name: str) -> str | None:
    """Validate that an object name is safe and well-formed.

    Checks for path traversal attempts and invalid characters in object names.
    While S3 technically allows almost any characters in object names,
    we restrict to safe patterns for security.

    Args:
        object_name: Object key/path to validate.

    Returns:
        str | None: Error message if validation fails, None if valid.
    """
    if not object_name:
        return "Object name cannot be empty"

    # Reject path traversal patterns
    if ".." in object_name:
        return "Object name cannot contain '..'"

    # Reject absolute paths (starting with /)
    if object_name.startswith("/"):
        return "Object name cannot start with '/'"

    # Reject names with null bytes
    if "\x00" in object_name:
        return "Object name cannot contain null bytes"

    # Limit length (S3 limit is 1024 bytes)
    if len(object_name.encode("utf-8")) > 1024:
        return "Object name exceeds maximum length of 1024 bytes"

    return None


def _allow_absolute_paths() -> bool:
    """Check if absolute paths are allowed for downloads."""
    return os.getenv("STORAGE_ALLOW_ABSOLUTE_PATHS", "").lower() == "true"


def validate_local_path(file_path: str) -> str | None:
    """Validate that a local file path is safe for writing.

    By default, paths must be within the current working directory to prevent
    directory traversal attacks. Set STORAGE_ALLOW_ABSOLUTE_PATHS=true to allow
    writing to any path (use with caution).

    Args:
        file_path: Local file path to validate.

    Returns:
        str | None: Error message if validation fails, None if valid.
    """
    if not file_path:
        return "File path cannot be empty"

    path = Path(file_path)

    # Reject path traversal patterns
    if ".." in str(path):
        return "File path cannot contain '..'"

    # If absolute paths are allowed, skip containment check
    if _allow_absolute_paths():
        return None

    # Resolve both paths to compare
    try:
        resolved = path.resolve()
        base_dir = Path.cwd().resolve()

        # Check if path is within base directory
        resolved.relative_to(base_dir)
        return None
    except ValueError:
        return (
            f"Path '{file_path}' is outside allowed directory '{base_dir}'. "
            "Set STORAGE_ALLOW_ABSOLUTE_PATHS=true to allow absolute paths."
        )
    except OSError as e:
        return f"Invalid path: {e}"
