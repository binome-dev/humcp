"""REST route generation for tools."""

import asyncio
import base64
import hashlib
import logging
import secrets
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import httpx
from fastapi import Body, Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastmcp.server.dependencies import get_access_token
from pydantic import BaseModel, Field, create_model

from src.humcp.decorator import RegisteredTool
from src.humcp.schemas import (
    CategoryInfo,
    CategorySummary,
    GetCategoryResponse,
    GetToolResponse,
    InputSchema,
    ListCategoriesResponse,
    ListToolsResponse,
    SkillFull,
    SkillMetadata,
    ToolSummary,
)
from src.humcp.skills import discover_skills
from src.tools.google.auth import set_rest_access_token

logger = logging.getLogger("humcp.routes")

# Store for PKCE verifiers and registered client
_pkce_store: dict[str, str] = {}
_browser_client: dict[str, str] = {}
_registration_lock = asyncio.Lock()


def _format_tag(category: str) -> str:
    """Format category as display tag: 'local_files' -> 'Local Files'."""
    return category.replace("_", " ").title()


async def _extract_token(request: Request) -> str | None:
    """Extract access token from request if available.

    Checks multiple sources in order:
    1. FastMCP's get_access_token() for MCP session context
    2. Cookie-based access_token from browser login
    3. Bearer token in Authorization header

    Also sets the access token in context variable for Google tools to use.

    Args:
        request: FastAPI request object

    Returns:
        Access token string if found, None otherwise
    """
    # Try FastMCP's get_access_token() for MCP context
    try:
        token = get_access_token()
        if token and token.token:
            logger.debug("REST request authenticated via MCP session")
            set_rest_access_token(token.token)
            return token.token
    except Exception:
        pass  # Fall through to other methods

    # Check for cookie (from /login flow)
    access_token = request.cookies.get("access_token")
    if access_token:
        logger.debug("REST request authenticated via cookie")
        set_rest_access_token(access_token)
        return access_token

    # Check for Bearer token in Authorization header
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        access_token = auth_header[7:]
        logger.debug("REST request authenticated via Bearer token")
        set_rest_access_token(access_token)
        return access_token

    return None


