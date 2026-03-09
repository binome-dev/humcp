"""Tests for storage path utilities."""

import pytest
from src.humcp.storage_path import (
    get_storage_path,
    is_storage_path,
    parse_storage_path,
)


class TestIsStoragePath:
    def test_storage_url(self):
        assert is_storage_path("minio://bucket/path/to/file.csv") is True

    def test_storage_url_simple(self):
        assert is_storage_path("minio://bucket/file.csv") is True

    def test_local_path(self):
        assert is_storage_path("/path/to/file.csv") is False

    def test_relative_path(self):
        assert is_storage_path("file.csv") is False

    def test_s3_url_not_storage(self):
        assert is_storage_path("s3://bucket/file.csv") is False

    def test_http_url_not_storage(self):
        assert is_storage_path("http://example.com/file.csv") is False


class TestParseStoragePath:
    def test_simple_path(self):
        bucket, object_name = parse_storage_path("minio://my-bucket/file.csv")
        assert bucket == "my-bucket"
        assert object_name == "file.csv"

    def test_nested_path(self):
        bucket, object_name = parse_storage_path("minio://datasets/data/2024/sales.csv")
        assert bucket == "datasets"
        assert object_name == "data/2024/sales.csv"

    def test_path_with_special_chars(self):
        bucket, object_name = parse_storage_path(
            "minio://my-bucket/path/file-name_v2.csv"
        )
        assert bucket == "my-bucket"
        assert object_name == "path/file-name_v2.csv"

    def test_not_storage_path_raises(self):
        with pytest.raises(ValueError, match="Not a storage path"):
            parse_storage_path("/local/path/file.csv")

    def test_no_bucket_raises(self):
        with pytest.raises(ValueError, match="no bucket"):
            parse_storage_path("minio:///file.csv")

    def test_no_object_raises(self):
        with pytest.raises(ValueError, match="no object"):
            parse_storage_path("minio://bucket/")

    def test_bucket_only_raises(self):
        with pytest.raises(ValueError, match="no object"):
            parse_storage_path("minio://bucket")


class TestGetStoragePath:
    def test_simple(self):
        path = get_storage_path("my-bucket", "file.csv")
        assert path == "minio://my-bucket/file.csv"

    def test_nested(self):
        path = get_storage_path("datasets", "data/2024/sales.csv")
        assert path == "minio://datasets/data/2024/sales.csv"

    def test_roundtrip(self):
        original = "minio://my-bucket/path/to/file.csv"
        bucket, object_name = parse_storage_path(original)
        reconstructed = get_storage_path(bucket, object_name)
        assert reconstructed == original
