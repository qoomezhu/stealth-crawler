from __future__ import annotations

import os
from typing import Any, Dict, Optional, Set

import httpx
from fastmcp import FastMCP
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from stealth_crawler.schemas import CrawlOptions


API_BASE_URL = os.getenv("CRAWLER_API_BASE_URL", "http://127.0.0.1:8080").rstrip("/")
API_KEY = os.getenv("CRAWLER_API_KEY", "").strip()
HTTP_TIMEOUT = float(os.getenv("CRAWLER_HTTP_TIMEOUT", "60"))
MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "stdio").strip().lower()
MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.getenv("MCP_PORT", "8001"))
MCP_BEARER_TOKEN = os.getenv("MCP_BEARER_TOKEN", "").strip()
MCP_PUBLIC_PATHS = {
    path.strip()
    for path in os.getenv("MCP_PUBLIC_PATHS", "/healthz").split(",")
    if path.strip()
}

mcp = FastMCP("Stealth Crawler Bridge")


class BearerAuthMiddleware(BaseHTTPMiddleware):
    """Validate Authorization: Bearer <token> for HTTP MCP requests."""

    def __init__(self, app, expected_token: str, public_paths: Optional[Set[str]] = None):
        super().__init__(app)
        self.expected_token = expected_token
        self.public_paths = public_paths or set()

    @staticmethod
    def _extract_bearer_token(request: Request) -> Optional[str]:
        auth = request.headers.get("authorization", "")
        if not auth.lower().startswith("bearer "):
            return None
        token = auth.split(" ", 1)[1].strip()
        return token or None

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.public_paths:
            return await call_next(request)

        # If no token is configured, the server remains open for local dev.
        # For remote deployment, set MCP_BEARER_TOKEN.
        if not self.expected_token:
            return await call_next(request)

        token = self._extract_bearer_token(request)
        if token != self.expected_token:
            return JSONResponse(
                status_code=401,
                content={"detail": "Unauthorized"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        return await call_next(request)


async def _healthz(_: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "stealth-crawler-mcp-bridge"})


def _auth_headers() -> Dict[str, str]:
    if API_KEY:
        return {"X-API-Key": API_KEY}
    return {}


async def _get(path: str) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        resp = await client.get(f"{API_BASE_URL}{path}", headers=_auth_headers())
        resp.raise_for_status()
        return resp.json()


async def _post(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        resp = await client.post(f"{API_BASE_URL}{path}", json=payload, headers=_auth_headers())
        resp.raise_for_status()
        return resp.json()


@mcp.tool
async def health() -> Dict[str, Any]:
    """Check the remote crawler API health."""
    return await _get("/health")


@mcp.tool
async def fetch(url: str, options: Optional[CrawlOptions] = None) -> Dict[str, Any]:
    """Fetch a URL through the remote crawler API."""
    options = options or CrawlOptions()
    return await _post(
        "/fetch",
        {"url": url, "options": options.model_dump()},
    )


@mcp.tool
async def parse(url: str, options: Optional[CrawlOptions] = None) -> Dict[str, Any]:
    """Fetch and parse a URL through the remote crawler API."""
    options = options or CrawlOptions()
    return await _post(
        "/parse",
        {"url": url, "options": options.model_dump()},
    )


@mcp.tool
async def analyze(
    url: str,
    robots_mode: str = "strict",
    user_agent: str = "*",
    timeout: int = 10,
) -> Dict[str, Any]:
    """Analyze robots.txt for a URL."""
    return await _post(
        "/analyze",
        {
            "url": url,
            "robots_mode": robots_mode,
            "user_agent": user_agent,
            "timeout": timeout,
        },
    )


def create_http_app():
    middleware = [
        Middleware(
            BearerAuthMiddleware,
            expected_token=MCP_BEARER_TOKEN,
            public_paths=MCP_PUBLIC_PATHS,
        )
    ]
    routes = [Route("/healthz", _healthz, methods=["GET"])]
    return mcp.http_app(path="/mcp", middleware=middleware, routes=routes)


http_app = create_http_app()


if __name__ == "__main__":
    if MCP_TRANSPORT == "http":
        if not MCP_BEARER_TOKEN:
            print("[WARN] MCP_BEARER_TOKEN is empty. HTTP MCP endpoint will be unauthenticated.")

        import uvicorn

        uvicorn.run(http_app, host=MCP_HOST, port=MCP_PORT)
    else:
        mcp.run()
