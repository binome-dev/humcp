import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

PROJECT_ROOT = Path(__file__).parent.parent
SERVER_HOST = "localhost"
SERVER_PORT = 8081
SERVER_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"


def wait_for_server(url: str, timeout: float = 30.0, interval: float = 0.5) -> bool:
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = httpx.get(f"{url}/mcp", timeout=2.0)
            if response.status_code < 500:
                return True
        except httpx.ConnectError:
            pass
        except httpx.ReadTimeout:
            return True
        time.sleep(interval)
    return False


@pytest.fixture(scope="session")
def mcp_server():
    server_script = PROJECT_ROOT / "src" / "server.py"

    process = subprocess.Popen(
        [sys.executable, str(server_script)],
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if not wait_for_server(SERVER_URL):
        stdout, stderr = process.communicate(timeout=5)
        process.kill()
        raise RuntimeError(
            f"MCP server failed to start within timeout.\n"
            f"stdout: {stdout.decode()}\n"
            f"stderr: {stderr.decode()}"
        )

    yield {
        "url": SERVER_URL,
        "mcp_url": f"{SERVER_URL}/mcp",
        "host": SERVER_HOST,
        "port": SERVER_PORT,
    }

    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


@pytest.fixture
def mcp_url(mcp_server):
    return mcp_server["mcp_url"]
