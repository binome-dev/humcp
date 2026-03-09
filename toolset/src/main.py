"""HuMCP Server entry point."""

import warnings

# Suppress deprecation warnings from third-party libraries
# pydub: missing ffmpeg warning (not needed for our use case)
warnings.filterwarnings(
    "ignore", message="Couldn't find ffmpeg or avconv", category=RuntimeWarning
)
# httplib2: uses deprecated pyparsing methods (waiting for upstream fix)
warnings.filterwarnings("ignore", module="httplib2.auth", category=DeprecationWarning)

from dotenv import load_dotenv  # noqa: E402

from src.humcp.server import create_app  # noqa: E402
from src.logging_setup import configure_logging  # noqa: E402

load_dotenv()

configure_logging()

app = create_app()
