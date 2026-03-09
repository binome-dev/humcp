"""CSV file tools with DuckDB query support.

Security Note:
    The query_csv_file tool only allows SELECT queries for safety.
    All queries are validated before execution.

Supports both local file paths and storage URLs:
    - Local: /path/to/file.csv
    - storage: minio://bucket/path/to/file.csv
"""

import csv as csv_lib
import logging
import re
import threading
from pathlib import Path

from src.humcp.decorator import tool
from src.humcp.permissions import check_permission, require_auth
from src.humcp.storage_path import is_storage_path, parse_storage_path, resolve_path
from src.tools.data.schemas import (
    AddCSVFileData,
    AddCSVFileResponse,
    DescribeCSVFileData,
    DescribeCSVFileResponse,
    GetCSVColumnsData,
    GetCSVColumnsResponse,
    ListCSVFilesData,
    ListCSVFilesResponse,
    QueryCSVFileData,
    QueryCSVFileResponse,
    ReadCSVFileData,
    ReadCSVFileResponse,
    RemoveCSVFileData,
    RemoveCSVFileResponse,
)

logger = logging.getLogger("humcp.tools.csv")

# Allowed SQL operations (read-only)
_ALLOWED_SQL_PATTERN = re.compile(
    r"^\s*SELECT\s+.+\s+FROM\s+",
    re.IGNORECASE | re.DOTALL,
)

# Disallowed SQL keywords that could modify data or execute dangerous operations
_DISALLOWED_KEYWORDS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE|EXEC|EXECUTE|"
    r"ATTACH|DETACH|COPY|LOAD|INSTALL|PRAGMA)\b",
    re.IGNORECASE,
)

try:
    import duckdb

    DUCKDB_AVAILABLE = True
except ImportError:
    DUCKDB_AVAILABLE = False


class CSVManager:
    """Manages CSV files from both local filesystem and storage storage.

    Supports paths in two formats:
        - Local: /path/to/file.csv
        - storage: minio://bucket/path/to/file.csv
    """

    def __init__(self, csv_files: list[str] | None = None):
        self.csv_files: list[str] = []  # Original paths (local or minio://)
        self.csv_map: dict[str, str] = {}  # name -> original path
        if csv_files:
            for file_path in csv_files:
                self._add_file(file_path)

    def _add_file(self, file_path: str) -> str | None:
        """Add a file to the manager. Returns the file name or None if invalid."""
        if is_storage_path(file_path):
            # storage path - extract name from object path
            try:
                _, object_name = parse_storage_path(file_path)
                name = Path(object_name).stem
                if not object_name.lower().endswith(".csv"):
                    return None
                self.csv_files.append(file_path)
                self.csv_map[name] = file_path
                return name
            except ValueError:
                return None
        else:
            # Local path
            path = Path(file_path)
            if path.exists() and path.suffix.lower() == ".csv":
                self.csv_files.append(file_path)
                self.csv_map[path.stem] = file_path
                return path.stem
        return None

    def get_file_path(self, csv_name: str) -> str | None:
        """Get the original path (local or minio://) for a CSV file."""
        return self.csv_map.get(csv_name)

    def list_files(self) -> list[str]:
        """List all registered CSV file names."""
        return list(self.csv_map.keys())

    def get_file_info(self, csv_name: str) -> dict | None:
        """Get info about a CSV file including whether it's from storage."""
        path = self.csv_map.get(csv_name)
        if not path:
            return None
        return {
            "name": csv_name,
            "path": path,
            "is_remote": is_storage_path(path),
        }


_csv_manager = None
_csv_manager_lock = threading.Lock()


def get_csv_manager():
    """Get the CSVManager singleton with thread-safe lazy initialization."""
    global _csv_manager
    if _csv_manager is None:
        with _csv_manager_lock:
            # Double-checked locking pattern for thread safety
            if _csv_manager is None:
                _csv_manager = CSVManager()
    return _csv_manager


def set_csv_files(csv_files: list):
    """Set the CSV files for the manager. Thread-safe."""
    global _csv_manager
    with _csv_manager_lock:
        _csv_manager = CSVManager(csv_files)


@tool()
async def list_csv_files() -> ListCSVFilesResponse:
    """List all available CSV files."""
    try:
        await require_auth()

        manager = get_csv_manager()
        files = manager.list_files()
        logger.info("Listing CSV files count=%d", len(files))
        return ListCSVFilesResponse(
            success=True,
            data=ListCSVFilesData(files=files, count=len(files)),
        )
    except Exception as e:
        logger.exception("Failed to list CSV files")
        return ListCSVFilesResponse(success=False, error=str(e))


