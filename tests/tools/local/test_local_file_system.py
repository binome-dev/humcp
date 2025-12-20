import pytest

from src.tools.local.local_file_system import (
    append_to_file,
    copy_file,
    create_directory,
    delete_file,
    file_exists,
    get_file_info,
    list_files,
    read_file,
    write_file,
)


class TestWriteFile:
    @pytest.mark.asyncio
    async def test_write_file_basic(self, tmp_path):
        result = await write_file(
            content="Hello, World!", filename="test.txt", directory=str(tmp_path)
        )
        assert result["success"] is True
        assert (tmp_path / "test.txt").exists()
        assert (tmp_path / "test.txt").read_text() == "Hello, World!"

    @pytest.mark.asyncio
    async def test_write_file_with_extension(self, tmp_path):
        result = await write_file(
            content="data", filename="myfile", directory=str(tmp_path), extension="json"
        )
        assert result["success"] is True
        assert (tmp_path / "myfile.json").exists()


class TestReadFile:
    @pytest.mark.asyncio
    async def test_read_file_exists(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")

        result = await read_file(filename="test.txt", directory=str(tmp_path))
        assert result["success"] is True
        assert result["data"]["content"] == "Hello, World!"

    @pytest.mark.asyncio
    async def test_read_file_not_found(self, tmp_path):
        result = await read_file(filename="nonexistent.txt", directory=str(tmp_path))
        assert result["success"] is False
        assert "not found" in result["error"].lower()


class TestListFiles:
    @pytest.mark.asyncio
    async def test_list_files_basic(self, tmp_path):
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.txt").write_text("content2")

        result = await list_files(directory=str(tmp_path))
        assert result["success"] is True
        assert result["count"] == 2

    @pytest.mark.asyncio
    async def test_list_files_with_pattern(self, tmp_path):
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.py").write_text("content2")

        result = await list_files(directory=str(tmp_path), pattern="*.txt")
        assert result["success"] is True
        assert result["count"] == 1

    @pytest.mark.asyncio
    async def test_list_files_empty_dir(self, tmp_path):
        result = await list_files(directory=str(tmp_path))
        assert result["success"] is True
        assert result["count"] == 0


class TestDeleteFile:
    @pytest.mark.asyncio
    async def test_delete_file_exists(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        result = await delete_file(filename="test.txt", directory=str(tmp_path))
        assert result["success"] is True
        assert not test_file.exists()

    @pytest.mark.asyncio
    async def test_delete_file_not_found(self, tmp_path):
        result = await delete_file(filename="nonexistent.txt", directory=str(tmp_path))
        assert result["success"] is False


class TestCreateDirectory:
    @pytest.mark.asyncio
    async def test_create_directory_basic(self, tmp_path):
        new_dir = tmp_path / "new_folder"
        result = await create_directory(directory=str(new_dir))
        assert result["success"] is True
        assert new_dir.exists()

    @pytest.mark.asyncio
    async def test_create_directory_already_exists(self, tmp_path):
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()

        result = await create_directory(directory=str(existing_dir))
        assert result["success"] is False
        assert "already exists" in result["error"].lower()


class TestFileExists:
    @pytest.mark.asyncio
    async def test_file_exists_true(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        result = await file_exists(filename="test.txt", directory=str(tmp_path))
        assert result["success"] is True
        assert result["data"]["exists"] is True

    @pytest.mark.asyncio
    async def test_file_exists_false(self, tmp_path):
        result = await file_exists(filename="nonexistent.txt", directory=str(tmp_path))
        assert result["success"] is True
        assert result["data"]["exists"] is False


class TestGetFileInfo:
    @pytest.mark.asyncio
    async def test_get_file_info_exists(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello!")

        result = await get_file_info(filename="test.txt", directory=str(tmp_path))
        assert result["success"] is True
        assert result["data"]["size_bytes"] == 6
        assert result["data"]["extension"] == "txt"

    @pytest.mark.asyncio
    async def test_get_file_info_not_found(self, tmp_path):
        result = await get_file_info(
            filename="nonexistent.txt", directory=str(tmp_path)
        )
        assert result["success"] is False


class TestAppendToFile:
    @pytest.mark.asyncio
    async def test_append_to_file(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello")

        result = await append_to_file(
            content=", World!", filename="test.txt", directory=str(tmp_path)
        )
        assert result["success"] is True
        assert test_file.read_text() == "Hello, World!"

    @pytest.mark.asyncio
    async def test_append_to_nonexistent_file(self, tmp_path):
        result = await append_to_file(
            content="data", filename="nonexistent.txt", directory=str(tmp_path)
        )
        assert result["success"] is False


class TestCopyFile:
    @pytest.mark.asyncio
    async def test_copy_file_basic(self, tmp_path):
        source = tmp_path / "source.txt"
        source.write_text("content")

        result = await copy_file(
            source_filename="source.txt",
            destination_filename="dest.txt",
            source_directory=str(tmp_path),
            destination_directory=str(tmp_path),
        )
        assert result["success"] is True
        assert (tmp_path / "dest.txt").exists()
        assert (tmp_path / "dest.txt").read_text() == "content"

    @pytest.mark.asyncio
    async def test_copy_file_source_not_found(self, tmp_path):
        result = await copy_file(
            source_filename="nonexistent.txt",
            destination_filename="dest.txt",
            source_directory=str(tmp_path),
            destination_directory=str(tmp_path),
        )
        assert result["success"] is False
