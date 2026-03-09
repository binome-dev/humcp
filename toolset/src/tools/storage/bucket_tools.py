"""Bucket operations for S3-compatible object storage.

This module provides tools for creating, deleting, listing, and checking
the existence of buckets in S3-compatible storage.
"""

import logging
from functools import partial

from minio.error import S3Error

from src.humcp.decorator import tool
from src.humcp.permissions import check_permission, require_auth
from src.tools.storage.client import (
    get_allowed_buckets,
    get_client,
    run_sync,
    validate_bucket,
)
from src.tools.storage.schemas import (
    BucketExistsData,
    BucketExistsResponse,
    BucketInfo,
    CreateBucketData,
    CreateBucketResponse,
    DeleteBucketData,
    DeleteBucketResponse,
    ListBucketsData,
    ListBucketsResponse,
)

logger = logging.getLogger(__name__)


@tool()
async def list_buckets() -> ListBucketsResponse:
    """List all accessible buckets in storage.

    Retrieves all buckets visible to the configured credentials. If
    STORAGE_ALLOWED_BUCKETS is set, only those buckets are included in the result.

    Returns:
        ListBucketsResponse: Response containing bucket list.
            On success: success=True, data=ListBucketsData(buckets=[...])
            On error: success=False, error=str
    """
    try:
        await require_auth()

        client = get_client()
        # Run sync S3 call in thread pool to avoid blocking event loop
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
    """Create a new bucket in storage.

    Creates a bucket with the specified name. The bucket must be in the
    allowed list if STORAGE_ALLOWED_BUCKETS is configured.

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
        await require_auth()

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
    """Delete an empty bucket from storage.

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
        await check_permission("storage_bucket", bucket, "owner")

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
    """Check if a bucket exists in storage.

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
        await check_permission("storage_bucket", bucket, "viewer")

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
