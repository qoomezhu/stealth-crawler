import json
import unittest
from unittest.mock import Mock, patch

from stealth_crawler import (
    AsyncCrawler,
    Crawler,
    CrawlerConfig,
    FetchResult,
    HTMLParser,
    ProxyPool,
    RobotsChecker,
)
from stealth_crawler.config import build_crawler_config
from stealth_crawler.exceptions import RetryExhaustedError
from stealth_crawler.normalization import normalize_analysis_payload

try:
    from fastapi.testclient import TestClient
except Exception:
    TestClient = None


class TestHTMLParser(unittest.TestCase):
    def test_title_links_meta(self):
        html = """
        <html>
          <head>
            <title> Demo Page </title>
            <meta name="description" content="hello world" />
          </head>
          <body>
            <a href="/a">A</a>
            <a href="https://example.com/b">B</a>
          </body>
        </html>
        """
        self.assertEqual(HTMLParser.title(html), "Demo Page")
        self.assertEqual(
            HTMLParser.links(html, "https://example.com"),
            ["https://example.com/a", "https://example.com/b"],
        )
        self.assertEqual(HTMLParser.meta(html)["description"], "hello world")


class TestFetchResult(unittest.TestCase):
    def test_json(self):
        result = FetchResult(
            url="https://example.com/api",
            final_url="https://example.com/api",
            status_code=200,
            headers={},
            text=json.dumps({"ok": True}),
            content=b'{"ok": true}',
            elapsed=0.1,
            ok=True,
        )
        self.assertEqual(result.json()["ok"], True)

    def test_normalized_payload(self):
        result = FetchResult(
            url="https://example.com",
            final_url="https://example.com/home",
            status_code=200,
            headers={"Content-Type": "text/html"},
            text="<html><title>ok</title></html>",
            content=b"<html><title>ok</title></html>",
            elapsed=0.125,
            ok=True,
            meta={"proxy": "http://p1:8080"},
        )
        payload = result.to_normalized_dict(
            include_text=True,
            include_parsed=True,
            preview_chars=5,
        )
        self.assertEqual(payload["kind"], "fetch")
        self.assertEqual(payload["response"]["status_code"], 200)
        self.assertEqual(payload["content"]["length"], len(result.content))
        self.assertEqual(payload["content"]["preview"], "<html")
        self.assertEqual(payload["parsed"]["title"], "ok")


class TestConfig(unittest.TestCase):
    def test_build_crawler_config_normalizes_ranges(self):
        config = build_crawler_config(
            timeout=0,
            max_retries=-1,
            delay_min=2.5,
            delay_max=1.0,
            require_proxy=True,
        )
        self.assertEqual(config.timeout, 1)
        self.assertEqual(config.max_retries, 0)
        self.assertEqual(config.delay_range, (1.0, 2.5))
        self.assertTrue(config.require_proxy)


class TestProxyPool(unittest.TestCase):
    def test_rotation_and_disable(self):
        pool = ProxyPool(
            ["http://p1:8080", "http://p2:8080"],
            rotate=True,
            failure_threshold=1,
            cooldown=60,
        )
        first = pool.get_proxy_url()
        second = pool.get_proxy_url()
        self.assertIn(first, ["http://p1:8080", "http://p2:8080"])
        self.assertIn(second, ["http://p1:8080", "http://p2:8080"])
        self.assertNotEqual(first, second)
        pool.mark_failure(first)
        self.assertNotEqual(pool.get_proxy_url(), first)


class TestRobotsChecker(unittest.TestCase):
    def test_strict_and_warn_modes(self):
        class FakeParser:
            def can_fetch(self, ua, url):
                return False

            def crawl_delay(self, ua):
                return 2

        checker = RobotsChecker()
        with patch.object(RobotsChecker, "_load_parser", return_value=FakeParser()):
            allowed, reason, delay = checker.check("https://example.com/private", mode="strict")
            self.assertFalse(allowed)
            self.assertEqual(reason, "blocked by robots.txt")
            self.assertEqual(delay, 2)

            allowed, reason, delay = checker.check("https://example.com/private", mode="warn")
            self.assertTrue(allowed)
            self.assertIn("warn mode", reason)

            allowed, reason, delay = checker.check("https://example.com/private", mode="ignore")
            self.assertTrue(allowed)
            self.assertEqual(reason, "robots.txt ignored")


