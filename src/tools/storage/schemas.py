"""Pydantic output schemas for S3-compatible storage tools."""

from pydantic import BaseModel, Field

from src.humcp.schemas import ToolResponse

# =============================================================================
# Data Models for Response Fields
# =============================================================================


class BucketInfo(BaseModel):
    """Information about a bucket."""

    name: str = Field(..., description="Bucket name")
    creation_date: str | None = Field(
        None, description="Bucket creation date in ISO format"
    )


class ObjectInfo(BaseModel):
    """Information about an object in a bucket."""

    name: str = Field(..., description="Object name/path")
    size: int | None = Field(None, description="Object size in bytes")
    last_modified: str | None = Field(
        None, description="Last modification date in ISO format"
    )
    etag: str | None = Field(None, description="Object ETag")
    is_dir: bool = Field(False, description="Whether this is a directory marker")


# =============================================================================
# Output Data Schemas (the 'data' field content)
# =============================================================================


class ListBucketsData(BaseModel):
    """Output data for list_buckets tool."""

    buckets: list[BucketInfo] = Field(..., description="List of accessible buckets")


class CreateBucketData(BaseModel):
    """Output data for create_bucket tool."""

    bucket: str = Field(..., description="Name of the created bucket")
    created: bool = Field(True, description="Whether the bucket was created")


class DeleteBucketData(BaseModel):
    """Output data for delete_bucket tool."""

    bucket: str = Field(..., description="Name of the deleted bucket")
    deleted: bool = Field(True, description="Whether the bucket was deleted")


class BucketExistsData(BaseModel):
    """Output data for bucket_exists tool."""

    bucket: str = Field(..., description="Bucket name that was checked")
    exists: bool = Field(..., description="Whether the bucket exists")


class ListObjectsData(BaseModel):
    """Output data for list_objects tool."""

    bucket: str = Field(..., description="Bucket name")
    prefix: str = Field("", description="Prefix filter used")
    recursive: bool = Field(True, description="Whether listing was recursive")
    objects: list[ObjectInfo] = Field(..., description="List of objects")
    count: int = Field(..., description="Number of objects returned")


class UploadContentData(BaseModel):
    """Output data for upload_content tool."""

    bucket: str = Field(..., description="Destination bucket name")
    object_name: str = Field(..., description="Object key/path")
    size: int = Field(..., description="Size of uploaded content in bytes")
    etag: str = Field(default="", description="ETag of the uploaded object")
    version_id: str | None = Field(
        None, description="Version ID if versioning is enabled"
    )


class UploadFromPathData(BaseModel):
    """Output data for upload_from_path tool."""

    bucket: str = Field(..., description="Destination bucket name")
    object_name: str = Field(..., description="Object key/path")
    file_path: str = Field(..., description="Source file path")
    size: int = Field(..., description="Size of uploaded file in bytes")
    etag: str = Field(default="", description="ETag of the uploaded object")
    version_id: str | None = Field(
        None, description="Version ID if versioning is enabled"
    )


class DownloadContentData(BaseModel):
    """Output data for download_content tool."""

    bucket: str = Field(..., description="Source bucket name")
    object_name: str = Field(..., description="Object key/path")
    content_base64: str = Field(..., description="Base64-encoded file content")
    size: int = Field(..., description="Size of content in bytes")
    content_type: str = Field(..., description="MIME type of the content")
    etag: str = Field(..., description="ETag of the object")


class DownloadToPathData(BaseModel):
    """Output data for download_to_path tool."""

    bucket: str = Field(..., description="Source bucket name")
    object_name: str = Field(..., description="Object key/path")
    file_path: str = Field(..., description="Destination file path")
    size: int = Field(..., description="Size of downloaded file in bytes")


class DeleteObjectData(BaseModel):
    """Output data for delete_object tool."""

    bucket: str = Field(..., description="Bucket name")
    object_name: str = Field(..., description="Deleted object key/path")
    deleted: bool = Field(True, description="Whether the object was deleted")


class CopyObjectData(BaseModel):
    """Output data for copy_object tool."""

    source: str = Field(..., description="Source path (bucket/object)")
    destination: str = Field(..., description="Destination path (bucket/object)")
    etag: str = Field(default="", description="ETag of the copied object")
    version_id: str | None = Field(
        None, description="Version ID if versioning is enabled"
    )


class GetObjectMetadataData(BaseModel):
    """Output data for get_object_metadata tool."""

    bucket: str = Field(..., description="Bucket name")
    object_name: str = Field(..., description="Object key/path")
    size: int = Field(default=0, description="Object size in bytes")
    last_modified: str | None = Field(
        None, description="Last modification date in ISO format"
    )
    etag: str = Field(default="", description="Object ETag")
    content_type: str = Field(default="", description="MIME type of the content")
    version_id: str | None = Field(None, description="Version ID")
    metadata: dict[str, str] = Field(
        default_factory=dict, description="Custom user metadata"
    )


class GetPresignedUrlData(BaseModel):
    """Output data for get_presigned_url tool."""

    bucket: str = Field(..., description="Bucket name")
    object_name: str = Field(..., description="Object key/path")
    url: str = Field(..., description="Presigned URL for downloading the object")
    expires_in_hours: int = Field(..., description="URL validity period in hours")


# =============================================================================
# Full Response Schemas (inheriting from ToolResponse[T])
# =============================================================================


class ListBucketsResponse(ToolResponse[ListBucketsData]):
    """Response schema for list_buckets tool."""

    pass


class CreateBucketResponse(ToolResponse[CreateBucketData]):
    """Response schema for create_bucket tool."""

    pass


class DeleteBucketResponse(ToolResponse[DeleteBucketData]):
    """Response schema for delete_bucket tool."""

    pass


class BucketExistsResponse(ToolResponse[BucketExistsData]):
    """Response schema for bucket_exists tool."""

    pass


class ListObjectsResponse(ToolResponse[ListObjectsData]):
    """Response schema for list_objects tool."""

    pass


class UploadContentResponse(ToolResponse[UploadContentData]):
    """Response schema for upload_content tool."""

    pass


class UploadFromPathResponse(ToolResponse[UploadFromPathData]):
    """Response schema for upload_from_path tool."""

    pass


class DownloadContentResponse(ToolResponse[DownloadContentData]):
    """Response schema for download_content tool."""

    pass


class DownloadToPathResponse(ToolResponse[DownloadToPathData]):
    """Response schema for download_to_path tool."""

    pass


class DeleteObjectResponse(ToolResponse[DeleteObjectData]):
    """Response schema for delete_object tool."""

    pass


class CopyObjectResponse(ToolResponse[CopyObjectData]):
    """Response schema for copy_object tool."""

    pass


class GetObjectMetadataResponse(ToolResponse[GetObjectMetadataData]):
    """Response schema for get_object_metadata tool."""

    pass


class GetPresignedUrlResponse(ToolResponse[GetPresignedUrlData]):
    """Response schema for get_presigned_url tool."""

    pass
