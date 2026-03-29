from dataclasses import dataclass, field
from typing import Dict, List, Tuple

DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
]

DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


@dataclass
class CrawlerConfig:
    timeout: int = 20
    max_retries: int = 3
    backoff_factor: float = 1.5
    delay_range: Tuple[float, float] = (0.5, 1.5)
    respect_robots: bool = True
    robots_mode: str = "strict"  # strict / warn / ignore
    rotate_user_agent: bool = True
    require_proxy: bool = False
    default_headers: Dict[str, str] = field(default_factory=lambda: DEFAULT_HEADERS.copy())
    user_agents: List[str] = field(default_factory=lambda: DEFAULT_USER_AGENTS.copy())
    log_level: str = "INFO"


def build_crawler_config(
    *,
    timeout: int = 20,
    max_retries: int = 3,
    delay_min: float = 0.5,
    delay_max: float = 1.5,
    robots_mode: str = "strict",
    respect_robots: bool = True,
    rotate_user_agent: bool = True,
    require_proxy: bool = False,
    log_level: str = "INFO",
) -> CrawlerConfig:
    timeout = max(1, int(timeout))
    max_retries = max(0, int(max_retries))
    lo, hi = sorted((float(delay_min), float(delay_max)))
    lo = max(0.0, lo)
    hi = max(lo, hi)
    return CrawlerConfig(
        timeout=timeout,
        max_retries=max_retries,
        delay_range=(lo, hi),
        robots_mode=robots_mode,
        respect_robots=respect_robots,
        rotate_user_agent=rotate_user_agent,
        require_proxy=require_proxy,
        log_level=log_level,
    )