class TestCrawler(unittest.TestCase):
    def test_request_with_mock_response(self):
        crawler = Crawler(
            CrawlerConfig(
                respect_robots=False,
                delay_range=(0, 0),
                rotate_user_agent=False,
            )
        )
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><title>ok</title></html>"
        mock_response.content = b"<html><title>ok</title></html>"
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.url = "https://example.com"

        with patch.object(crawler.session, "request", return_value=mock_response):
            result = crawler.get("https://example.com")

        self.assertTrue(result.ok)
        self.assertEqual(result.status_code, 200)
        self.assertIn("title", result.text)
        crawler.close()


class TestAsyncCrawler(unittest.IsolatedAsyncioTestCase):
    async def test_async_request_with_mock_response(self):
        crawler = AsyncCrawler(
            CrawlerConfig(
                respect_robots=False,
                delay_range=(0, 0),
                rotate_user_agent=False,
            )
        )

        class FakeResponse:
            def __init__(self):
                self.status = 200
                self.headers = {"Content-Type": "text/html"}
                self.url = "https://example.com"

            async def text(self, errors="ignore"):
                return "<html><title>ok</title></html>"

            async def read(self):
                return b"<html><title>ok</title></html>"

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

        class FakeSession:
            def request(self, *args, **kwargs):
                return FakeResponse()

            async def close(self):
                return None

        crawler.session = FakeSession()
        result = await crawler.get("https://example.com")
        self.assertTrue(result.ok)
        self.assertEqual(result.status_code, 200)


class TestHTTPAPI(unittest.TestCase):
    def setUp(self):
        if TestClient is None:
            raise unittest.SkipTest("fastapi is not installed")
        from stealth_crawler.http_api import app

        self.client = TestClient(app)

    def test_fetch_returns_normalized_payload(self):
        class FakeResult:
            def to_normalized_dict(self, include_text=True, include_parsed=False, preview_chars=0):
                return {
                    "kind": "fetch",
                    "request": {
                        "url": "https://example.com",
                        "final_url": "https://example.com/home",
                    },
                    "response": {
                        "status_code": 200,
                        "ok": True,
                        "elapsed_seconds": 0.12,
                        "headers": {"content-type": "text/html"},
                    },
                    "content": {
                        "encoding": "base64",
                        "base64": "PGh0bWw+PC9odG1sPg==",
                        "length": 13,
                        "text": "<html></html>",
                    },
                    "meta": {"proxy": "http://proxy:8080"},
                }

        with patch("stealth_crawler.http_api.Crawler") as MockCrawler:
            crawler_instance = Mock()
            crawler_instance.get.return_value = FakeResult()
            MockCrawler.return_value.__enter__.return_value = crawler_instance

            response = self.client.post(
                "/fetch",
                json={"url": "https://example.com", "options": {"proxies": []}},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["kind"], "fetch")
        self.assertEqual(payload["response"]["status_code"], 200)
        self.assertEqual(payload["content"]["length"], 13)

    def test_fetch_maps_retry_exhausted_to_gateway_timeout(self):
        with patch("stealth_crawler.http_api.Crawler") as MockCrawler:
            crawler_instance = Mock()
            crawler_instance.get.side_effect = RetryExhaustedError("too many retries")
            MockCrawler.return_value.__enter__.return_value = crawler_instance

            response = self.client.post(
                "/fetch",
                json={"url": "https://example.com", "options": {"proxies": []}},
            )

        self.assertEqual(response.status_code, 504)
        self.assertEqual(response.json()["error"]["type"], "RetryExhaustedError")

    def test_analyze_returns_normalized_payload(self):
        payload = normalize_analysis_payload("https://example.com", True, "ok", None, "strict")
        self.assertEqual(payload["kind"], "robots-analysis")
        self.assertTrue(payload["decision"]["allowed"])


if __name__ == "__main__":
    unittest.main()
