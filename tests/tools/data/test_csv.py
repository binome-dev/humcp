
import pytest

from src.tools.data.csv import (
    CSVManager,
    add_csv_file,
    describe_csv_file,
    get_csv_columns,
    get_csv_manager,
    list_csv_files,
    read_csv_file,
    remove_csv_file,
    set_csv_files,
)


@pytest.fixture
def sample_csv(tmp_path):
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text("name,age,city\nAlice,30,NYC\nBob,25,LA\nCharlie,35,Chicago\n")
    return csv_file


@pytest.fixture
def csv_manager(sample_csv):
    set_csv_files([str(sample_csv)])
    return get_csv_manager()


class TestCSVManager:
    def test_init_with_files(self, sample_csv):
        manager = CSVManager([str(sample_csv)])
        assert "sample" in manager.list_files()

    def test_init_empty(self):
        manager = CSVManager()
        assert manager.list_files() == []

    def test_get_file_path(self, sample_csv):
        manager = CSVManager([str(sample_csv)])
        assert manager.get_file_path("sample") == sample_csv

    def test_get_file_path_not_found(self):
        manager = CSVManager()
        assert manager.get_file_path("nonexistent") is None


class TestListCSVFiles:
    @pytest.mark.asyncio
    async def test_list_csv_files(self, csv_manager):
        result = await list_csv_files()
        assert result["success"] is True
        assert "sample" in result["data"]

    @pytest.mark.asyncio
    async def test_list_csv_files_empty(self):
        set_csv_files([])
        result = await list_csv_files()
        assert result["success"] is True
        assert result["count"] == 0


class TestReadCSVFile:
    @pytest.mark.asyncio
    async def test_read_csv_file(self, csv_manager):
        result = await read_csv_file("sample")
        assert result["success"] is True
        assert result["row_count"] == 3
        assert result["data"][0]["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_read_csv_file_with_limit(self, csv_manager):
        result = await read_csv_file("sample", row_limit=2)
        assert result["success"] is True
        assert result["row_count"] == 2

    @pytest.mark.asyncio
    async def test_read_csv_file_not_found(self, csv_manager):
        result = await read_csv_file("nonexistent")
        assert result["success"] is False
        assert "not found" in result["error"].lower()


class TestGetCSVColumns:
    @pytest.mark.asyncio
    async def test_get_csv_columns(self, csv_manager):
        result = await get_csv_columns("sample")
        assert result["success"] is True
        assert result["data"] == ["name", "age", "city"]
        assert result["column_count"] == 3

    @pytest.mark.asyncio
    async def test_get_csv_columns_not_found(self, csv_manager):
        result = await get_csv_columns("nonexistent")
        assert result["success"] is False


class TestDescribeCSVFile:
    @pytest.mark.asyncio
    async def test_describe_csv_file(self, csv_manager):
        result = await describe_csv_file("sample")
        assert result["success"] is True
        assert result["data"]["file_name"] == "sample"
        assert result["data"]["column_count"] == 3
        assert "sample_rows" in result["data"]

    @pytest.mark.asyncio
    async def test_describe_csv_file_not_found(self, csv_manager):
        result = await describe_csv_file("nonexistent")
        assert result["success"] is False


class TestAddCSVFile:
    @pytest.mark.asyncio
    async def test_add_csv_file(self, tmp_path):
        set_csv_files([])
        new_csv = tmp_path / "new.csv"
        new_csv.write_text("col1,col2\n1,2\n")

        result = await add_csv_file(str(new_csv))
        assert result["success"] is True
        assert result["data"]["file_name"] == "new"

    @pytest.mark.asyncio
    async def test_add_csv_file_not_found(self):
        set_csv_files([])
        result = await add_csv_file("/nonexistent/path.csv")
        assert result["success"] is False
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_add_non_csv_file(self, tmp_path):
        set_csv_files([])
        txt_file = tmp_path / "file.txt"
        txt_file.write_text("not a csv")

        result = await add_csv_file(str(txt_file))
        assert result["success"] is False
        assert "not a csv" in result["error"].lower()


class TestRemoveCSVFile:
    @pytest.mark.asyncio
    async def test_remove_csv_file(self, csv_manager):
        result = await remove_csv_file("sample")
        assert result["success"] is True

        # Verify it's removed
        list_result = await list_csv_files()
        assert "sample" not in list_result["data"]

    @pytest.mark.asyncio
    async def test_remove_csv_file_not_found(self, csv_manager):
        result = await remove_csv_file("nonexistent")
        assert result["success"] is False