async def require_rest_auth(request: Request):
    """Require OAuth authentication for REST endpoints.

    This dependency checks for authentication and raises 401 if not found.
    Used when AUTH_ENABLED=true.

    Args:
        request: FastAPI request object

    Returns:
        Access token string if authenticated

    Raises:
        HTTPException: 401 if not authenticated or token is invalid
    """
    token = await _extract_token(request)
    if token:
        return token

    # No valid authentication found
    raise HTTPException(
        status_code=401,
        detail="Authentication required. Please visit /login to authenticate.",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def optional_rest_auth(request: Request):
    """Optional authentication for REST endpoints.

    This dependency extracts and sets the token if available, but doesn't
    require authentication. Used when AUTH_ENABLED=false but Google tools
    still need the Bearer token if provided.

    Args:
        request: FastAPI request object

    Returns:
        Access token string if found, None otherwise
    """
    return await _extract_token(request)


def _register_auth_routes(
    app: FastAPI,
    auth_provider: Any,
) -> None:
    """Register authentication routes (login/logout).

    When auth_provider is None (AUTH_ENABLED=false), no routes are registered.

    Args:
        app: FastAPI application.
        auth_provider: FastMCP auth provider for OAuth operations (None if disabled).
    """
    # Skip login/logout endpoints if auth is disabled
    if not auth_provider:
        logger.info(
            "Skipping auth endpoints (/login, /logout) - authentication disabled"
        )
        return

    @app.get("/login", tags=["Auth"])
    async def login(request: Request):
        """Browser login endpoint - initiates OAuth flow for Swagger UI users.

        This endpoint:
        1. Registers a browser OAuth client with FastMCP (if not already registered)
        2. Generates PKCE challenge
        3. Redirects to /authorize with proper parameters
        """

        async with _registration_lock:
            if not _browser_client.get("client_id"):
                async with httpx.AsyncClient() as client:
                    register_response = await client.post(
                        "http://localhost:8080/register",
                        json={
                            "client_name": "HuMCP Browser Client",
                            "redirect_uris": ["http://localhost:8080/login/callback"],
                            "grant_types": ["authorization_code", "refresh_token"],
                            "response_types": ["code"],
                            "token_endpoint_auth_method": "none",  # Public client (PKCE only)
                        },
                    )

                    if register_response.status_code != 201:
                        logger.error(
                            "Failed to register browser client: %s",
                            register_response.text,
                        )
                        return HTMLResponse(
                            content=f"<h1>Registration Failed</h1><pre>{register_response.text}</pre>",
                            status_code=500,
                        )

                    client_data = register_response.json()
                    _browser_client["client_id"] = client_data["client_id"]
                    _browser_client["client_secret"] = client_data.get(
                        "client_secret", ""
                    )
                    logger.info(
                        "Registered browser client: %s", _browser_client["client_id"]
                    )

        # Generate PKCE code verifier and challenge
        code_verifier = secrets.token_urlsafe(32)
        code_challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest())
            .decode()
            .rstrip("=")
        )

        # Store verifier for later token exchange
        state = secrets.token_urlsafe(16)
        _pkce_store[state] = code_verifier

        # Use the same scopes as MCP authentication
        scopes = (
            " ".join(auth_provider.required_scopes) if auth_provider else "openid email"
        )

        # Build authorization URL with registered client
        params = {
            "client_id": _browser_client["client_id"],
            "response_type": "code",
            "redirect_uri": "http://localhost:8080/login/callback",
            "scope": scopes,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }

        auth_url = f"http://localhost:8080/authorize?{urlencode(params)}"

        accept_header = request.headers.get("accept", "")
        if "application/json" in accept_header and "text/html" not in accept_header:
            return {
                "message": "Please visit the login URL in your browser to authenticate",
                "login_url": auth_url,
                "instructions": "Open the login_url in a new browser tab to complete authentication",
            }

        # Direct browser visit - redirect to OAuth
        return RedirectResponse(url=auth_url)

    @app.get("/login/callback", tags=["Auth"])
    async def login_callback(
        request: Request,
        code: str | None = None,
        state: str | None = None,
        error: str | None = None,
    ):
        """OAuth callback handler for browser login.

        Exchanges authorization code for tokens and creates a session.
        """
        if error:
            return HTMLResponse(
                content=f"<h1>Authentication Error</h1><p>{error}</p><a href='/login'>Try again</a>",
                status_code=400,
            )

        if not code or not state:
            return HTMLResponse(
                content="<h1>Missing Parameters</h1><p>Missing code or state parameter</p><a href='/login'>Try again</a>",
                status_code=400,
            )

        # Get the stored PKCE verifier
        code_verifier = _pkce_store.pop(state, None)
        if not code_verifier:
            return HTMLResponse(
                content="<h1>Invalid State</h1><p>Session expired or invalid state</p><a href='/login'>Try again</a>",
                status_code=400,
            )

        # Exchange code for token using registered browser client
        import httpx

        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "http://localhost:8080/token",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": "http://localhost:8080/login/callback",
                    "client_id": _browser_client.get("client_id", ""),
                    "code_verifier": code_verifier,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

        if token_response.status_code != 200:
            logger.error("Token exchange failed: %s", token_response.text)
            return HTMLResponse(
                content=f"<h1>Token Exchange Failed</h1><pre>{token_response.text}</pre><a href='/login'>Try again</a>",
                status_code=400,
            )

        tokens = token_response.json()
        fastmcp_jwt = tokens.get("access_token")

        # FastMCP returns its own JWT, but we need the actual Google access token
        # Use FastMCP's load_access_token to get the upstream Google token
        access_token = fastmcp_jwt
        if auth_provider:
            try:
                access_token_obj = await auth_provider.load_access_token(fastmcp_jwt)
                if access_token_obj:
                    access_token = access_token_obj.token
                    logger.info("Retrieved upstream Google token from FastMCP JWT")
                else:
                    logger.warning("Could not load upstream token, using FastMCP JWT")
            except Exception as e:
                logger.warning(
                    "Failed to load upstream token: %s, using FastMCP JWT", e
                )

        # Create response with session cookie
        response = HTMLResponse(
            content=f"""
            <html>
            <head><title>Login Successful</title></head>
            <body>
                <h1>Login Successful!</h1>
                <p>You are now authenticated.</p>
                <p><a href="/docs">Go to Swagger UI</a></p>
                <script>
                    localStorage.setItem('access_token', '{access_token}');
                </script>
            </body>
            </html>
            """,
            status_code=200,
        )

        # Set the access token as a cookie for REST API calls
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            samesite="lax",
            max_age=3600,  # 1 hour
        )

        return response

    @app.get("/logout", tags=["Auth"])
    async def logout():
        """Logout endpoint - clears the session cookie."""
        response = RedirectResponse(url="/")
        response.delete_cookie("access_token")
        return response


