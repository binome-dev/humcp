"""MinIO S3-compatible object storage tools.

This module provides tools for interacting with MinIO/S3-compatible object storage.
All tools follow a standardized response format and validate bucket access against
an optional allowlist.

Environment Variables:
    MINIO_ENDPOINT: MinIO server address (default: "minio:9000")
    MINIO_ACCESS_KEY: Access key for authentication (required)
    MINIO_SECRET_KEY: Secret key for authentication (required)
    MINIO_SECURE: Use HTTPS connection (default: "false")
    MINIO_ALLOWED_BUCKETS: Comma-separated list of allowed bucket names (optional)

Example:
    >>> result = await list_buckets()
    >>> if result.success:
    ...     for bucket in result.data.buckets:
    ...         print(bucket.name)
"""

import asyncio
import base64
import io
import logging
import os
from datetime import timedelta
from functools import partial
from pathlib import Path

from minio import Minio
from minio.commonconfig import CopySource
from minio.error import S3Error

from src.humcp.decorator import tool
from src.tools.storage.schemas import (
    BucketExistsData,
    BucketExistsResponse,
    BucketInfo,
    CopyObjectData,
    CopyObjectResponse,
    CreateBucketData,
    CreateBucketResponse,
    DeleteBucketData,
    DeleteBucketResponse,
    DeleteObjectData,
    DeleteObjectResponse,
    DownloadContentData,
    DownloadContentResponse,
    DownloadToPathData,
    DownloadToPathResponse,
    GetObjectMetadataData,
    GetObjectMetadataResponse,
    GetPresignedUrlData,
    GetPresignedUrlResponse,
    ListBucketsData,
    ListBucketsResponse,
    ListObjectsData,
    ListObjectsResponse,
    ObjectInfo,
    UploadContentData,
    UploadContentResponse,
    UploadFromPathData,
    UploadFromPathResponse,
)

logger = logging.getLogger(__name__)

# Singleton MinIO client
_client: Minio | None = None
_allowed_buckets: set[str] | None = None


async def run_sync[T](func: partial[T]) -> T:
    """Run a synchronous function in a thread pool to avoid blocking the event loop.

    The MinIO client uses synchronous HTTP calls. This helper runs those calls
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
    """Get or create the MinIO client singleton.

    Creates a MinIO client using environment variables for configuration.
    The client is cached as a singleton for reuse across requests.

    Returns:
        Minio: Configured MinIO client instance.

    Raises:
        ValueError: If MINIO_ACCESS_KEY or MINIO_SECRET_KEY is not set.
    """
    global _client
    if _client is None:
        endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
        access_key = os.getenv("MINIO_ACCESS_KEY")
        secret_key = os.getenv("MINIO_SECRET_KEY")
        secure = os.getenv("MINIO_SECURE", "false").lower() == "true"

        if not access_key or not secret_key:
            raise ValueError("MINIO_ACCESS_KEY and MINIO_SECRET_KEY must be set")

        _client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )
    return _client


def get_allowed_buckets() -> set[str]:
    """Get the set of allowed bucket names from environment.

    Parses MINIO_ALLOWED_BUCKETS environment variable as a comma-separated
    list of bucket names. If not set, returns an empty set (all buckets allowed).

    Returns:
        set[str]: Set of allowed bucket names, or empty set if no restrictions.
    """
    global _allowed_buckets
    if _allowed_buckets is None:
        buckets_str = os.getenv("MINIO_ALLOWED_BUCKETS", "")
        _allowed_buckets = {b.strip() for b in buckets_str.split(",") if b.strip()}
    return _allowed_buckets


def reset_client() -> None:
    """Reset the client singleton and cached configuration.

    Clears the cached MinIO client and allowed buckets set. Primarily used
    for testing to ensure a fresh client state between tests.
    """
    global _client, _allowed_buckets
    _client = None
    _allowed_buckets = None


def validate_bucket(bucket: str) -> str | None:
    """Validate that a bucket is in the allowed list.

    Checks if the given bucket name is permitted according to the
    MINIO_ALLOWED_BUCKETS configuration. If no allowlist is configured,
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
    While S3/MinIO technically allows almost any characters in object names,
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
    return os.getenv("MINIO_ALLOW_ABSOLUTE_PATHS", "").lower() == "true"


