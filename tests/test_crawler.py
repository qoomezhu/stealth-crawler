import json
import unittest
from unittest.mock import Mock, patch

from stealth_crawler import Crawler, CrawlerConfig, FetchResult, HTMLParser, ProxyPool, RobotsChecker


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
        self.assertEqual(HTMLParser.links(html, "https://example.com"), ["https://example.com/a", "https://example.com/b"])
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


class TestProxyPool(unittest.TestCase):
    def test_rotation_and_disable(self):
        pool = ProxyPool(["http://p1:8080", "http://p2:8080"], rotate=True, failure_threshold=1, cooldown=60)
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
        crawler = Crawler(CrawlerConfig(respect_robots=False, delay_range=(0, 0), rotate_user_agent=False))
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


if __name__ == "__main__":
    unittest.main()
