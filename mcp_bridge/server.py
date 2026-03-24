from typing import Any, Dict, List, Optional
import os

import httpx
from fastmcp import FastMCP
from pydantic import BaseModel, Field


API_BASE_URL = os.getenv("CRAWLER_API_BASE_URL", "http://127.0.0.1:8080").rstrip("/")
API_KEY = os.getenv("CRAWLER_API_KEY", "").strip()
HTTP_TIMEOUT = float(os.getenv("CRAWLER_HTTP_TIMEOUT", "60"))
MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "stdio")
MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.getenv("MCP_PORT", "8001"))

mcp = FastMCP("Stealth Crawler Bridge")


class CrawlOptions(BaseModel):
    timeout: int = 20
    max_retries: int = 3
    delay_min: float = 0.5
    delay_max: float = 1.5
    robots_mode: str = "strict"
    respect_robots: bool = True
    rotate_user_agent: bool = True
    proxies: List[str] = Field(default_factory=list)
    headers: Dict[str, str] = Field(default_factory=dict)


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
    return await _post("/fetch", {"url": url, "options": options.model_dump()})


@mcp.tool
async def parse(url: str, options: Optional[CrawlOptions] = None) -> Dict[str, Any]:
    """Fetch and parse a URL through the remote crawler API."""
    options = options or CrawlOptions()
    return await _post("/parse", {"url": url, "options": options.model_dump()})


@mcp.tool
async def analyze(url: str, robots_mode: str = "strict", user_agent: str = "*", timeout: int = 10) -> Dict[str, Any]:
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


if __name__ == "__main__":
    if MCP_TRANSPORT.lower() == "http":
        mcp.run(transport="http", host=MCP_HOST, port=MCP_PORT)
    else:
        mcp.run()
