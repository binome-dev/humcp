"""HuMCP Server entry point."""

from dotenv import load_dotenv

load_dotenv()

from src.humcp.server import create_app
from src.logging_setup import configure_logging

configure_logging()

app = create_app()
