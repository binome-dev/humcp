import os
import threading

from dotenv import load_dotenv

from src.adapter.adapter import FastMCPFastAPIAdapter
from src.server import mcp

load_dotenv()

MCP_PORT = os.getenv("MCP_PORT", "8081")


def start_mcp_server() -> threading.Thread:
    """Start the MCP server in a background thread so FastAPI and MCP run together."""

    def _run_server():
        mcp.run(transport="http", host="0.0.0.0", port=int(MCP_PORT), path="/mcp")

    thread = threading.Thread(target=_run_server, daemon=True, name="mcp-server-thread")
    thread.start()
    return thread


_mcp_thread = start_mcp_server()

mcp_server_url = os.getenv("MCP_SERVER_URL") or f"http://0.0.0.0:{MCP_PORT}/mcp"

adapter = FastMCPFastAPIAdapter(
    title="HuMCP FastAPI server",
    description="HuMCP FastAPI server",
    mcp_url=mcp_server_url,
)

app = adapter.create_app()
