from pydantic import BaseModel, Field
from typing import Dict, List


class CrawlOptions(BaseModel):
    timeout: int = 20
    max_retries: int = 3
    delay_min: float = 0.5
    delay_max: float = 1.5
    robots_mode: str = "strict"
    respect_robots: bool = True
    rotate_user_agent: bool = True
    require_proxy: bool = False
    proxies: List[str] = Field(default_factory=list)
    headers: Dict[str, str] = Field(default_factory=dict)
