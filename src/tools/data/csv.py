import csv as csv_lib
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from fastmcp import FastMCP

try:
    import duckdb
    DUCKDB_AVAILABLE = True
except ImportError:
    DUCKDB_AVAILABLE = False

class CSVManager:
    def __init__(self, csv_files: list = None):
        self.csv_files = []
        self.csv_map = {}
        if csv_files:
            for file_path in csv_files:
                path = Path(file_path)
                if path.exists() and path.suffix.lower() == '.csv':
                    self.csv_files.append(path)
                    self.csv_map[path.stem] = path

    def get_file_path(self, csv_name: str):
        return self.csv_map.get(csv_name)

    def list_files(self):
        return list(self.csv_map.keys())


_csv_manager = None

def get_csv_manager():
    global _csv_manager
    if _csv_manager is None:
        _csv_manager = CSVManager()
    return _csv_manager

def set_csv_files(csv_files: list):
    global _csv_manager
    _csv_manager = CSVManager(csv_files)


async def list_csv_files() -> dict:
    """List all available CSV files."""
    try:
        manager = get_csv_manager()
        return {"success": True, "data": manager.list_files(), "count": len(manager.list_files())}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def read_csv_file(csv_name: str, row_limit: int = None) -> dict:
    """Read contents of a CSV file."""
    try:
        manager = get_csv_manager()
        file_path = manager.get_file_path(csv_name)
        if not file_path:
            return {"success": False, "error": f"CSV '{csv_name}' not found"}

        rows = []
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv_lib.DictReader(f)
            for i, row in enumerate(reader):
                if row_limit and i >= row_limit:
                    break
                rows.append(row)

        return {"success": True, "data": rows, "row_count": len(rows)}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def get_csv_columns(csv_name: str) -> dict:
    """Get column names from a CSV file."""
    try:
        manager = get_csv_manager()
        file_path = manager.get_file_path(csv_name)
        if not file_path:
            return {"success": False, "error": f"CSV '{csv_name}' not found"}

        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv_lib.DictReader(f)
            columns = reader.fieldnames or []

        return {"success": True, "data": columns, "column_count": len(columns)}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def query_csv_file(csv_name: str, sql_query: str) -> dict:
    """Execute SQL query on CSV file using DuckDB."""
    try:
        if not DUCKDB_AVAILABLE:
            return {"success": False, "error": "DuckDB required: pip install duckdb"}

        manager = get_csv_manager()
        file_path = manager.get_file_path(csv_name)
        if not file_path:
            return {"success": False, "error": f"CSV '{csv_name}' not found"}

        query = sql_query.strip().replace('`', '').split(';')[0]
        conn = duckdb.connect(':memory:')
        conn.execute(f"CREATE TABLE {csv_name} AS SELECT * FROM read_csv_auto('{file_path}')")
        result = conn.execute(query).fetchall()
        columns = [desc[0] for desc in conn.description]
        rows = [dict(zip(columns, row)) for row in result]
        conn.close()

        return {"success": True, "data": rows, "row_count": len(rows), "columns": columns}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def describe_csv_file(csv_name: str) -> dict:
    """Get detailed information about a CSV file."""
    try:
        manager = get_csv_manager()
        file_path = manager.get_file_path(csv_name)
        if not file_path:
            return {"success": False, "error": f"CSV '{csv_name}' not found"}

        file_size = file_path.stat().st_size
        rows = []

        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv_lib.DictReader(f)
            columns = reader.fieldnames or []
            for i, row in enumerate(reader):
                if i < 5:
                    rows.append(row)
                if i >= 1000:
                    break
            row_count = i + 1

        return {
            "success": True,
            "data": {
                "file_name": csv_name,
                "file_size_bytes": file_size,
                "columns": columns,
                "column_count": len(columns),
                "row_count": row_count,
                "sample_rows": rows[:5]
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


async def add_csv_file(file_path: str) -> dict:
    """Add a CSV file to available files."""
    try:
        path = Path(file_path)
        if not path.exists():
            return {"success": False, "error": f"File not found: {file_path}"}
        if path.suffix.lower() != '.csv':
            return {"success": False, "error": f"Not a CSV: {file_path}"}

        manager = get_csv_manager()
        manager.csv_files.append(path)
        manager.csv_map[path.stem] = path

        return {"success": True, "data": {"message": f"Added: {path.stem}", "file_name": path.stem}}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def remove_csv_file(csv_name: str) -> dict:
    """Remove a CSV file from available files."""
    try:
        manager = get_csv_manager()
        if csv_name not in manager.csv_map:
            return {"success": False, "error": f"CSV '{csv_name}' not found"}

        path = manager.csv_map[csv_name]
        manager.csv_files.remove(path)
        del manager.csv_map[csv_name]

        return {"success": True, "data": {"message": f"Removed: {csv_name}"}}
    except Exception as e:
        return {"success": False, "error": str(e)}


def register_tools(mcp: FastMCP) -> None:
    """Register all CSV tools with the MCP server."""

    mcp.tool(name="csv/list_csv_files")(list_csv_files)
    mcp.tool(name="csv/read_csv_file")(read_csv_file)
    mcp.tool(name="csv/get_csv_columns")(get_csv_columns)
    mcp.tool(name="csv/query_csv_file")(query_csv_file)
    mcp.tool(name="csv/describe_csv_file")(describe_csv_file)
    mcp.tool(name="csv/add_csv_file")(add_csv_file)
    mcp.tool(name="csv/remove_csv_file")(remove_csv_file)