@tool()
async def read_csv_file(
    csv_name: str, row_limit: int | None = None
) -> ReadCSVFileResponse:
    """Read contents of a CSV file.

    Supports files from both local filesystem and storage storage.
    """
    try:
        await require_auth()

        manager = get_csv_manager()
        original_path = manager.get_file_path(csv_name)
        if not original_path:
            return ReadCSVFileResponse(
                success=False, error=f"CSV '{csv_name}' not found"
            )
        logger.info("Reading CSV file name=%s limit=%s", csv_name, row_limit)

        rows = []
        async with resolve_path(original_path) as local_path:
            with open(local_path, encoding="utf-8") as f:
                reader = csv_lib.DictReader(f)
                for i, row in enumerate(reader):
                    if row_limit and i >= row_limit:
                        break
                    rows.append(row)

        return ReadCSVFileResponse(
            success=True,
            data=ReadCSVFileData(rows=rows, row_count=len(rows)),
        )
    except Exception as e:
        logger.exception("Failed to read CSV file name=%s", csv_name)
        return ReadCSVFileResponse(success=False, error=str(e))


@tool()
async def get_csv_columns(csv_name: str) -> GetCSVColumnsResponse:
    """Get column names from a CSV file.

    Supports files from both local filesystem and storage storage.
    """
    try:
        await require_auth()

        manager = get_csv_manager()
        original_path = manager.get_file_path(csv_name)
        if not original_path:
            return GetCSVColumnsResponse(
                success=False, error=f"CSV '{csv_name}' not found"
            )
        logger.info("Getting CSV columns name=%s", csv_name)

        async with resolve_path(original_path) as local_path:
            with open(local_path, encoding="utf-8") as f:
                reader = csv_lib.DictReader(f)
                columns = list(reader.fieldnames or [])

        return GetCSVColumnsResponse(
            success=True,
            data=GetCSVColumnsData(columns=columns, column_count=len(columns)),
        )
    except Exception as e:
        logger.exception("Failed to get CSV columns name=%s", csv_name)
        return GetCSVColumnsResponse(success=False, error=str(e))


def _validate_sql_query(query: str) -> tuple[bool, str]:
    """Validate SQL query for safety.

    Args:
        query: SQL query to validate.

    Returns:
        Tuple of (is_valid, error_message).
    """
    # Check for disallowed keywords
    if _DISALLOWED_KEYWORDS.search(query):
        return False, "Query contains disallowed SQL keywords (only SELECT allowed)"

    # Check if query starts with SELECT
    if not _ALLOWED_SQL_PATTERN.match(query):
        return False, "Only SELECT queries are allowed"

    return True, ""


@tool()
async def query_csv_file(csv_name: str, sql_query: str) -> QueryCSVFileResponse:
    """Execute SQL query on CSV file using DuckDB.

    Supports files from both local filesystem and storage storage.

    Security: Only SELECT queries are allowed. Queries with INSERT, UPDATE,
    DELETE, DROP, or other data-modifying statements will be rejected.
    """
    try:
        await require_auth()

        if not DUCKDB_AVAILABLE:
            return QueryCSVFileResponse(
                success=False, error="DuckDB required: pip install duckdb"
            )

        manager = get_csv_manager()
        original_path = manager.get_file_path(csv_name)
        if not original_path:
            return QueryCSVFileResponse(
                success=False, error=f"CSV '{csv_name}' not found"
            )

        # Sanitize and validate query
        query = sql_query.strip().split(";")[0]  # Only first statement
        is_valid, error_msg = _validate_sql_query(query)
        if not is_valid:
            logger.warning("SQL query rejected name=%s reason=%s", csv_name, error_msg)
            return QueryCSVFileResponse(success=False, error=error_msg)

        logger.info("Querying CSV file name=%s", csv_name)

        async with resolve_path(original_path) as local_path:
            # Use parameterized table creation with sanitized table name
            safe_table_name = re.sub(r"[^a-zA-Z0-9_]", "_", csv_name)
            conn = duckdb.connect(":memory:")
            try:
                # Set query timeout to prevent long-running queries (30 seconds)
                conn.execute("SET timeout='30s'")

                conn.execute(
                    f"CREATE TABLE {safe_table_name} AS SELECT * FROM read_csv_auto(?)",
                    [str(local_path)],
                )
                # Replace table name in query
                query = re.sub(
                    rf"\b{re.escape(csv_name)}\b",
                    safe_table_name,
                    query,
                    flags=re.IGNORECASE,
                )
                result = conn.execute(query).fetchall()
                columns = [desc[0] for desc in conn.description]
                rows = [dict(zip(columns, row, strict=False)) for row in result]
            finally:
                conn.close()

        return QueryCSVFileResponse(
            success=True,
            data=QueryCSVFileData(rows=rows, row_count=len(rows), columns=columns),
        )
    except Exception as e:
        logger.exception("Failed to query CSV file name=%s", csv_name)
        return QueryCSVFileResponse(success=False, error=str(e))


