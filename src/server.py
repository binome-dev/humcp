from fastmcp import FastMCP

mcp = FastMCP("Humcp Server")

try:
    from src.tools.data import csv

    csv.register_tools(mcp)
except ImportError as e:
    print(f"CSV tools not available: {e}")

# try:
#     from src.tools.data import pandas
#     pandas.register_tools(mcp)
# except ImportError as e:
#     print(f"Pandas tools not available: {e}")

try:
    from src.tools.local import calculator

    calculator.register_tools(mcp)
except ImportError as e:
    print(f"Calculator tools not available: {e}")

# try:
#     from src.tools.local import local_file_system
#     local_file_system.register_tools(mcp)
# except ImportError as e:
#     print(f"Local File System tools not available: {e}")

# try:
#     from src.tools.local import shell
#     shell.register_tools(mcp)
# except ImportError as e:
#     print(f"Shell tools not available: {e}")

try:
    from src.tools.search import tavily_tool

    tavily_tool.register_tools(mcp)
except ImportError as e:
    print(f"Tavily search tools not available: {e}")


if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=8081)
