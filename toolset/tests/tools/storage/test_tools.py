"""Tests for S3-compatible storage tools."""

import base64
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from minio.error import S3Error
from src.tools.storage.tools import (
    bucket_exists,
    copy_object,
    create_bucket,
    delete_bucket,
    delete_object,
    download_content,
    download_to_path,
    get_allowed_buckets,
    get_object_metadata,
    get_presigned_url,
    list_buckets,
    list_objects,
    reset_client,
    upload_content,
    upload_from_path,
    validate_bucket,
)


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset client singleton before each test."""
    reset_client()
    yield
    reset_client()


@pytest.fixture
def mock_client():
    """Create a mock S3-compatible client."""
    client = MagicMock()
    with (
        patch("src.tools.storage.bucket_tools.get_client", return_value=client),
        patch("src.tools.storage.object_tools.get_client", return_value=client),
        patch("src.tools.storage.metadata_tools.get_client", return_value=client),
    ):
        yield client


@pytest.fixture
def mock_env_no_allowlist(monkeypatch):
    """Set up environment without allowlist."""
    monkeypatch.setenv("STORAGE_ENDPOINT", "localhost:9000")
    monkeypatch.setenv("STORAGE_ACCESS_KEY", "testkey")
    monkeypatch.setenv("STORAGE_SECRET_KEY", "testsecret")
    monkeypatch.delenv("STORAGE_ALLOWED_BUCKETS", raising=False)


@pytest.fixture
def mock_env_with_allowlist(monkeypatch):
    """Set up environment with bucket allowlist."""
    monkeypatch.setenv("STORAGE_ENDPOINT", "localhost:9000")
    monkeypatch.setenv("STORAGE_ACCESS_KEY", "testkey")
    monkeypatch.setenv("STORAGE_SECRET_KEY", "testsecret")
    monkeypatch.setenv("STORAGE_ALLOWED_BUCKETS", "allowed-bucket,another-bucket")


# =============================================================================
# Helper Function Tests
# =============================================================================


class TestGetAllowedBuckets:
    def test_empty_when_not_set(self, mock_env_no_allowlist):
        reset_client()
        allowed = get_allowed_buckets()
        assert allowed == set()

    def test_parses_comma_separated(self, mock_env_with_allowlist):
        reset_client()
        allowed = get_allowed_buckets()
        assert allowed == {"allowed-bucket", "another-bucket"}


class TestValidateBucket:
    def test_allows_any_bucket_when_no_allowlist(self, mock_env_no_allowlist):
        reset_client()
        result = validate_bucket("any-bucket")
        assert result is None

    def test_allows_bucket_in_allowlist(self, mock_env_with_allowlist):
        reset_client()
        result = validate_bucket("allowed-bucket")
        assert result is None

    def test_rejects_bucket_not_in_allowlist(self, mock_env_with_allowlist):
        reset_client()
        result = validate_bucket("forbidden-bucket")
        assert result is not None
        assert "not in allowed list" in result


# =============================================================================
# Bucket Operations Tests
# =============================================================================


class TestListBuckets:
    @pytest.mark.asyncio
    async def test_list_buckets_success(self, mock_client, mock_env_no_allowlist):
        bucket1 = MagicMock()
        bucket1.name = "bucket1"
        bucket1.creation_date = datetime(2024, 1, 1, 12, 0, 0)

        bucket2 = MagicMock()
        bucket2.name = "bucket2"
        bucket2.creation_date = datetime(2024, 2, 1, 12, 0, 0)

        mock_client.list_buckets.return_value = [bucket1, bucket2]

        result = await list_buckets()

        assert result.success is True
        assert len(result.data.buckets) == 2
        assert result.data.buckets[0].name == "bucket1"

    @pytest.mark.asyncio
    async def test_list_buckets_filters_by_allowlist(
        self, mock_client, mock_env_with_allowlist
    ):
        reset_client()
        bucket1 = MagicMock()
        bucket1.name = "allowed-bucket"
        bucket1.creation_date = datetime(2024, 1, 1)

        bucket2 = MagicMock()
        bucket2.name = "forbidden-bucket"
        bucket2.creation_date = datetime(2024, 2, 1)

        mock_client.list_buckets.return_value = [bucket1, bucket2]

        result = await list_buckets()

        assert result.success is True
        assert len(result.data.buckets) == 1
        assert result.data.buckets[0].name == "allowed-bucket"


class TestCreateBucket:
    @pytest.mark.asyncio
    async def test_create_bucket_success(self, mock_client, mock_env_no_allowlist):
        mock_client.bucket_exists.return_value = False

        result = await create_bucket("new-bucket")

        assert result.success is True
        assert result.data.bucket == "new-bucket"
        assert result.data.created is True
        mock_client.make_bucket.assert_called_once_with("new-bucket")

    @pytest.mark.asyncio
    async def test_create_bucket_already_exists(
        self, mock_client, mock_env_no_allowlist
    ):
        mock_client.bucket_exists.return_value = True

        result = await create_bucket("existing-bucket")

        assert result.success is False
        assert "already exists" in result.error

    @pytest.mark.asyncio
    async def test_create_bucket_not_allowed(
        self, mock_client, mock_env_with_allowlist
    ):
        reset_client()
        result = await create_bucket("forbidden-bucket")

        assert result.success is False
        assert "not in allowed list" in result.error


class TestDeleteBucket:
    @pytest.mark.asyncio
    async def test_delete_bucket_success(self, mock_client, mock_env_no_allowlist):
        mock_client.bucket_exists.return_value = True

        result = await delete_bucket("my-bucket")

        assert result.success is True
        assert result.data.deleted is True
        mock_client.remove_bucket.assert_called_once_with("my-bucket")

    @pytest.mark.asyncio
    async def test_delete_bucket_not_exists(self, mock_client, mock_env_no_allowlist):
        mock_client.bucket_exists.return_value = False

        result = await delete_bucket("nonexistent-bucket")

        assert result.success is False
        assert "does not exist" in result.error


class TestBucketExists:
    @pytest.mark.asyncio
    async def test_bucket_exists_true(self, mock_client, mock_env_no_allowlist):
        mock_client.bucket_exists.return_value = True

        result = await bucket_exists("my-bucket")

        assert result.success is True
        assert result.data.exists is True

    @pytest.mark.asyncio
    async def test_bucket_exists_false(self, mock_client, mock_env_no_allowlist):
        mock_client.bucket_exists.return_value = False

        result = await bucket_exists("nonexistent-bucket")

        assert result.success is True
        assert result.data.exists is False


# =============================================================================
# Object Listing Tests
# =============================================================================


class TestListObjects:
    @pytest.mark.asyncio
    async def test_list_objects_success(self, mock_client, mock_env_no_allowlist):
        mock_client.bucket_exists.return_value = True

        obj1 = MagicMock()
        obj1.object_name = "file1.txt"
        obj1.size = 1024
        obj1.last_modified = datetime(2024, 1, 1)
        obj1.etag = "abc123"
        obj1.is_dir = False

        obj2 = MagicMock()
        obj2.object_name = "folder/"
        obj2.size = 0
        obj2.last_modified = None
        obj2.etag = None
        obj2.is_dir = True

        mock_client.list_objects.return_value = [obj1, obj2]

        result = await list_objects("my-bucket", prefix="", recursive=True)

        assert result.success is True
        assert result.data.count == 2
        assert result.data.objects[0].name == "file1.txt"

    @pytest.mark.asyncio
    async def test_list_objects_bucket_not_exists(
        self, mock_client, mock_env_no_allowlist
    ):
        mock_client.bucket_exists.return_value = False

        result = await list_objects("nonexistent-bucket")

        assert result.success is False
        assert "does not exist" in result.error


# =============================================================================
# Upload Tests
# =============================================================================


class TestUploadContent:
    @pytest.mark.asyncio
    async def test_upload_content_success(self, mock_client, mock_env_no_allowlist):
        mock_client.bucket_exists.return_value = True
        mock_result = MagicMock()
        mock_result.etag = "abc123"
        mock_result.version_id = "v1"
        mock_client.put_object.return_value = mock_result

        content = base64.b64encode(b"Hello, World!").decode()
        result = await upload_content(
            bucket="my-bucket",
            object_name="test.txt",
            content_base64=content,
            content_type="text/plain",
        )

        assert result.success is True
        assert result.data.object_name == "test.txt"
        assert result.data.size == 13

    @pytest.mark.asyncio
    async def test_upload_content_invalid_base64(
        self, mock_client, mock_env_no_allowlist
    ):
        mock_client.bucket_exists.return_value = True

        result = await upload_content(
            bucket="my-bucket",
            object_name="test.txt",
            content_base64="not-valid-base64!!!",
        )

        assert result.success is False
        assert "Invalid base64" in result.error


class TestUploadFromPath:
    @pytest.mark.asyncio
    async def test_upload_from_path_success(
        self, mock_client, mock_env_no_allowlist, tmp_path
    ):
        mock_client.bucket_exists.return_value = True
        mock_result = MagicMock()
        mock_result.etag = "abc123"
        mock_result.version_id = "v1"
        mock_client.fput_object.return_value = mock_result

        # Create temp file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")

        result = await upload_from_path(
            bucket="my-bucket",
            object_name="test.txt",
            file_path=str(test_file),
        )

        assert result.success is True
        assert result.data.size == 13

    @pytest.mark.asyncio
    async def test_upload_from_path_file_not_found(
        self, mock_client, mock_env_no_allowlist
    ):
        mock_client.bucket_exists.return_value = True

        result = await upload_from_path(
            bucket="my-bucket",
            object_name="test.txt",
            file_path="/nonexistent/path/file.txt",
        )

        assert result.success is False
        assert "File not found" in result.error


# =============================================================================
# Download Tests
# =============================================================================


class TestDownloadContent:
    @pytest.mark.asyncio
    async def test_download_content_success(self, mock_client, mock_env_no_allowlist):
        response = MagicMock()
        response.read.return_value = b"Hello, World!"
        mock_client.get_object.return_value = response

        stat = MagicMock()
        stat.content_type = "text/plain"
        stat.etag = "abc123"
        mock_client.stat_object.return_value = stat

        result = await download_content(bucket="my-bucket", object_name="test.txt")

        assert result.success is True
        assert result.data.size == 13
        decoded = base64.b64decode(result.data.content_base64)
        assert decoded == b"Hello, World!"


class TestDownloadToPath:
    @pytest.mark.asyncio
    async def test_download_to_path_success(
        self, mock_client, mock_env_no_allowlist, tmp_path, monkeypatch
    ):
        # Allow absolute paths for test (temp directory is outside cwd)
        monkeypatch.setenv("STORAGE_ALLOW_ABSOLUTE_PATHS", "true")

        target_file = tmp_path / "downloaded.txt"

        def mock_fget(bucket, obj_name, path):
            with open(path, "w") as f:
                f.write("Hello, World!")

        mock_client.fget_object.side_effect = mock_fget

        result = await download_to_path(
            bucket="my-bucket",
            object_name="test.txt",
            file_path=str(target_file),
        )

        assert result.success is True
        assert result.data.file_path == str(target_file)

    @pytest.mark.asyncio
    async def test_download_to_path_rejects_traversal(
        self, mock_client, mock_env_no_allowlist
    ):
        """Test that path traversal is rejected."""
        result = await download_to_path(
            bucket="my-bucket",
            object_name="test.txt",
            file_path="../../../etc/passwd",
        )

        assert result.success is False
        assert "cannot contain '..'" in result.error

    @pytest.mark.asyncio
    async def test_download_to_path_rejects_outside_cwd(
        self, mock_client, mock_env_no_allowlist
    ):
        """Test that paths outside cwd are rejected by default."""
        result = await download_to_path(
            bucket="my-bucket",
            object_name="test.txt",
            file_path="/tmp/outside_cwd.txt",
        )

        assert result.success is False
        assert "outside allowed directory" in result.error


# =============================================================================
# Delete & Copy Tests
# =============================================================================


class TestDeleteObject:
    @pytest.mark.asyncio
    async def test_delete_object_success(self, mock_client, mock_env_no_allowlist):
        mock_client.stat_object.return_value = MagicMock()

        result = await delete_object(bucket="my-bucket", object_name="test.txt")

        assert result.success is True
        assert result.data.deleted is True
        mock_client.remove_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_object_not_found(self, mock_client, mock_env_no_allowlist):
        error = S3Error(
            code="NoSuchKey",
            message="Object not found",
            resource="test.txt",
            request_id="123",
            host_id="host",
            response=MagicMock(),
        )
        mock_client.stat_object.side_effect = error

        result = await delete_object(bucket="my-bucket", object_name="test.txt")

        assert result.success is False
        assert "not found" in result.error


class TestCopyObject:
    @pytest.mark.asyncio
    async def test_copy_object_success(self, mock_client, mock_env_no_allowlist):
        mock_client.stat_object.return_value = MagicMock()
        mock_client.bucket_exists.return_value = True

        mock_result = MagicMock()
        mock_result.etag = "abc123"
        mock_result.version_id = "v1"
        mock_client.copy_object.return_value = mock_result

        result = await copy_object(
            source_bucket="src-bucket",
            source_object="src.txt",
            dest_bucket="dest-bucket",
            dest_object="dest.txt",
        )

        assert result.success is True
        assert "src-bucket/src.txt" in result.data.source
        assert "dest-bucket/dest.txt" in result.data.destination


# =============================================================================
# Utility Tests
# =============================================================================


class TestGetObjectMetadata:
    @pytest.mark.asyncio
    async def test_get_metadata_success(self, mock_client, mock_env_no_allowlist):
        stat = MagicMock()
        stat.size = 1024
        stat.last_modified = datetime(2024, 1, 1)
        stat.etag = "abc123"
        stat.content_type = "text/plain"
        stat.version_id = "v1"
        stat.metadata = {"custom": "value"}
        mock_client.stat_object.return_value = stat

        result = await get_object_metadata(bucket="my-bucket", object_name="test.txt")

        assert result.success is True
        assert result.data.size == 1024
        assert result.data.content_type == "text/plain"


class TestGetPresignedUrl:
    @pytest.mark.asyncio
    async def test_presigned_url_success(self, mock_client, mock_env_no_allowlist):
        mock_client.stat_object.return_value = MagicMock()
        mock_client.presigned_get_object.return_value = "https://example.com/presigned"

        result = await get_presigned_url(
            bucket="my-bucket",
            object_name="test.txt",
            expires_hours=24,
        )

        assert result.success is True
        assert result.data.url == "https://example.com/presigned"
        assert result.data.expires_in_hours == 24

    @pytest.mark.asyncio
    async def test_presigned_url_invalid_expiry(
        self, mock_client, mock_env_no_allowlist
    ):
        result = await get_presigned_url(
            bucket="my-bucket",
            object_name="test.txt",
            expires_hours=200,  # > 168 (7 days)
        )

        assert result.success is False
        assert "between 1 and 168" in result.error
