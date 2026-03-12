"""Metadata and utility operations for S3-compatible object storage.

This module provides tools for retrieving object metadata and generating
presigned URLs for temporary object access.
"""

import logging
from datetime import timedelta
from functools import partial

from minio.error import S3Error

from src.humcp.decorator import tool
from src.humcp.permissions import check_permission
from src.tools.storage.client import (
    get_client,
    run_sync,
    validate_bucket,
    validate_object_name,
)
from src.tools.storage.schemas import (
    GetObjectMetadataData,
    GetObjectMetadataResponse,
    GetPresignedUrlData,
    GetPresignedUrlResponse,
)

logger = logging.getLogger(__name__)


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
        await check_permission("storage_bucket", bucket, "viewer")

        client = get_client()
        stat = await run_sync(partial(client.stat_object, bucket, object_name))

        return GetObjectMetadataResponse(
            success=True,
            data=GetObjectMetadataData(
                bucket=bucket,
                object_name=object_name,
                size=stat.size or 0,
                last_modified=stat.last_modified.isoformat()
                if stat.last_modified
                else None,
                etag=stat.etag or "",
                content_type=stat.content_type or "",
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
        await check_permission("storage_bucket", bucket, "viewer")

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
