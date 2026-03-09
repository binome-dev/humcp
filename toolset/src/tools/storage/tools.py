"""S3-compatible object storage tools.

This module re-exports all storage tools and client utilities from their
respective sub-modules for backward compatibility. New code should import
directly from the specific sub-modules:

- ``src.tools.storage.client`` - MinIO client setup and validation
- ``src.tools.storage.bucket_tools`` - Bucket operations
- ``src.tools.storage.object_tools`` - Object operations (list, upload, download, delete, copy)
- ``src.tools.storage.metadata_tools`` - Metadata and presigned URL operations

Environment Variables:
    STORAGE_ENDPOINT: Storage server address (default: "minio:9000")
    STORAGE_ACCESS_KEY: Access key for authentication (required)
    STORAGE_SECRET_KEY: Secret key for authentication (required)
    STORAGE_SECURE: Use HTTPS connection (default: "false")
    STORAGE_REGION: Region for the storage service (optional, needed for AWS S3/GCS)
    STORAGE_ALLOWED_BUCKETS: Comma-separated list of allowed bucket names (optional)

Example:
    >>> result = await list_buckets()
    >>> if result.success:
    ...     for bucket in result.data.buckets:
    ...         print(bucket.name)
"""

# Client utilities
# Bucket operations
from src.tools.storage.bucket_tools import (
    bucket_exists,
    create_bucket,
    delete_bucket,
    list_buckets,
)
from src.tools.storage.client import (
    get_allowed_buckets,
    get_client,
    reset_client,
    run_sync,
    validate_bucket,
    validate_local_path,
    validate_object_name,
)

# Metadata operations
from src.tools.storage.metadata_tools import (
    get_object_metadata,
    get_presigned_url,
)

# Object operations
from src.tools.storage.object_tools import (
    copy_object,
    delete_object,
    download_content,
    download_to_path,
    list_objects,
    upload_content,
    upload_from_path,
)

__all__ = [
    # Client utilities
    "get_allowed_buckets",
    "get_client",
    "reset_client",
    "run_sync",
    "validate_bucket",
    "validate_local_path",
    "validate_object_name",
    # Bucket operations
    "bucket_exists",
    "create_bucket",
    "delete_bucket",
    "list_buckets",
    # Object operations
    "copy_object",
    "delete_object",
    "download_content",
    "download_to_path",
    "list_objects",
    "upload_content",
    "upload_from_path",
    # Metadata operations
    "get_object_metadata",
    "get_presigned_url",
]
