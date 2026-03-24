import random
import time
from typing import Any, Dict, Optional

try:
    from curl_cffi import requests as httpx
except Exception:
    import requests as httpx

from .config import CrawlerConfig
from .exceptions import RobotsBlockedError, RetryExhaustedError
from .logger import get_logger
from .models import FetchResult
from .proxy import ProxyPool
from .robots import RobotsChecker

RETRY_STATUS = {429, 500, 502, 503, 504}


class Crawler:
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
        self.session = httpx.Session()
        self.stats = {"requests": 0, "success": 0, "failed": 0, "retries": 0}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def close(self):
        try:
            self.session.close()
        except Exception:
            pass

    def _delay(self):
        lo, hi = self.config.delay_range
        time.sleep(random.uniform(lo, hi))

    def _headers(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = self.config.default_headers.copy()
        if self.config.rotate_user_agent and self.config.user_agents:
            headers["User-Agent"] = random.choice(self.config.user_agents)
        if extra:
            headers.update(extra)
        return headers

    def _backoff(self, attempt: int) -> float:
        return self.config.backoff_factor * (2 ** max(0, attempt - 1))

    def _request(
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
        if self.config.respect_robots:
            ua_for_check = headers.get("User-Agent") if headers else "*"
            allowed, reason, delay = self.robots.check(url, user_agent=ua_for_check or "*", mode=self.config.robots_mode)
            if not allowed:
                raise RobotsBlockedError(reason)
            if delay:
                time.sleep(delay)

        self._delay()
        final_error: Any = None

        for attempt in range(1, self.config.max_retries + 2):
            proxy_url = self.proxy_pool.get_proxy_url()
            proxies = self.proxy_pool.to_requests_dict(proxy_url)

            try:
                self.stats["requests"] += 1
                started = time.monotonic()
                resp = self.session.request(
                    method=method.upper(),
                    url=url,
                    headers=self._headers(headers),
                    params=params,
                    data=data,
                    json=json,
                    proxies=proxies,
                    timeout=self.config.timeout,
                    allow_redirects=allow_redirects,
                    **kwargs,
                )
                elapsed = time.monotonic() - started

                if resp.status_code in RETRY_STATUS:
                    self.stats["retries"] += 1
                    self.proxy_pool.mark_failure(proxy_url)
                    final_error = f"retryable status {resp.status_code}"
                    time.sleep(self._backoff(attempt))
                    continue

                self.proxy_pool.mark_success(proxy_url)
                self.stats["success"] += 1
                return FetchResult(
                    url=url,
                    final_url=getattr(resp, "url", url),
                    status_code=resp.status_code,
                    headers=dict(resp.headers),
                    text=resp.text,
                    content=resp.content,
                    elapsed=elapsed,
                    ok=200 <= resp.status_code < 400,
                    meta={"proxy": proxy_url},
                )
            except Exception as exc:
                self.stats["retries"] += 1
                self.proxy_pool.mark_failure(proxy_url)
                final_error = exc
                time.sleep(self._backoff(attempt))

        self.stats["failed"] += 1
        raise RetryExhaustedError(str(final_error))

    def get(self, url: str, **kwargs: Any) -> FetchResult:
        return self._request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> FetchResult:
        return self._request("POST", url, **kwargs)
