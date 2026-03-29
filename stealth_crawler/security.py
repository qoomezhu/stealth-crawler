import asyncio
import time
from collections import defaultdict, deque
from typing import Deque, Dict, Iterable, Optional, Protocol, Set, Tuple

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitBackend(Protocol):
    async def check(
        self,
        client_id: str,
        limit: int,
        window: int,
    ) -> Tuple[bool, int, int, int]:
        ...


class InMemoryRateLimitBackend:
    def __init__(self):
        self._requests: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def check(
        self,
        client_id: str,
        limit: int,
        window: int,
    ) -> Tuple[bool, int, int, int]:
        if limit <= 0:
            return True, 0, 0, 0

        now = time.monotonic()
        async with self._lock:
            bucket = self._requests[client_id]
            while bucket and now - bucket[0] >= window:
                bucket.popleft()

            if len(bucket) >= limit:
                retry_after = max(1, int(window - (now - bucket[0])))
                return False, limit, 0, retry_after

            bucket.append(now)
            remaining = max(0, limit - len(bucket))
            return True, limit, remaining, 0


class RedisRateLimitBackend:
    def __init__(self, redis_url: str, key_prefix: str = "stealth_crawler:ratelimit"):
        if not redis_url:
            raise ValueError("redis_url is required for redis rate limiting")

        try:
            import redis.asyncio as redis
        except Exception as exc:
            raise RuntimeError("Redis rate limiting requires installing the 'redis' package") from exc

        self._redis = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        self._key_prefix = key_prefix

    async def aclose(self):
        close = getattr(self._redis, "aclose", None)
        if callable(close):
            await close()
            return

        close = getattr(self._redis, "close", None)
        if callable(close):
            result = close()
            if asyncio.iscoroutine(result):
                await result

    async def check(
        self,
        client_id: str,
        limit: int,
        window: int,
    ) -> Tuple[bool, int, int, int]:
        if limit <= 0:
            return True, 0, 0, 0

        key = f"{self._key_prefix}:{client_id}"
        now = int(time.time())
        script = """
        local key = KEYS[1]
        local limit = tonumber(ARGV[1])
        local window = tonumber(ARGV[2])
        local now = tonumber(ARGV[3])
        redis.call('ZREMRANGEBYSCORE', key, 0, now - window)
        local current = redis.call('ZCARD', key)
        if current >= limit then
            local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
            local retry_after = 1
            if oldest[2] then
                retry_after = math.max(1, math.floor(window - (now - tonumber(oldest[2]))))
            end
            return {0, limit, 0, retry_after}
        end
        redis.call('ZADD', key, now, now .. ':' .. tostring(current))
        redis.call('EXPIRE', key, window)
        return {1, limit, limit - current - 1, 0}
        """
        allowed, limit_value, remaining, retry_after = await self._redis.eval(
            script,
            1,
            key,
            limit,
            window,
            now,
        )
        return bool(int(allowed)), int(limit_value), int(remaining), int(retry_after)


class SecurityMiddleware(BaseHTTPMiddleware):
    """Combined API-key authentication and rate limiting middleware."""

    def __init__(
        self,
        app,
        api_key: Optional[str] = None,
        rate_limit_requests: int = 60,
        rate_limit_window: int = 60,
        rate_limit_backend: str = "memory",
        redis_url: Optional[str] = None,
        mcp_bearer_token: Optional[str] = None,
        bypass_paths: Optional[Iterable[str]] = None,
        mcp_public_paths: Optional[Iterable[str]] = None,
    ):
        super().__init__(app)
        self.api_key = api_key.strip() if api_key else None
        self.mcp_bearer_token = mcp_bearer_token.strip() if mcp_bearer_token else None
        self.rate_limit_requests = max(0, int(rate_limit_requests))
        self.rate_limit_window = max(1, int(rate_limit_window))
        self.bypass_paths: Set[str] = set(
            bypass_paths or {"/health", "/docs", "/redoc", "/openapi.json"}
        )
        self.mcp_public_paths: Set[str] = set(mcp_public_paths or {"/mcp/healthz"})
        self._backend = self._build_backend(rate_limit_backend, redis_url)

    def _build_backend(
        self,
        rate_limit_backend: str,
        redis_url: Optional[str],
    ) -> Optional[RateLimitBackend]:
        if self.rate_limit_requests <= 0:
            return None

        backend = (rate_limit_backend or "memory").strip().lower()
        if backend == "redis":
            if not redis_url:
                raise ValueError("CRAWLER_RATE_LIMIT_REDIS_URL is required for redis backend")
            return RedisRateLimitBackend(redis_url=redis_url)
        return InMemoryRateLimitBackend()

    def _extract_token(self, request: Request) -> Optional[str]:
        api_key = request.headers.get("x-api-key")
        if api_key:
            return api_key.strip()

        auth = request.headers.get("authorization", "")
        if auth.lower().startswith("bearer "):
            return auth.split(" ", 1)[1].strip()

        return None

    def _client_id(self, request: Request) -> str:
        if request.client and request.client.host:
            return request.client.host
        return "unknown"

    def _is_bypassed(self, request: Request) -> bool:
        path = request.url.path
        return path in self.bypass_paths or path in self.mcp_public_paths

    async def _check_rate_limit(self, request: Request) -> Tuple[bool, int, int, int]:
        """Return (allowed, limit, remaining, retry_after)."""
        if self.rate_limit_requests <= 0 or self._backend is None:
            return True, 0, 0, 0

        client_id = self._client_id(request)
        return await self._backend.check(
            client_id,
            self.rate_limit_requests,
            self.rate_limit_window,
        )

    async def dispatch(self, request: Request, call_next):
        if self._is_bypassed(request):
            return await call_next(request)

        path = request.url.path
        if path.startswith("/mcp"):
            if self.mcp_bearer_token:
                provided = self._extract_token(request)
                if provided != self.mcp_bearer_token:
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "Unauthorized"},
                        headers={"WWW-Authenticate": "Bearer"},
                    )
        elif self.api_key:
            provided = self._extract_token(request)
            if provided != self.api_key:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Unauthorized"},
                    headers={"WWW-Authenticate": "Bearer"},
                )

        allowed, limit, remaining, retry_after = await self._check_rate_limit(request)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "limit": limit,
                    "retry_after": retry_after,
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                },
            )

        response = await call_next(request)
        if self.rate_limit_requests > 0:
            response.headers["X-RateLimit-Limit"] = str(self.rate_limit_requests)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
