import itertools
import time
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class ProxyState:
    failures: int = 0
    disabled_until: float = 0.0


class ProxyPool:
    def __init__(
        self,
        proxies: Optional[List[str]] = None,
        rotate: bool = True,
        failure_threshold: int = 3,
        cooldown: int = 60,
    ):
        self.proxies = proxies or []
        self.rotate = rotate
        self.failure_threshold = failure_threshold
        self.cooldown = cooldown
        self._states: Dict[str, ProxyState] = {proxy: ProxyState() for proxy in self.proxies}
        self._cycle = itertools.cycle(self.proxies) if self.proxies else None

    def _available(self, proxy: str) -> bool:
        return time.monotonic() >= self._states[proxy].disabled_until

    def has_available_proxy(self) -> bool:
        return any(self._available(proxy) for proxy in self.proxies)

    def get_proxy_url(self) -> Optional[str]:
        if not self.proxies:
            return None

        if self.rotate:
            for _ in range(len(self.proxies)):
                proxy = next(self._cycle)
                if self._available(proxy):
                    return proxy
            return None

        for proxy in self.proxies:
            if self._available(proxy):
                return proxy
        return None

    @staticmethod
    def to_requests_dict(proxy_url: Optional[str]) -> Optional[Dict[str, str]]:
        if not proxy_url:
            return None
        return {"http": proxy_url, "https": proxy_url}

    def mark_success(self, proxy_url: Optional[str]):
        if not proxy_url or proxy_url not in self._states:
            return
        self._states[proxy_url].failures = 0

    def mark_failure(self, proxy_url: Optional[str]):
        if not proxy_url or proxy_url not in self._states:
            return
        state = self._states[proxy_url]
        state.failures += 1
        if state.failures >= self.failure_threshold:
            state.disabled_until = time.monotonic() + self.cooldown
            state.failures = 0
