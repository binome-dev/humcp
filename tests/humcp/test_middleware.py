"""Tests for humcp middleware module."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.responses import JSONResponse


def _create_test_app(service_api_key: str = "") -> FastAPI:
    """Create a minimal FastAPI app with APIKeyMiddleware for testing."""
    # We need to patch the module-level SERVICE_API_KEY before adding middleware,
    # so we import and patch at call time.
    import src.humcp.middleware as mw_module

    original_key = mw_module.SERVICE_API_KEY
    mw_module.SERVICE_API_KEY = service_api_key

    app = FastAPI()
    app.add_middleware(mw_module.APIKeyMiddleware)

    @app.get("/")
    async def root():
        return {"message": "root"}

    @app.get("/docs")
    async def docs():
        return {"message": "docs"}

    @app.get("/openapi.json")
    async def openapi():
        return {"message": "openapi"}

    @app.get("/tools")
    async def tools():
        return {"message": "tools"}

    @app.get("/tools/test")
    async def tools_test():
        return {"message": "tools_test"}

    # Restore original key after app creation (middleware captures reference to module)
    # We rely on the middleware reading mw_module.SERVICE_API_KEY at dispatch time
    return app, mw_module, original_key


class TestAPIKeyMiddleware:
    """Tests for APIKeyMiddleware."""

    def test_public_paths_bypass_auth(self):
        """Requests to /, /docs, /openapi.json should pass without API key."""
        app, mw_module, original_key = _create_test_app(service_api_key="secret-key")
        try:
            client = TestClient(app, raise_server_exceptions=False)

            resp = client.get("/")
            assert resp.status_code == 200

            resp = client.get("/docs")
            assert resp.status_code == 200

            resp = client.get("/openapi.json")
            assert resp.status_code == 200
        finally:
            mw_module.SERVICE_API_KEY = original_key

    def test_missing_api_key_returns_401(self):
        """When SERVICE_API_KEY is set, request without key to /tools returns 401."""
        app, mw_module, original_key = _create_test_app(service_api_key="secret-key")
        try:
            client = TestClient(app, raise_server_exceptions=False)

            resp = client.get("/tools")
            assert resp.status_code == 401
        finally:
            mw_module.SERVICE_API_KEY = original_key

    def test_valid_api_key_passes(self):
        """Request with correct X-API-Key header should pass."""
        app, mw_module, original_key = _create_test_app(service_api_key="secret-key")
        try:
            client = TestClient(app, raise_server_exceptions=False)

            resp = client.get("/tools", headers={"X-API-Key": "secret-key"})
            assert resp.status_code == 200
            assert resp.json()["message"] == "tools"
        finally:
            mw_module.SERVICE_API_KEY = original_key

    def test_invalid_api_key_returns_401(self):
        """Wrong API key should return 401."""
        app, mw_module, original_key = _create_test_app(service_api_key="secret-key")
        try:
            client = TestClient(app, raise_server_exceptions=False)

            resp = client.get("/tools", headers={"X-API-Key": "wrong-key"})
            assert resp.status_code == 401
        finally:
            mw_module.SERVICE_API_KEY = original_key

    def test_no_api_key_configured_passes(self):
        """When SERVICE_API_KEY is not set, all requests should pass."""
        app, mw_module, original_key = _create_test_app(service_api_key="")
        try:
            client = TestClient(app, raise_server_exceptions=False)

            resp = client.get("/tools")
            assert resp.status_code == 200

            resp = client.get("/tools/test")
            assert resp.status_code == 200
        finally:
            mw_module.SERVICE_API_KEY = original_key
