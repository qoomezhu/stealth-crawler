import os

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .config import build_crawler_config
from .crawler import Crawler
from .exceptions import CrawlerError, ParseError, ProxyError, RobotsBlockedError, RetryExhaustedError
from .normalization import normalize_analysis_payload
from .robots import RobotsChecker
from .schemas import CrawlOptions
from .security import SecurityMiddleware

app = FastAPI(title="Stealth Crawler API", version="2.3.0")

API_KEY = os.getenv("CRAWLER_API_KEY", "").strip() or None
RATE_LIMIT_REQUESTS = int(os.getenv("CRAWLER_RATE_LIMIT_REQUESTS", "60"))
RATE_LIMIT_WINDOW = int(os.getenv("CRAWLER_RATE_LIMIT_WINDOW", "60"))
RATE_LIMIT_BACKEND = os.getenv("CRAWLER_RATE_LIMIT_BACKEND", "memory").strip().lower()
RATE_LIMIT_REDIS_URL = os.getenv("CRAWLER_RATE_LIMIT_REDIS_URL", "").strip() or None

app.add_middleware(
    SecurityMiddleware,
    api_key=API_KEY,
    rate_limit_requests=RATE_LIMIT_REQUESTS,
    rate_limit_window=RATE_LIMIT_WINDOW,
    rate_limit_backend=RATE_LIMIT_BACKEND,
    redis_url=RATE_LIMIT_REDIS_URL,
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


@app.get("/health")
def health():
    return {"status": "ok", "service": "stealth-crawler"}


@app.post("/fetch")
def fetch(req: FetchRequest):
    config = _build_config(req.options)
    try:
        with Crawler(config=config, proxies=req.options.proxies or None) as crawler:
            result = crawler.get(req.url, headers=req.options.headers or None)
        return result.to_normalized_dict(include_text=True, include_parsed=False)
    except Exception as exc:
        return _error_response(exc)


@app.post("/parse")
def parse(req: ParseRequest):
    config = _build_config(req.options)
    try:
        with Crawler(config=config, proxies=req.options.proxies or None) as crawler:
            result = crawler.get(req.url, headers=req.options.headers or None)
        return result.to_normalized_dict(include_text=True, include_parsed=True)
    except Exception as exc:
        return _error_response(exc)


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    try:
        checker = RobotsChecker(timeout=req.timeout)
        allowed, reason, crawl_delay = checker.check(
            req.url,
            user_agent=req.user_agent,
            mode=req.robots_mode,
        )
        return normalize_analysis_payload(
            req.url,
            allowed,
            reason,
            crawl_delay,
            req.robots_mode,
        )
    except Exception as exc:
        return _error_response(exc)
