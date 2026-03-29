from base64 import b64encode
from typing import Any, Dict, Mapping, Optional

from .parser import HTMLParser


def normalize_headers(headers: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        str(key).lower(): headers[key]
        for key in sorted(headers, key=lambda item: str(item).lower())
    }


def normalize_fetch_payload(
    result: Any,
    *,
    include_text: bool = True,
    include_parsed: bool = False,
    preview_chars: int = 0,
) -> Dict[str, Any]:
    headers = normalize_headers(getattr(result, "headers", {}) or {})
    text = getattr(result, "text", "") or ""
    content = getattr(result, "content", b"") or b""

    payload: Dict[str, Any] = {
        "kind": "fetch",
        "request": {
            "url": getattr(result, "url", ""),
            "final_url": getattr(result, "final_url", ""),
        },
        "response": {
            "status_code": int(getattr(result, "status_code", 0)),
            "ok": bool(getattr(result, "ok", False)),
            "elapsed_seconds": round(float(getattr(result, "elapsed", 0.0)), 3),
            "headers": headers,
        },
        "content": {
            "encoding": "base64",
            "base64": b64encode(content).decode("ascii"),
            "length": len(content),
        },
        "meta": getattr(result, "meta", {}) or {},
    }

    if include_text:
        payload["content"]["text"] = text
    if preview_chars > 0:
        payload["content"]["preview"] = text[:preview_chars]
    if include_parsed:
        payload["parsed"] = {
            "title": HTMLParser.title(text),
            "links": HTMLParser.links(text, getattr(result, "final_url", None)),
            "meta": HTMLParser.meta(text),
        }

    return payload


def normalize_analysis_payload(
    url: str,
    allowed: bool,
    reason: str,
    crawl_delay: Optional[float],
    robots_mode: str,
) -> Dict[str, Any]:
    return {
        "kind": "robots-analysis",
        "request": {"url": url},
        "decision": {
            "allowed": allowed,
            "reason": reason,
            "crawl_delay": crawl_delay,
            "robots_mode": robots_mode,
        },
    }
