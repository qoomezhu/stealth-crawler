from dataclasses import dataclass, field
from typing import Dict, Any
import json


@dataclass
class FetchResult:
    url: str
    final_url: str
    status_code: int
    headers: Dict[str, str]
    text: str
    content: bytes
    elapsed: float
    ok: bool = False
    meta: Dict[str, Any] = field(default_factory=dict)

    def json(self) -> Any:
        return json.loads(self.text)
