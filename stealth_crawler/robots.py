from functools import lru_cache
from typing import Optional, Tuple
from urllib.parse import urljoin, urlparse
from urllib import robotparser

try:
    from curl_cffi import requests as httpx
except Exception:
    import requests as httpx


class RobotsChecker:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def _robots_url(self, base_url: str) -> str:
        return urljoin(base_url.rstrip("/") + "/", "robots.txt")

    @lru_cache(maxsize=256)
    def _load_parser(self, base_url: str) -> Optional[robotparser.RobotFileParser]:
        robots_url = self._robots_url(base_url)
        try:
            response = httpx.get(robots_url, timeout=self.timeout)
            if response.status_code != 200:
                return None

            rp = robotparser.RobotFileParser()
            rp.set_url(robots_url)
            rp.parse(response.text.splitlines())
            return rp
        except Exception:
            return None

    def check(self, url: str, user_agent: str = "*", mode: str = "strict") -> Tuple[bool, str, Optional[float]]:
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        if mode == "ignore":
            return True, "robots.txt ignored", None

        rp = self._load_parser(base_url)
        if rp is None:
            return True, "no robots.txt", None

        can_fetch = rp.can_fetch(user_agent, url)
        crawl_delay = rp.crawl_delay(user_agent)

        if can_fetch:
            return True, "allowed by robots.txt", crawl_delay

        if mode == "warn":
            return True, "blocked by robots.txt, but allowed in warn mode", crawl_delay

        return False, "blocked by robots.txt", crawl_delay
