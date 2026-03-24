class CrawlerError(Exception):
    """Base crawler exception."""


class RobotsBlockedError(CrawlerError):
    """Raised when robots.txt blocks a URL."""


class ProxyError(CrawlerError):
    """Raised when proxy handling fails."""


class RetryExhaustedError(CrawlerError):
    """Raised when all retries are exhausted."""


class ParseError(CrawlerError):
    """Raised when parsing fails."""