def register_routes(
    app: FastAPI,
    tools_path: Path,
    tools: list[RegisteredTool],
    auth_provider: Any = None,
    title: str = "HuMCP Server",
    version: str = "1.0.0",
    apps_count: int = 0,
) -> None:
    """Register all REST routes including tools and auth endpoints.

    Args:
        app: FastAPI application.
        tools_path: Path to tools directory for skill discovery.
        tools: List of registered tools.
        auth_provider: FastMCP auth provider for OAuth operations (None if auth disabled).
        title: App title for info endpoint.
        version: App version for info endpoint.
        apps_count: Number of MCP App bundles available.
    """
    # Build lookups
    categories = _build_categories(tools)
    tool_lookup = {(t.category, t.tool.name): t for t in tools}

    # Choose auth dependency based on whether auth is enabled
    # When auth_provider is None (AUTH_ENABLED=false), use optional auth
    # This still allows Bearer tokens for Google tools but doesn't require auth
    auth_dependency = require_rest_auth if auth_provider else optional_rest_auth

    if auth_provider:
        logger.info("Authentication enabled - REST endpoints require auth")
    else:
        logger.info(
            "Authentication disabled - REST endpoints open (Bearer token optional for Google tools)"
        )

    # Tool execution endpoints
    for reg in tools:
        _add_tool_route(app, reg, auth_dependency)

    # Discover skills
    skills = discover_skills(tools_path)

    # Register auth endpoints only when auth is enabled
    _register_auth_routes(app, auth_provider)

    # Info endpoints
    @app.get("/tools", tags=["Info"], response_model=ListToolsResponse)
    async def list_tools() -> ListToolsResponse:
        return ListToolsResponse(
            total_tools=len(tools),
            categories={
                cat: CategorySummary(
                    count=len(items),
                    tools=[ToolSummary(**t) for t in items],
                    skill=SkillMetadata(
                        name=skills[cat].name, description=skills[cat].description
                    )
                    if cat in skills
                    else None,
                )
                for cat, items in sorted(categories.items())
            },
        )

    @app.get("/tools/{category}", tags=["Info"], response_model=GetCategoryResponse)
    async def get_category(category: str) -> GetCategoryResponse:
        if category not in categories:
            raise HTTPException(404, f"Category '{category}' not found")
        skill = skills.get(category)
        return GetCategoryResponse(
            category=category,
            count=len(categories[category]),
            tools=[ToolSummary(**t) for t in categories[category]],
            skill=SkillFull(
                name=skill.name, description=skill.description, content=skill.content
            )
            if skill
            else None,
        )

    @app.get(
        "/tools/{category}/{tool_name}", tags=["Info"], response_model=GetToolResponse
    )
    async def get_tool(category: str, tool_name: str) -> GetToolResponse:
        reg = tool_lookup.get((category, tool_name))
        if not reg:
            raise HTTPException(404, f"Tool '{tool_name}' not found in '{category}'")
        return GetToolResponse(
            name=reg.tool.name,
            category=reg.category,
            description=reg.tool.description,
            endpoint=f"/tools/{reg.tool.name}",
            input_schema=InputSchema(**reg.tool.parameters),
            output_schema=reg.tool.output_schema,
        )

    @app.get("/categories", tags=["Info"], response_model=ListCategoriesResponse)
    async def list_categories() -> ListCategoriesResponse:
        category_list = [
            CategoryInfo(
                name=cat,
                tool_count=len(items),
                skill=SkillFull(
                    name=skills[cat].name,
                    description=skills[cat].description,
                    content=skills[cat].content,
                )
                if cat in skills
                else None,
            )
            for cat, items in sorted(categories.items())
        ]
        return ListCategoriesResponse(
            total_categories=len(category_list),
            categories=category_list,
        )


