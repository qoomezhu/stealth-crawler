import asyncio
import random
import time
from typing import Any, Dict, Optional

import aiohttp

from .config import CrawlerConfig
from .exceptions import ProxyError, RetryExhaustedError, RobotsBlockedError
from .logger import get_logger
from .models import FetchResult
from .proxy import ProxyPool
from .robots import RobotsChecker

RETRY_STATUS = {429, 500, 502, 503, 504}


class AsyncCrawler:
    def __init__(
        self,
        config: Optional[CrawlerConfig] = None,
        proxies: Optional[list[str]] = None,
        log_file: Optional[str] = None,
    ):
        self.config = config or CrawlerConfig()
        self.logger = get_logger(level=self.config.log_level, log_file=log_file)
        self.proxy_pool = ProxyPool(proxies=proxies, rotate=True) if proxies else ProxyPool()
        self.robots = RobotsChecker(timeout=min(10, self.config.timeout))
        self.session: Optional[aiohttp.ClientSession] = None
        self.stats = {"requests": 0, "success": 0, "failed": 0, "retries": 0}

    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers=self.config.default_headers.copy(),
        )
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.session:
            await self.session.close()

    def _headers(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = self.config.default_headers.copy()
        if self.config.rotate_user_agent and self.config.user_agents:
            headers["User-Agent"] = random.choice(self.config.user_agents)
        if extra:
            headers.update(extra)
        return headers

    def _backoff(self, attempt: int) -> float:
        return self.config.backoff_factor * (2 ** max(0, attempt - 1))

    async def _delay(self):
        lo, hi = sorted(self.config.delay_range)
        await asyncio.sleep(random.uniform(lo, hi))

    async def _request(
        self,
        method: str,
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        params=None,
        data=None,
        json=None,
        allow_redirects: bool = True,
        **kwargs: Any,
    ) -> FetchResult:
        if self.session is None:
            raise RuntimeError("Use `async with AsyncCrawler() as crawler:` first")

        if self.config.require_proxy and not self.proxy_pool.has_available_proxy():
            self.stats["failed"] += 1
            raise ProxyError("Proxy access required but no available proxies were found")

        if self.config.respect_robots:
            ua_for_check = headers.get("User-Agent") if headers else "*"
            allowed, reason, delay = self.robots.check(
                url,
                user_agent=ua_for_check or "*",
                mode=self.config.robots_mode,
            )
            if not allowed:
                raise RobotsBlockedError(reason)
            if delay:
                await asyncio.sleep(delay)

        await self._delay()
        final_error: Any = None

        for attempt in range(1, self.config.max_retries + 2):
            proxy_url = self.proxy_pool.get_proxy_url()
            try:
                self.stats["requests"] += 1
                started = time.monotonic()
                async with self.session.request(
                    method.upper(),
                    url,
                    headers=self._headers(headers),
                    params=params,
                    data=data,
                    json=json,
                    proxy=proxy_url,
                    allow_redirects=allow_redirects,
                    **kwargs,
                ) as resp:
                    text = await resp.text(errors="ignore")
                    content = await resp.read()
                    elapsed = time.monotonic() - started

                    if resp.status in RETRY_STATUS:
                        self.stats["retries"] += 1
                        self.proxy_pool.mark_failure(proxy_url)
                        final_error = f"retryable status {resp.status}"
                        if self.config.require_proxy and not self.proxy_pool.has_available_proxy():
                            raise ProxyError("Proxy access required but all proxies are exhausted")
                        await asyncio.sleep(self._backoff(attempt))
                        continue

                    self.proxy_pool.mark_success(proxy_url)
                    self.stats["success"] += 1
                    return FetchResult(
                        url=url,
                        final_url=str(resp.url),
                        status_code=resp.status,
                        headers=dict(resp.headers),
                        text=text,
                        content=content,
                        elapsed=elapsed,
                        ok=200 <= resp.status < 400,
                        meta={"proxy": proxy_url},
                    )
            except ProxyError:
                self.stats["failed"] += 1
                raise
            except Exception as exc:
                self.stats["retries"] += 1
                self.proxy_pool.mark_failure(proxy_url)
                final_error = exc
                if self.config.require_proxy and not self.proxy_pool.has_available_proxy():
                    raise ProxyError("Proxy access required but all proxies are exhausted")
                await asyncio.sleep(self._backoff(attempt))

        self.stats["failed"] += 1
        raise RetryExhaustedError(str(final_error))

    async def get(self, url: str, **kwargs: Any) -> FetchResult:
        return await self._request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> FetchResult:
        return await self._request("POST", url, **kwargs)
