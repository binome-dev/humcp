import os

from dotenv import load_dotenv

from src.adapter.adapter import FastMCPFastAPIAdapter

load_dotenv()

mcp_server_url = os.getenv("MCP_SERVER_URL")

adapter = FastMCPFastAPIAdapter(
    title="Humcp FastAPI server",
    description="Humcp FastAPI server",
    mcp_url=mcp_server_url,
)

app = adapter.create_app()