@tool()
async def describe_csv_file(csv_name: str) -> DescribeCSVFileResponse:
    """Get detailed information about a CSV file.

    Supports files from both local filesystem and storage storage.
    """
    try:
        await require_auth()

        manager = get_csv_manager()
        original_path = manager.get_file_path(csv_name)
        if not original_path:
            return DescribeCSVFileResponse(
                success=False, error=f"CSV '{csv_name}' not found"
            )
        logger.info("Describing CSV file name=%s", csv_name)

        async with resolve_path(original_path) as local_path:
            file_size = Path(local_path).stat().st_size
            rows = []

            with open(local_path, encoding="utf-8") as f:
                reader = csv_lib.DictReader(f)
                columns = list(reader.fieldnames or [])
                row_count = 0
                for i, row in enumerate(reader):
                    if i < 5:
                        rows.append(row)
                    row_count = i + 1
                    if i >= 1000:
                        break

        return DescribeCSVFileResponse(
            success=True,
            data=DescribeCSVFileData(
                file_name=csv_name,
                file_size_bytes=file_size,
                columns=columns,
                column_count=len(columns),
                row_count=row_count,
                sample_rows=rows[:5],
            ),
        )
    except Exception as e:
        logger.exception("Failed to describe CSV file name=%s", csv_name)
        return DescribeCSVFileResponse(success=False, error=str(e))


@tool()
async def add_csv_file(file_path: str) -> AddCSVFileResponse:
    """Add a CSV file to available files.

    Supports both local file paths and storage URLs:
        - Local: /path/to/file.csv
        - storage: minio://bucket/path/to/file.csv
    """
    try:
        if is_storage_path(file_path):
            # storage path - validate it exists by checking metadata
            try:
                bucket, object_name = parse_storage_path(file_path)
                await check_permission("storage_bucket", bucket, "viewer")
                if not object_name.lower().endswith(".csv"):
                    return AddCSVFileResponse(
                        success=False, error=f"Not a CSV file: {file_path}"
                    )

                # Validate the object exists in storage
                from src.tools.storage.tools import get_client, validate_bucket

                if error := validate_bucket(bucket):
                    return AddCSVFileResponse(success=False, error=error)

                client = get_client()
                client.stat_object(bucket, object_name)  # Will raise if not found

                manager = get_csv_manager()
                file_name = manager._add_file(file_path)
                if not file_name:
                    return AddCSVFileResponse(
                        success=False, error=f"Failed to add CSV: {file_path}"
                    )

                logger.info(
                    "Added storage CSV file name=%s path=%s", file_name, file_path
                )
                return AddCSVFileResponse(
                    success=True,
                    data=AddCSVFileData(
                        message=f"Added from storage: {file_name}", file_name=file_name
                    ),
                )
            except Exception as e:
                return AddCSVFileResponse(success=False, error=f"storage error: {e}")
        else:
            await require_auth()

            # Local file path
            path = Path(file_path)
            if not path.exists():
                return AddCSVFileResponse(
                    success=False, error=f"File not found: {file_path}"
                )
            if path.suffix.lower() != ".csv":
                return AddCSVFileResponse(
                    success=False, error=f"Not a CSV: {file_path}"
                )

            manager = get_csv_manager()
            file_name = manager._add_file(file_path)
            if not file_name:
                return AddCSVFileResponse(
                    success=False, error=f"Failed to add CSV: {file_path}"
                )

            logger.info("Added local CSV file name=%s", file_name)
            return AddCSVFileResponse(
                success=True,
                data=AddCSVFileData(message=f"Added: {file_name}", file_name=file_name),
            )
    except Exception as e:
        logger.exception("Failed to add CSV file path=%s", file_path)
        return AddCSVFileResponse(success=False, error=str(e))


@tool()
async def remove_csv_file(csv_name: str) -> RemoveCSVFileResponse:
    """Remove a CSV file from available files."""
    try:
        await require_auth()

        manager = get_csv_manager()
        if csv_name not in manager.csv_map:
            return RemoveCSVFileResponse(
                success=False, error=f"CSV '{csv_name}' not found"
            )

        path = manager.csv_map[csv_name]
        manager.csv_files.remove(path)
        del manager.csv_map[csv_name]

        logger.info("Removed CSV file name=%s", csv_name)
        return RemoveCSVFileResponse(
            success=True,
            data=RemoveCSVFileData(message=f"Removed: {csv_name}"),
        )
    except Exception as e:
        logger.exception("Failed to remove CSV file name=%s", csv_name)
        return RemoveCSVFileResponse(success=False, error=str(e))