def _add_tool_route(app: FastAPI, reg: RegisteredTool, auth_dependency: Any) -> None:
    """Add POST /tools/{name} endpoint for a tool.

    Args:
        app: FastAPI application.
        reg: Tool registration info.
        auth_dependency: Authentication dependency (require_rest_auth or optional_rest_auth).
    """
    tool = reg.tool
    InputModel = _create_model_from_schema(
        tool.parameters, f"{_pascal(tool.name)}Input"
    )

    async def endpoint(
        data: BaseModel = Body(...),  # type: ignore[assignment]
        token=Depends(auth_dependency),
    ) -> dict[str, Any]:
        try:
            params = data.model_dump(exclude_none=True)
            result = await tool.fn(**params)
            return {"result": result}
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("Tool %s failed", tool.name)
            raise HTTPException(500, "Tool execution failed") from e

    endpoint.__annotations__["data"] = InputModel
    app.add_api_route(
        f"/tools/{tool.name}",
        endpoint,
        methods=["POST"],
        summary=tool.description or tool.name,
        tags=[_format_tag(reg.category)],
        name=tool.name,
    )


def _build_categories(tools: list[RegisteredTool]) -> dict[str, list[dict[str, Any]]]:
    """Build category -> tools map."""
    cats: dict[str, list[dict[str, Any]]] = {}
    for reg in tools:
        cats.setdefault(reg.category, []).append(
            {
                "name": reg.tool.name,
                "description": reg.tool.description,
                "endpoint": f"/tools/{reg.tool.name}",
            }
        )
    return cats


def build_openapi_tags(tools: list[RegisteredTool]) -> list[dict[str, str]]:
    """Build OpenAPI tag metadata."""
    categories = sorted({reg.category for reg in tools})
    tags = [{"name": "Info", "description": "Server and tool information"}]
    for cat in categories:
        count = sum(1 for reg in tools if reg.category == cat)
        tags.append(
            {
                "name": _format_tag(cat),
                "description": f"{_format_tag(cat)} tools ({count} endpoints)",
            }
        )
    return tags


def _pascal(name: str) -> str:
    """Convert to PascalCase."""
    name = name.replace("_", " ").replace("-", " ").replace(".", " ")
    name = "".join(w.capitalize() for w in name.split())
    return f"Model{name}" if name and not name[0].isalpha() else name or "Model"


def _create_model_from_schema(schema: dict[str, Any], name: str) -> type[BaseModel]:
    """Create Pydantic model from JSON schema."""
    if schema.get("type") != "object":
        return create_model(name, value=(Any, ...))

    props = schema.get("properties", {})
    required = schema.get("required", [])
    fields: dict[str, Any] = {}

    type_map = {
        "string": str,
        "integer": int,
        "number": float,
        "boolean": bool,
        "array": list,
        "object": dict,
    }

    for fname, fschema in props.items():
        ftype = type_map.get(fschema.get("type"), Any)
        desc = fschema.get("description")
        if fname in required:
            fields[fname] = (
                (ftype, Field(..., description=desc)) if desc else (ftype, ...)
            )
        else:
            fields[fname] = (
                (ftype | None, Field(None, description=desc))
                if desc
                else (ftype | None, None)
            )

    return create_model(name, **fields)
