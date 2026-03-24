from dataclasses import asdict
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .config import CrawlerConfig
from .crawler import Crawler
from .parser import HTMLParser
from .robots import RobotsChecker

app = FastAPI(title="Stealth Crawler API", version="2.0.0")


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


def _build_config(options: CrawlOptions) -> CrawlerConfig:
    return CrawlerConfig(
        timeout=options.timeout,
        max_retries=options.max_retries,
        delay_range=(options.delay_min, options.delay_max),
        robots_mode=options.robots_mode,
        respect_robots=options.respect_robots,
        rotate_user_agent=options.rotate_user_agent,
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
        return result.to_dict()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/parse")
def parse(req: ParseRequest):
    config = _build_config(req.options)
    try:
        with Crawler(config=config, proxies=req.options.proxies or None) as crawler:
            result = crawler.get(req.url, headers=req.options.headers or None)
        payload = result.to_dict()
        payload.update(
            {
                "title": HTMLParser.title(result.text),
                "links": HTMLParser.links(result.text, result.final_url),
                "meta": HTMLParser.meta(result.text),
            }
        )
        return payload
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    checker = RobotsChecker(timeout=req.timeout)
    allowed, reason, crawl_delay = checker.check(req.url, user_agent=req.user_agent, mode=req.robots_mode)
    return {
        "url": req.url,
        "allowed": allowed,
        "reason": reason,
        "crawl_delay": crawl_delay,
        "robots_mode": req.robots_mode,
    }
