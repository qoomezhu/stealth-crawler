from typing import Dict, List, Optional
import argparse
import json
import sys

from .config import build_crawler_config
from .crawler import Crawler
from .exceptions import CrawlerError
from .normalization import normalize_analysis_payload
from .parser import HTMLParser
from .robots import RobotsChecker


def _parse_headers(items: List[str]) -> Dict[str, str]:
    headers: Dict[str, str] = {}
    for item in items:
        if ":" not in item:
            raise argparse.ArgumentTypeError(f"Invalid header format: {item}. Use Key:Value")
        key, value = item.split(":", 1)
        headers[key.strip()] = value.strip()
    return headers


def _build_config(args: argparse.Namespace):
    return build_crawler_config(
        timeout=args.timeout,
        max_retries=args.max_retries,
        delay_min=args.delay_min,
        delay_max=args.delay_max,
        robots_mode=args.robots_mode,
        respect_robots=not args.no_robots,
        rotate_user_agent=not args.no_rotate_ua,
        require_proxy=args.require_proxy,
        log_level=args.log_level,
    )


def cmd_fetch(args: argparse.Namespace) -> int:
    config = _build_config(args)
    headers = _parse_headers(args.header)
    with Crawler(config=config, proxies=args.proxy or None, log_file=args.log_file) as crawler:
        result = crawler.get(args.url, headers=headers or None)

    if args.json:
        print(
            json.dumps(
                result.to_normalized_dict(
                    include_text=True,
                    include_parsed=False,
                    preview_chars=args.preview_chars,
                ),
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(f"status_code: {result.status_code}")
        print(f"final_url: {result.final_url}")
        print(f"elapsed: {result.elapsed:.3f}s")
        print(f"title: {HTMLParser.title(result.text)}")
        print(result.text[: args.preview_chars])
    return 0


def cmd_analyze(args: argparse.Namespace) -> int:
    checker = RobotsChecker(timeout=args.timeout)
    allowed, reason, crawl_delay = checker.check(args.url, user_agent=args.user_agent, mode=args.robots_mode)
    payload = normalize_analysis_payload(args.url, allowed, reason, crawl_delay, args.robots_mode)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"allowed: {allowed}")
        print(f"reason: {reason}")
        print(f"crawl_delay: {crawl_delay}")
    return 0


def cmd_parse(args: argparse.Namespace) -> int:
    config = _build_config(args)
    with Crawler(config=config, proxies=args.proxy or None, log_file=args.log_file) as crawler:
        result = crawler.get(args.url)

    payload = result.to_normalized_dict(include_text=True, include_parsed=True)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    try:
        import uvicorn
    except ImportError:
        print("Please install API extras: pip install '.[api]'", file=sys.stderr)
        return 2

    uvicorn.run(
        "stealth_crawler.http_api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level.lower(),
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="stealth-crawler", description="Stealth Crawler CLI")
    parser.add_argument("--log-level", default="INFO", help="logging level")
    sub = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--timeout", type=int, default=20)
    common.add_argument("--max-retries", type=int, default=3)
    common.add_argument("--delay-min", type=float, default=0.5)
    common.add_argument("--delay-max", type=float, default=1.5)
    common.add_argument("--robots-mode", choices=["strict", "warn", "ignore"], default="strict")
    common.add_argument("--no-robots", action="store_true", help="disable robots checking")
    common.add_argument("--no-rotate-ua", action="store_true")
    common.add_argument("--require-proxy", action="store_true", help="fail when no proxy is available")
    common.add_argument("--proxy", action="append", default=[], help="proxy url, repeatable")
    common.add_argument("--log-file", default=None)

    fetch = sub.add_parser("fetch", parents=[common], help="fetch a url")
    fetch.add_argument("url")
    fetch.add_argument("--header", action="append", default=[], help="custom header in Key:Value format")
    fetch.add_argument("--json", action="store_true", help="output as json")
    fetch.add_argument("--preview-chars", type=int, default=1000)
    fetch.set_defaults(func=cmd_fetch)

    analyze = sub.add_parser("analyze", parents=[common], help="analyze robots.txt")
    analyze.add_argument("url")
    analyze.add_argument("--json", action="store_true", help="output as json")
    analyze.add_argument("--user-agent", default="*")
    analyze.set_defaults(func=cmd_analyze)

    parse = sub.add_parser("parse", parents=[common], help="fetch and parse a page")
    parse.add_argument("url")
    parse.add_argument("--json", action="store_true", help="output as json")
    parse.set_defaults(func=cmd_parse)

    serve = sub.add_parser("serve", help="run the HTTP API server")
    serve.add_argument("--host", default="0.0.0.0")
    serve.add_argument("--port", type=int, default=8080)
    serve.add_argument("--reload", action="store_true")
    serve.add_argument("--log-level", default="info")
    serve.set_defaults(func=cmd_serve)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except CrawlerError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
