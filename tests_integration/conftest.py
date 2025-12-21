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
    print(f"Waiting for server at {url}...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = httpx.get(f"{url}/mcp", timeout=2.0)
            print(f"Server response: {response.status_code}")
            if response.status_code < 500:
                return True
        except httpx.ConnectError as e:
            print(f"Connection error (retrying): {e}")
        except httpx.ReadTimeout:
            print("Read timeout (server may be starting)")
            return True
        time.sleep(interval)
    return False


@pytest.fixture(scope="session")
def mcp_server():
    print(f"Working directory: {PROJECT_ROOT}")

    process = subprocess.Popen(
        [sys.executable, "-m", "src.server"],
        cwd=str(PROJECT_ROOT),
        env={**dict(__import__("os").environ), "PYTHONPATH": str(PROJECT_ROOT)},
    )

    time.sleep(2)

    if process.poll() is not None:
        raise RuntimeError(
            f"MCP server process exited immediately with code: {process.returncode}"
        )

    if not wait_for_server(SERVER_URL):
        process.kill()
        raise RuntimeError(f"MCP server failed to start within timeout at {SERVER_URL}")

    print(f"=== MCP Server Started at {SERVER_URL} ===\n")

    yield {
        "url": SERVER_URL,
        "mcp_url": f"{SERVER_URL}/mcp",
        "host": SERVER_HOST,
        "port": SERVER_PORT,
    }

    print("\n=== Stopping MCP Server ===")
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
    print("=== MCP Server Stopped ===\n")


@pytest.fixture
def mcp_url(mcp_server):
    return mcp_server["mcp_url"]
