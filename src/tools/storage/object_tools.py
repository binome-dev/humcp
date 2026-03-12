"""Object operations for S3-compatible object storage.

This module provides tools for listing, uploading, downloading, deleting,
and copying objects in S3-compatible storage buckets.
"""

import base64
import io
import logging
from functools import partial
from pathlib import Path

from minio.commonconfig import CopySource
from minio.error import S3Error

from src.humcp.decorator import tool
from src.humcp.permissions import check_permission
from src.tools.storage.client import (
    get_client,
    run_sync,
    validate_bucket,
    validate_local_path,
    validate_object_name,
)
from src.tools.storage.schemas import (
    CopyObjectData,
    CopyObjectResponse,
    DeleteObjectData,
    DeleteObjectResponse,
    DownloadContentData,
    DownloadContentResponse,
    DownloadToPathData,
    DownloadToPathResponse,
    ListObjectsData,
    ListObjectsResponse,
    ObjectInfo,
    UploadContentData,
    UploadContentResponse,
    UploadFromPathData,
    UploadFromPathResponse,
)

logger = logging.getLogger(__name__)


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
        await check_permission("storage_bucket", bucket, "viewer")

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
    """Upload base64-encoded content to storage.

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
        await check_permission("storage_bucket", bucket, "editor")

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
                etag=result.etag or "",
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
    """Upload a file from the local filesystem to storage.

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
    if error := validate_local_path(file_path):
        return UploadFromPathResponse(success=False, error=error)

    try:
        await check_permission("storage_bucket", bucket, "editor")

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
                etag=result.etag or "",
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
        await check_permission("storage_bucket", bucket, "viewer")

        client = get_client()

        # Get object content and metadata in thread pool
        def _download() -> tuple[bytes, str | None, str | None]:
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
                content_type=content_type_val or "",
                etag=etag or "",
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

    Downloads an object from storage and saves it to the specified path.
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
        await check_permission("storage_bucket", bucket, "viewer")

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
        await check_permission("storage_bucket", bucket, "editor")

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
    STORAGE_ALLOWED_BUCKETS is configured. The copy is performed server-side.

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
        await check_permission("storage_bucket", source_bucket, "viewer")
        await check_permission("storage_bucket", dest_bucket, "editor")

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
                etag=result.etag or "",
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
