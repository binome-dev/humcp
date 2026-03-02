---
name: storage
description: Use these tools for S3-compatible object storage operations with MinIO
---

# Storage Tools (MinIO)

Tools for interacting with MinIO S3-compatible object storage. Use these for file uploads, downloads, and bucket management.

## Configuration

Set these environment variables:

```bash
MINIO_ENDPOINT=minio:9000        # MinIO server address
MINIO_ACCESS_KEY=minioadmin      # Access key (required)
MINIO_SECRET_KEY=minioadmin      # Secret key (required)
MINIO_SECURE=false               # Use HTTPS (true/false)
MINIO_ALLOWED_BUCKETS=bucket1,bucket2  # Comma-separated allowlist
```

## Security

All bucket operations validate against `MINIO_ALLOWED_BUCKETS`. If set, only those buckets can be accessed.

## Available Tools

### Bucket Operations

| Tool | Description |
|------|-------------|
| `list_buckets` | List all accessible buckets |
| `create_bucket` | Create a new bucket |
| `delete_bucket` | Delete an empty bucket |
| `bucket_exists` | Check if a bucket exists |

### Object Listing

| Tool | Description |
|------|-------------|
| `list_objects` | List objects with optional prefix filter |

### Upload

| Tool | Description |
|------|-------------|
| `upload_content` | Upload base64-encoded content |
| `upload_from_path` | Upload from local file path |

### Download

| Tool | Description |
|------|-------------|
| `download_content` | Download as base64-encoded content |
| `download_to_path` | Download to local file path |

### Delete & Copy

| Tool | Description |
|------|-------------|
| `delete_object` | Delete an object |
| `copy_object` | Copy object between buckets |

### Utilities

| Tool | Description |
|------|-------------|
| `get_object_metadata` | Get object size, type, and metadata |
| `get_presigned_url` | Generate temporary download URL |

## Usage Examples

### Upload a file

```python
# From base64 content
result = await upload_content(
    bucket="my-bucket",
    object_name="documents/report.pdf",
    content_base64="JVBERi0xLjQK...",
    content_type="application/pdf"
)

# From local path
result = await upload_from_path(
    bucket="my-bucket",
    object_name="images/photo.jpg",
    file_path="/tmp/photo.jpg",
    content_type="image/jpeg"
)
```

### Download a file

```python
# To base64 (for small files)
result = await download_content(bucket="my-bucket", object_name="doc.pdf")
content = base64.b64decode(result["data"]["content_base64"])

# To local path (for large files)
result = await download_to_path(
    bucket="my-bucket",
    object_name="video.mp4",
    file_path="/tmp/video.mp4"
)
```

### List objects with prefix

```python
result = await list_objects(
    bucket="my-bucket",
    prefix="documents/2024/",
    recursive=True
)
# Returns all objects under documents/2024/
```

### Generate presigned URL

```python
result = await get_presigned_url(
    bucket="my-bucket",
    object_name="private/report.pdf",
    expires_hours=24
)
# Share result["data"]["url"] for temporary access
```

## Response Format

All tools return a standardized response:

```python
# Success
{"success": True, "data": {...}}

# Error
{"success": False, "error": "Error message"}
```

## When to Use

- **upload_content**: Small files (<10MB), content already in memory
- **upload_from_path**: Large files, files on disk
- **download_content**: Small files, need content in memory
- **download_to_path**: Large files, need to save to disk
- **get_presigned_url**: Share temporary access without exposing credentials