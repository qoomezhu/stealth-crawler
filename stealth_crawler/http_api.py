import os
from typing import Dict, Optional

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastmcp import FastMCP
from pydantic import BaseModel, Field

from .config import build_crawler_config
from .crawler import Crawler
from .exceptions import (
    CrawlerError,
    ParseError,
    ProxyError,
    RobotsBlockedError,
    RetryExhaustedError,
)
from .normalization import normalize_analysis_payload
from .schemas import CrawlOptions
from .security import SecurityMiddleware

app_version = "2.4.0"

API_KEY = os.getenv("CRAWLER_API_KEY", "").strip() or None
RATE_LIMIT_REQUESTS = int(os.getenv("CRAWLER_RATE_LIMIT_REQUESTS", "60"))
RATE_LIMIT_WINDOW = int(os.getenv("CRAWLER_RATE_LIMIT_WINDOW", "60"))
RATE_LIMIT_BACKEND = os.getenv("CRAWLER_RATE_LIMIT_BACKEND", "memory").strip().lower()
RATE_LIMIT_REDIS_URL = os.getenv("CRAWLER_RATE_LIMIT_REDIS_URL", "").strip() or None
MCP_BEARER_TOKEN = os.getenv("MCP_BEARER_TOKEN", "").strip() or None
MCP_PUBLIC_PATHS = {
    path.strip()
    for path in os.getenv("MCP_PUBLIC_PATHS", "/mcp/healthz").split(",")
    if path.strip()
}

mcp = FastMCP("Stealth Crawler")
mcp_app = mcp.http_app(path="/mcp")

app = FastAPI(title="Stealth Crawler API", version=app_version, lifespan=mcp_app.lifespan)

app.add_middleware(
    SecurityMiddleware,
    api_key=API_KEY,
    rate_limit_requests=RATE_LIMIT_REQUESTS,
    rate_limit_window=RATE_LIMIT_WINDOW,
    rate_limit_backend=RATE_LIMIT_BACKEND,
    redis_url=RATE_LIMIT_REDIS_URL,
    mcp_bearer_token=MCP_BEARER_TOKEN,
    mcp_public_paths=MCP_PUBLIC_PATHS,
)


class FetchRequest(BaseModel):
    url: str
    options: CrawlOptions = Field(default_factory=CrawlOptions)


class AnalyzeRequest(BaseModel):
    url: str
    robots_mode: str = "strict"
    user_agent: str = "*"
    timeout: int = 10


class ParseRequest(BaseModel):
    url: str
    options: CrawlOptions = Field(default_factory=CrawlOptions)


def _build_config(options: CrawlOptions):
    return build_crawler_config(
        timeout=options.timeout,
        max_retries=options.max_retries,
        delay_min=options.delay_min,
        delay_max=options.delay_max,
        robots_mode=options.robots_mode,
        respect_robots=options.respect_robots,
        rotate_user_agent=options.rotate_user_agent,
        require_proxy=options.require_proxy,
    )


def _error_response(exc: Exception) -> JSONResponse:
    status_code = 500
    if isinstance(exc, RobotsBlockedError):
        status_code = 403
    elif isinstance(exc, ProxyError):
        status_code = 502
    elif isinstance(exc, RetryExhaustedError):
        status_code = 504
    elif isinstance(exc, ParseError):
        status_code = 422
    elif isinstance(exc, CrawlerError):
        status_code = 400

    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "type": exc.__class__.__name__,
                "message": str(exc) or exc.__class__.__name__,
            }
        },
    )


def _fetch_result(url: str, options: CrawlOptions, headers: Optional[Dict[str, str]] = None):
    config = _build_config(options)
    with Crawler(config=config, proxies=options.proxies or None) as crawler:
        return crawler.get(url, headers=headers or None)


def _fetch_payload(url: str, options: CrawlOptions, headers: Optional[Dict[str, str]] = None):
    result = _fetch_result(url, options, headers=headers)
    return result.to_normalized_dict(include_text=True, include_parsed=False)


def _parse_payload(url: str, options: CrawlOptions, headers: Optional[Dict[str, str]] = None):
    result = _fetch_result(url, options, headers=headers)
    return result.to_normalized_dict(include_text=True, include_parsed=True)


def _analysis_payload(url: str, robots_mode: str, user_agent: str, timeout: int):
    from .robots import RobotsChecker

    checker = RobotsChecker(timeout=timeout)
    allowed, reason, crawl_delay = checker.check(
        url,
        user_agent=user_agent,
        mode=robots_mode,
    )
    return normalize_analysis_payload(
        url,
        allowed,
        reason,
        crawl_delay,
        robots_mode,
    )


@app.get("/health")
def health_route():
    return {"status": "ok", "service": "stealth-crawler"}


@app.post("/fetch")
def fetch_route(req: FetchRequest):
    try:
        return _fetch_payload(req.url, req.options, req.options.headers or None)
    except Exception as exc:
        return _error_response(exc)


@app.post("/parse")
def parse_route(req: ParseRequest):
    try:
        return _parse_payload(req.url, req.options, req.options.headers or None)
    except Exception as exc:
        return _error_response(exc)


@app.post("/analyze")
def analyze_route(req: AnalyzeRequest):
    try:
        return _analysis_payload(req.url, req.robots_mode, req.user_agent, req.timeout)
    except Exception as exc:
        return _error_response(exc)


@app.router.routes.extend(mcp_app.routes)


@mcp.tool
async def health() -> Dict[str, str]:
    return health_route()


@mcp.tool
async def fetch(url: str, options: Optional[CrawlOptions] = None) -> Dict[str, object]:
    return _fetch_payload(url, options or CrawlOptions(), None)


@mcp.tool
async def parse(url: str, options: Optional[CrawlOptions] = None) -> Dict[str, object]:
    return _parse_payload(url, options or CrawlOptions(), None)


@mcp.tool
async def analyze(
    url: str,
    robots_mode: str = "strict",
    user_agent: str = "*",
    timeout: int = 10,
) -> Dict[str, object]:
    return _analysis_payload(url, robots_mode, user_agent, timeout)
