import asyncio
import time
from collections import defaultdict, deque
from typing import Deque, Dict, Iterable, Optional, Set, Tuple

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityMiddleware(BaseHTTPMiddleware):
    """Combined API-key authentication and in-memory rate limiting middleware."""

    def __init__(
        self,
        app,
        api_key: Optional[str] = None,
        rate_limit_requests: int = 60,
        rate_limit_window: int = 60,
        bypass_paths: Optional[Iterable[str]] = None,
    ):
        super().__init__(app)
        self.api_key = api_key.strip() if api_key else None
        self.rate_limit_requests = max(0, int(rate_limit_requests))
        self.rate_limit_window = max(1, int(rate_limit_window))
        self.bypass_paths: Set[str] = set(bypass_paths or {"/health", "/docs", "/redoc", "/openapi.json"})
        self._requests: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

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
        return request.url.path in self.bypass_paths

    async def _check_rate_limit(self, request: Request) -> Tuple[bool, int, int, int]:
        """Return (allowed, limit, remaining, retry_after)."""
        if self.rate_limit_requests <= 0:
            return True, 0, 0, 0

        client_id = self._client_id(request)
        now = time.monotonic()

        async with self._lock:
            bucket = self._requests[client_id]
            while bucket and now - bucket[0] >= self.rate_limit_window:
                bucket.popleft()

            if len(bucket) >= self.rate_limit_requests:
                retry_after = max(1, int(self.rate_limit_window - (now - bucket[0])))
                return False, self.rate_limit_requests, 0, retry_after

            bucket.append(now)
            remaining = max(0, self.rate_limit_requests - len(bucket))
            return True, self.rate_limit_requests, remaining, 0

    async def dispatch(self, request: Request, call_next):
        if self._is_bypassed(request):
            return await call_next(request)

        if self.api_key:
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
