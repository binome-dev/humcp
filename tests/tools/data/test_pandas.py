import pandas as pd
import pytest

import src.tools.data.pandas as pandas_module
from src.tools.data.pandas import (
    DataFrameManager,
    create_pandas_dataframe,
    delete_dataframe,
    get_dataframe_info,
    list_dataframes,
    run_dataframe_operation,
)


@pytest.fixture
def reset_manager():
    pandas_module._dataframe_manager = None
    yield
    pandas_module._dataframe_manager = None


class TestDataFrameManager:
    def test_add_and_get_dataframe(self):
        manager = DataFrameManager()
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})

        manager.add_dataframe("test", df)
        result = manager.get_dataframe("test")

        assert result is not None
        assert list(result.columns) == ["a", "b"]

    def test_get_nonexistent_dataframe(self):
        manager = DataFrameManager()
        result = manager.get_dataframe("nonexistent")
        assert result is None

    def test_remove_dataframe(self):
        manager = DataFrameManager()
        df = pd.DataFrame({"a": [1]})
        manager.add_dataframe("test", df)

        assert manager.remove_dataframe("test") is True
        assert manager.get_dataframe("test") is None

    def test_list_dataframes(self):
        manager = DataFrameManager()
        manager.add_dataframe("df1", pd.DataFrame({"a": [1]}))
        manager.add_dataframe("df2", pd.DataFrame({"b": [2]}))

        result = manager.list_dataframes()
        assert "df1" in result
        assert "df2" in result

    def test_dataframe_exists(self):
        manager = DataFrameManager()
        manager.add_dataframe("test", pd.DataFrame({"a": [1]}))

        assert manager.dataframe_exists("test") is True
        assert manager.dataframe_exists("nonexistent") is False


class TestCreatePandasDataframe:
    @pytest.mark.asyncio
    async def test_create_from_dict(self, reset_manager):
        result = await create_pandas_dataframe(
            dataframe_name="test_df",
            create_using_function="DataFrame",
            function_parameters={"data": {"col1": [1, 2], "col2": [3, 4]}},
        )
        assert result["success"] is True
        assert result["data"]["name"] == "test_df"
        assert result["data"]["shape"] == (2, 2)

    @pytest.mark.asyncio
    async def test_create_duplicate_name(self, reset_manager):
        await create_pandas_dataframe(
            dataframe_name="test_df",
            create_using_function="DataFrame",
            function_parameters={"data": {"a": [1]}},
        )

        result = await create_pandas_dataframe(
            dataframe_name="test_df",
            create_using_function="DataFrame",
            function_parameters={"data": {"b": [2]}},
        )
        assert result["success"] is False
        assert "already exists" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_create_invalid_function(self, reset_manager):
        result = await create_pandas_dataframe(
            dataframe_name="test_df",
            create_using_function="nonexistent_function",
            function_parameters={},
        )
        assert result["success"] is False
        assert "does not exist" in result["error"].lower()


class TestRunDataframeOperation:
    @pytest.mark.asyncio
    async def test_head_operation(self, reset_manager):
        await create_pandas_dataframe(
            dataframe_name="test_df",
            create_using_function="DataFrame",
            function_parameters={"data": {"a": [1, 2, 3, 4, 5]}},
        )

        result = await run_dataframe_operation(
            dataframe_name="test_df", operation="head", operation_parameters={"n": 2}
        )
        assert result["success"] is True
        assert "result" in result["data"]

    @pytest.mark.asyncio
    async def test_operation_on_nonexistent_df(self, reset_manager):
        result = await run_dataframe_operation(
            dataframe_name="nonexistent", operation="head"
        )
        assert result["success"] is False
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_invalid_operation(self, reset_manager):
        await create_pandas_dataframe(
            dataframe_name="test_df",
            create_using_function="DataFrame",
            function_parameters={"data": {"a": [1]}},
        )

        result = await run_dataframe_operation(
            dataframe_name="test_df", operation="nonexistent_operation"
        )
        assert result["success"] is False


class TestListDataframes:
    @pytest.mark.asyncio
    async def test_list_dataframes_empty(self, reset_manager):
        result = await list_dataframes()
        assert result["success"] is True
        assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_list_dataframes_with_data(self, reset_manager):
        await create_pandas_dataframe(
            dataframe_name="df1",
            create_using_function="DataFrame",
            function_parameters={"data": {"a": [1]}},
        )
        await create_pandas_dataframe(
            dataframe_name="df2",
            create_using_function="DataFrame",
            function_parameters={"data": {"b": [2]}},
        )

        result = await list_dataframes()
        assert result["success"] is True
        assert result["count"] == 2


class TestGetDataframeInfo:
    @pytest.mark.asyncio
    async def test_get_info(self, reset_manager):
        await create_pandas_dataframe(
            dataframe_name="test_df",
            create_using_function="DataFrame",
            function_parameters={"data": {"col1": [1, 2], "col2": ["a", "b"]}},
        )

        result = await get_dataframe_info("test_df")
        assert result["success"] is True
        assert result["data"]["name"] == "test_df"
        assert "columns" in result["data"]
        assert "dtypes" in result["data"]

    @pytest.mark.asyncio
    async def test_get_info_not_found(self, reset_manager):
        result = await get_dataframe_info("nonexistent")
        assert result["success"] is False


class TestDeleteDataframe:
    @pytest.mark.asyncio
    async def test_delete_dataframe(self, reset_manager):
        await create_pandas_dataframe(
            dataframe_name="test_df",
            create_using_function="DataFrame",
            function_parameters={"data": {"a": [1]}},
        )

        result = await delete_dataframe("test_df")
        assert result["success"] is True

        # Verify deletion
        list_result = await list_dataframes()
        assert list_result["count"] == 0

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, reset_manager):
        result = await delete_dataframe("nonexistent")
        assert result["success"] is False
