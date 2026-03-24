from dataclasses import asdict, dataclass, field
from typing import Dict, Any
import base64
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

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["content_b64"] = base64.b64encode(self.content).decode("ascii")
        data["content_length"] = len(self.content)
        data.pop("content", None)
        return data