def validate_local_path(file_path: str) -> str | None:
    """Validate that a local file path is safe for writing.

    By default, paths must be within the current working directory to prevent
    directory traversal attacks. Set MINIO_ALLOW_ABSOLUTE_PATHS=true to allow
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
            "Set MINIO_ALLOW_ABSOLUTE_PATHS=true to allow absolute paths."
        )
    except OSError as e:
        return f"Invalid path: {e}"


# =============================================================================
# Bucket Operations
# =============================================================================


@tool()
async def list_buckets() -> ListBucketsResponse:
    """List all accessible buckets in MinIO.

    Retrieves all buckets visible to the configured credentials. If
    MINIO_ALLOWED_BUCKETS is set, only those buckets are included in the result.

    Returns:
        ListBucketsResponse: Response containing bucket list.
            On success: success=True, data=ListBucketsData(buckets=[...])
            On error: success=False, error=str
    """
    try:
        client = get_client()
        # Run sync MinIO call in thread pool to avoid blocking event loop
        all_buckets = await run_sync(partial(client.list_buckets))
        allowed = get_allowed_buckets()

        buckets = []
        for b in all_buckets:
            if not allowed or b.name in allowed:
                buckets.append(
                    BucketInfo(
                        name=b.name,
                        creation_date=b.creation_date.isoformat()
                        if b.creation_date
                        else None,
                    )
                )

        return ListBucketsResponse(success=True, data=ListBucketsData(buckets=buckets))
    except S3Error as e:
        logger.error("Failed to list buckets: %s", e)
        return ListBucketsResponse(success=False, error=str(e))
    except ValueError as e:
        return ListBucketsResponse(success=False, error=str(e))


@tool()
async def create_bucket(bucket: str) -> CreateBucketResponse:
    """Create a new bucket in MinIO.

    Creates a bucket with the specified name. The bucket must be in the
    allowed list if MINIO_ALLOWED_BUCKETS is configured.

    Args:
        bucket: Name of the bucket to create. Must follow S3 bucket naming rules:
            - 3-63 characters long
            - Lowercase letters, numbers, and hyphens only
            - Must start and end with a letter or number

    Returns:
        CreateBucketResponse: Response indicating creation result.
            On success: success=True, data=CreateBucketData(bucket=str, created=True)
            On error: success=False, error=str
    """
    if error := validate_bucket(bucket):
        return CreateBucketResponse(success=False, error=error)

    try:
        client = get_client()
        if await run_sync(partial(client.bucket_exists, bucket)):
            return CreateBucketResponse(
                success=False, error=f"Bucket '{bucket}' already exists"
            )

        await run_sync(partial(client.make_bucket, bucket))
        return CreateBucketResponse(
            success=True, data=CreateBucketData(bucket=bucket, created=True)
        )
    except S3Error as e:
        logger.error("Failed to create bucket '%s': %s", bucket, e)
        return CreateBucketResponse(success=False, error=str(e))
    except ValueError as e:
        return CreateBucketResponse(success=False, error=str(e))


@tool()
async def delete_bucket(bucket: str) -> DeleteBucketResponse:
    """Delete an empty bucket from MinIO.

    Removes a bucket from the storage. The bucket must be empty before
    deletion. Use list_objects to verify contents and delete_object to
    remove objects first if needed.

    Args:
        bucket: Name of the bucket to delete.

    Returns:
        DeleteBucketResponse: Response indicating deletion result.
            On success: success=True, data=DeleteBucketData(bucket=str, deleted=True)
            On error: success=False, error=str
                Common errors: bucket not empty, bucket does not exist
    """
    if error := validate_bucket(bucket):
        return DeleteBucketResponse(success=False, error=error)

    try:
        client = get_client()
        if not await run_sync(partial(client.bucket_exists, bucket)):
            return DeleteBucketResponse(
                success=False, error=f"Bucket '{bucket}' does not exist"
            )

        await run_sync(partial(client.remove_bucket, bucket))
        return DeleteBucketResponse(
            success=True, data=DeleteBucketData(bucket=bucket, deleted=True)
        )
    except S3Error as e:
        logger.error("Failed to delete bucket '%s': %s", bucket, e)
        return DeleteBucketResponse(success=False, error=str(e))
    except ValueError as e:
        return DeleteBucketResponse(success=False, error=str(e))


@tool()
async def bucket_exists(bucket: str) -> BucketExistsResponse:
    """Check if a bucket exists in MinIO.

    Verifies whether a bucket with the given name exists and is accessible.

    Args:
        bucket: Name of the bucket to check.

    Returns:
        BucketExistsResponse: Response indicating bucket existence.
            On success: success=True, data=BucketExistsData(bucket=str, exists=bool)
            On error: success=False, error=str
    """
    if error := validate_bucket(bucket):
        return BucketExistsResponse(success=False, error=error)

    try:
        client = get_client()
        exists = await run_sync(partial(client.bucket_exists, bucket))
        return BucketExistsResponse(
            success=True, data=BucketExistsData(bucket=bucket, exists=exists)
        )
    except S3Error as e:
        logger.error("Failed to check bucket '%s': %s", bucket, e)
        return BucketExistsResponse(success=False, error=str(e))
    except ValueError as e:
        return BucketExistsResponse(success=False, error=str(e))


# =============================================================================
# Object Listing
# =============================================================================


@tool()
async def list_objects(
    bucket: str, prefix: str = "", recursive: bool = True
) -> ListObjectsResponse:
    """List objects in a bucket with optional prefix filtering.

    Retrieves a list of objects in the specified bucket. Supports prefix
    filtering for listing objects in a specific "directory" and recursive
    listing to include objects in subdirectories.

    Args:
        bucket: Name of the bucket to list objects from.
        prefix: Filter objects by key prefix (e.g., "documents/2024/").
            Defaults to "" (no filter).
        recursive: If True, list all objects including those in subdirectories.
            If False, list only objects at the current level. Defaults to True.

    Returns:
        ListObjectsResponse: Response containing object list.
            On success: success=True, data=ListObjectsData(bucket, prefix, recursive, objects, count)
            On error: success=False, error=str
    """
    if error := validate_bucket(bucket):
        return ListObjectsResponse(success=False, error=error)

    try:
        client = get_client()
        if not await run_sync(partial(client.bucket_exists, bucket)):
            return ListObjectsResponse(
                success=False, error=f"Bucket '{bucket}' does not exist"
            )

        # list_objects returns an iterator, so we need to collect in thread pool
        def _list_objects() -> list[ObjectInfo]:
            result = []
            for obj in client.list_objects(bucket, prefix=prefix, recursive=recursive):
                result.append(
                    ObjectInfo(
                        name=obj.object_name,
                        size=obj.size,
                        last_modified=obj.last_modified.isoformat()
                        if obj.last_modified
                        else None,
                        etag=obj.etag,
                        is_dir=obj.is_dir,
                    )
                )
            return result

        objects = await run_sync(partial(_list_objects))

        return ListObjectsResponse(
            success=True,
            data=ListObjectsData(
                bucket=bucket,
                prefix=prefix,
                recursive=recursive,
                objects=objects,
                count=len(objects),
            ),
        )
    except S3Error as e:
        logger.error("Failed to list objects in '%s': %s", bucket, e)
        return ListObjectsResponse(success=False, error=str(e))
    except ValueError as e:
        return ListObjectsResponse(success=False, error=str(e))


# =============================================================================
# Upload Tools
# =============================================================================


@tool()
async def upload_content(
    bucket: str,
    object_name: str,
    content_base64: str,
    content_type: str = "application/octet-stream",
) -> UploadContentResponse:
    """Upload base64-encoded content to MinIO.

    Uploads data provided as a base64-encoded string to the specified
    bucket and object path. Best suited for small files (< 10MB) where
    content is already in memory.

    Args:
        bucket: Name of the destination bucket.
        object_name: Object key/path in the bucket (e.g., "documents/report.pdf").
        content_base64: Base64-encoded file content.
        content_type: MIME type of the content (e.g., "application/pdf", "image/jpeg").
            Defaults to "application/octet-stream".

    Returns:
        UploadContentResponse: Response containing upload result.
            On success: success=True, data=UploadContentData(bucket, object_name, size, etag, version_id)
            On error: success=False, error=str
    """
    if error := validate_bucket(bucket):
        return UploadContentResponse(success=False, error=error)
    if error := validate_object_name(object_name):
        return UploadContentResponse(success=False, error=error)

    try:
        client = get_client()

        # Ensure bucket exists
        if not await run_sync(partial(client.bucket_exists, bucket)):
            return UploadContentResponse(
                success=False, error=f"Bucket '{bucket}' does not exist"
            )

        # Decode base64 content
        try:
            content = base64.b64decode(content_base64)
        except Exception as e:
            return UploadContentResponse(
                success=False, error=f"Invalid base64 content: {e}"
            )

        # Upload
        data = io.BytesIO(content)
        result = await run_sync(
            partial(
                client.put_object,
                bucket,
                object_name,
                data,
                length=len(content),
                content_type=content_type,
            )
        )

        return UploadContentResponse(
            success=True,
            data=UploadContentData(
                bucket=bucket,
                object_name=object_name,
                size=len(content),
                etag=result.etag,
                version_id=result.version_id,
            ),
        )
    except S3Error as e:
        logger.error("Failed to upload to '%s/%s': %s", bucket, object_name, e)
        return UploadContentResponse(success=False, error=str(e))
    except ValueError as e:
        return UploadContentResponse(success=False, error=str(e))


@tool()
async def upload_from_path(
    bucket: str,
    object_name: str,
    file_path: str,
    content_type: str = "application/octet-stream",
) -> UploadFromPathResponse:
    """Upload a file from the local filesystem to MinIO.

    Uploads a file directly from disk to the specified bucket and object path.
    Suitable for large files as content is streamed rather than loaded into memory.

    Args:
        bucket: Name of the destination bucket.
        object_name: Object key/path in the bucket (e.g., "backups/data.zip").
        file_path: Absolute or relative path to the local file.
        content_type: MIME type of the content. Defaults to "application/octet-stream".

    Returns:
        UploadFromPathResponse: Response containing upload result.
            On success: success=True, data=UploadFromPathData(bucket, object_name, file_path, size, etag, version_id)
            On error: success=False, error=str
    """
    if error := validate_bucket(bucket):
        return UploadFromPathResponse(success=False, error=error)
    if error := validate_object_name(object_name):
        return UploadFromPathResponse(success=False, error=error)

    try:
        client = get_client()

        # Ensure bucket exists
        if not await run_sync(partial(client.bucket_exists, bucket)):
            return UploadFromPathResponse(
                success=False, error=f"Bucket '{bucket}' does not exist"
            )

        # Validate file path
        path = Path(file_path)
        if not path.exists():
            return UploadFromPathResponse(
                success=False, error=f"File not found: {file_path}"
            )
        if not path.is_file():
            return UploadFromPathResponse(
                success=False, error=f"Path is not a file: {file_path}"
            )

        # Upload
        result = await run_sync(
            partial(
                client.fput_object,
                bucket,
                object_name,
                file_path,
                content_type=content_type,
            )
        )

        return UploadFromPathResponse(
            success=True,
            data=UploadFromPathData(
                bucket=bucket,
                object_name=object_name,
                file_path=file_path,
                size=path.stat().st_size,
                etag=result.etag,
                version_id=result.version_id,
            ),
        )
    except S3Error as e:
        logger.error(
            "Failed to upload '%s' to '%s/%s': %s", file_path, bucket, object_name, e
        )
        return UploadFromPathResponse(success=False, error=str(e))
    except ValueError as e:
        return UploadFromPathResponse(success=False, error=str(e))


# =============================================================================
# Download Tools
# =============================================================================


@tool()
async def download_content(bucket: str, object_name: str) -> DownloadContentResponse:
    """Download an object and return its content as a base64-encoded string.

    Retrieves the complete content of an object and encodes it as base64.
    Best suited for small files (< 10MB) where content is needed in memory.
    For large files, use download_to_path instead.

    Args:
        bucket: Name of the source bucket.
        object_name: Object key/path to download.

    Returns:
        DownloadContentResponse: Response containing the object content.
            On success: success=True, data=DownloadContentData(bucket, object_name, content_base64, size, content_type, etag)
            On error: success=False, error=str
    """
    if error := validate_bucket(bucket):
        return DownloadContentResponse(success=False, error=error)
    if error := validate_object_name(object_name):
        return DownloadContentResponse(success=False, error=error)

    try:
        client = get_client()

        # Get object content and metadata in thread pool
        def _download() -> tuple[bytes, str, str]:
            response = client.get_object(bucket, object_name)
            try:
                content = response.read()
            finally:
                response.close()
                response.release_conn()
            stat = client.stat_object(bucket, object_name)
            return content, stat.content_type, stat.etag

        content, content_type_val, etag = await run_sync(partial(_download))

        return DownloadContentResponse(
            success=True,
            data=DownloadContentData(
                bucket=bucket,
                object_name=object_name,
                content_base64=base64.b64encode(content).decode("utf-8"),
                size=len(content),
                content_type=content_type_val,
                etag=etag,
            ),
        )
    except S3Error as e:
        logger.error("Failed to download '%s/%s': %s", bucket, object_name, e)
        return DownloadContentResponse(success=False, error=str(e))
    except ValueError as e:
        return DownloadContentResponse(success=False, error=str(e))


@tool()
async def download_to_path(
    bucket: str, object_name: str, file_path: str
) -> DownloadToPathResponse:
    """Download an object to a local file.

    Downloads an object from MinIO and saves it to the specified path.
    Parent directories are created automatically if they don't exist.
    Suitable for large files as content is streamed directly to disk.

    Args:
        bucket: Name of the source bucket.
        object_name: Object key/path to download.
        file_path: Destination path for the downloaded file.

    Returns:
        DownloadToPathResponse: Response confirming the download.
            On success: success=True, data=DownloadToPathData(bucket, object_name, file_path, size)
            On error: success=False, error=str
    """
    if error := validate_bucket(bucket):
        return DownloadToPathResponse(success=False, error=error)
    if error := validate_object_name(object_name):
        return DownloadToPathResponse(success=False, error=error)
    if error := validate_local_path(file_path):
        return DownloadToPathResponse(success=False, error=error)

    try:
        client = get_client()

        # Ensure parent directory exists
        path = Path(file_path)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            return DownloadToPathResponse(
                success=False,
                error=f"Permission denied creating directory: {path.parent}",
            )
        except OSError as e:
            return DownloadToPathResponse(
                success=False, error=f"Failed to create directory: {e}"
            )

        # Download
        await run_sync(partial(client.fget_object, bucket, object_name, file_path))

        # Get file size
        size = path.stat().st_size

        return DownloadToPathResponse(
            success=True,
            data=DownloadToPathData(
                bucket=bucket,
                object_name=object_name,
                file_path=file_path,
                size=size,
            ),
        )
    except S3Error as e:
        logger.error(
            "Failed to download '%s/%s' to '%s': %s", bucket, object_name, file_path, e
        )
        return DownloadToPathResponse(success=False, error=str(e))
    except ValueError as e:
        return DownloadToPathResponse(success=False, error=str(e))


# =============================================================================
# Delete & Copy
# =============================================================================


@tool()
async def delete_object(bucket: str, object_name: str) -> DeleteObjectResponse:
    """Delete an object from a bucket.

    Permanently removes an object from the specified bucket. This operation
    cannot be undone unless versioning is enabled on the bucket.

    Args:
        bucket: Name of the bucket containing the object.
        object_name: Object key/path to delete.

    Returns:
        DeleteObjectResponse: Response confirming the deletion.
            On success: success=True, data=DeleteObjectData(bucket, object_name, deleted=True)
            On error: success=False, error=str
    """
    if error := validate_bucket(bucket):
        return DeleteObjectResponse(success=False, error=error)
    if error := validate_object_name(object_name):
        return DeleteObjectResponse(success=False, error=error)

    try:
        client = get_client()

        # Check if object exists first
        try:
            await run_sync(partial(client.stat_object, bucket, object_name))
        except S3Error as e:
            if e.code == "NoSuchKey":
                return DeleteObjectResponse(
                    success=False,
                    error=f"Object '{object_name}' not found in bucket '{bucket}'",
                )
            raise

        await run_sync(partial(client.remove_object, bucket, object_name))
        return DeleteObjectResponse(
            success=True,
            data=DeleteObjectData(
                bucket=bucket,
                object_name=object_name,
                deleted=True,
            ),
        )
    except S3Error as e:
        logger.error("Failed to delete '%s/%s': %s", bucket, object_name, e)
        return DeleteObjectResponse(success=False, error=str(e))
    except ValueError as e:
        return DeleteObjectResponse(success=False, error=str(e))


@tool()
async def copy_object(
    source_bucket: str,
    source_object: str,
    dest_bucket: str,
    dest_object: str,
) -> CopyObjectResponse:
    """Copy an object from one location to another.

    Copies an object between buckets or within the same bucket. Both the
    source and destination buckets must be in the allowed list if
    MINIO_ALLOWED_BUCKETS is configured. The copy is performed server-side.

    Args:
        source_bucket: Name of the bucket containing the source object.
        source_object: Object key/path of the source object.
        dest_bucket: Name of the destination bucket.
        dest_object: Object key/path for the copied object.

    Returns:
        CopyObjectResponse: Response confirming the copy operation.
            On success: success=True, data=CopyObjectData(source, destination, etag, version_id)
            On error: success=False, error=str
    """
    # Validate both buckets
    if error := validate_bucket(source_bucket):
        return CopyObjectResponse(success=False, error=error)
    if error := validate_bucket(dest_bucket):
        return CopyObjectResponse(success=False, error=error)
    # Validate both object names
    if error := validate_object_name(source_object):
        return CopyObjectResponse(success=False, error=error)
    if error := validate_object_name(dest_object):
        return CopyObjectResponse(success=False, error=error)

    try:
        client = get_client()

        # Verify source exists
        try:
            await run_sync(partial(client.stat_object, source_bucket, source_object))
        except S3Error as e:
            if e.code == "NoSuchKey":
                return CopyObjectResponse(
                    success=False,
                    error=f"Source object '{source_object}' not found in bucket '{source_bucket}'",
                )
            raise

        # Ensure destination bucket exists
        if not await run_sync(partial(client.bucket_exists, dest_bucket)):
            return CopyObjectResponse(
                success=False,
                error=f"Destination bucket '{dest_bucket}' does not exist",
            )

        # Copy object
        result = await run_sync(
            partial(
                client.copy_object,
                dest_bucket,
                dest_object,
                CopySource(source_bucket, source_object),
            )
        )

        return CopyObjectResponse(
            success=True,
            data=CopyObjectData(
                source=f"{source_bucket}/{source_object}",
                destination=f"{dest_bucket}/{dest_object}",
                etag=result.etag,
                version_id=result.version_id,
            ),
        )
    except S3Error as e:
        logger.error(
            "Failed to copy '%s/%s' to '%s/%s': %s",
            source_bucket,
            source_object,
            dest_bucket,
            dest_object,
            e,
        )
        return CopyObjectResponse(success=False, error=str(e))
    except ValueError as e:
        return CopyObjectResponse(success=False, error=str(e))


# =============================================================================
# Utilities
# =============================================================================


@tool()
async def get_object_metadata(
    bucket: str, object_name: str
) -> GetObjectMetadataResponse:
    """Get metadata for an object without downloading its content.

    Retrieves object metadata including size, content type, modification time,
    ETag, and any custom user-defined metadata.

    Args:
        bucket: Name of the bucket containing the object.
        object_name: Object key/path to get metadata for.

    Returns:
        GetObjectMetadataResponse: Response containing object metadata.
            On success: success=True, data=GetObjectMetadataData(bucket, object_name, size, last_modified, etag, content_type, version_id, metadata)
            On error: success=False, error=str
    """
    if error := validate_bucket(bucket):
        return GetObjectMetadataResponse(success=False, error=error)
    if error := validate_object_name(object_name):
        return GetObjectMetadataResponse(success=False, error=error)

    try:
        client = get_client()
        stat = await run_sync(partial(client.stat_object, bucket, object_name))

        return GetObjectMetadataResponse(
            success=True,
            data=GetObjectMetadataData(
                bucket=bucket,
                object_name=object_name,
                size=stat.size,
                last_modified=stat.last_modified.isoformat()
                if stat.last_modified
                else None,
                etag=stat.etag,
                content_type=stat.content_type,
                version_id=stat.version_id,
                metadata=dict(stat.metadata) if stat.metadata else {},
            ),
        )
    except S3Error as e:
        if e.code == "NoSuchKey":
            return GetObjectMetadataResponse(
                success=False,
                error=f"Object '{object_name}' not found in bucket '{bucket}'",
            )
        logger.error("Failed to get metadata for '%s/%s': %s", bucket, object_name, e)
        return GetObjectMetadataResponse(success=False, error=str(e))
    except ValueError as e:
        return GetObjectMetadataResponse(success=False, error=str(e))


@tool()
async def get_presigned_url(
    bucket: str,
    object_name: str,
    expires_hours: int = 1,
) -> GetPresignedUrlResponse:
    """Generate a presigned URL for temporary object access.

    Creates a time-limited URL that allows downloading an object without
    authentication. Useful for sharing files temporarily or generating
    download links for end users.

    Args:
        bucket: Name of the bucket containing the object.
        object_name: Object key/path to generate URL for.
        expires_hours: URL validity period in hours. Must be between 1 and 168
            (7 days). Defaults to 1 hour.

    Returns:
        GetPresignedUrlResponse: Response containing the presigned URL.
            On success: success=True, data=GetPresignedUrlData(bucket, object_name, url, expires_in_hours)
            On error: success=False, error=str
    """
    if error := validate_bucket(bucket):
        return GetPresignedUrlResponse(success=False, error=error)
    if error := validate_object_name(object_name):
        return GetPresignedUrlResponse(success=False, error=error)

    if expires_hours < 1 or expires_hours > 168:  # Max 7 days
        return GetPresignedUrlResponse(
            success=False,
            error="expires_hours must be between 1 and 168 (7 days)",
        )

    try:
        client = get_client()

        # Verify object exists
        try:
            await run_sync(partial(client.stat_object, bucket, object_name))
        except S3Error as e:
            if e.code == "NoSuchKey":
                return GetPresignedUrlResponse(
                    success=False,
                    error=f"Object '{object_name}' not found in bucket '{bucket}'",
                )
            raise

        url = await run_sync(
            partial(
                client.presigned_get_object,
                bucket,
                object_name,
                expires=timedelta(hours=expires_hours),
            )
        )

        return GetPresignedUrlResponse(
            success=True,
            data=GetPresignedUrlData(
                bucket=bucket,
                object_name=object_name,
                url=url,
                expires_in_hours=expires_hours,
            ),
        )
    except S3Error as e:
        logger.error(
            "Failed to generate presigned URL for '%s/%s': %s", bucket, object_name, e
        )
        return GetPresignedUrlResponse(success=False, error=str(e))
    except ValueError as e:
        return GetPresignedUrlResponse(success=False, error=str(e))
