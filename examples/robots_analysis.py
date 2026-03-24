"""
Robots.txt 检查示例
"""

from stealth_crawler import Crawler, CrawlerConfig, RobotsChecker


def example_check_sites():
    print("\n" + "=" * 50)
    print("示例：检查网站 robots.txt")
    print("=" * 50)

    checker = RobotsChecker(timeout=10)
    sites = [
        "https://www.baidu.com/search",
        "https://www.taobao.com/search",
        "https://www.github.com/explore",
    ]

    for url in sites:
        allowed, reason, crawl_delay = checker.check(url, mode="strict")
        print(f"\nURL: {url}")
        print(f"  allowed: {allowed}")
        print(f"  reason: {reason}")
        print(f"  crawl_delay: {crawl_delay}")


def example_modes():
    print("\n" + "=" * 50)
    print("示例：robots_mode 三种模式")
    print("=" * 50)

    url = "https://www.baidu.com/search"
    for mode in ["strict", "warn", "ignore"]:
        checker = RobotsChecker(timeout=10)
        allowed, reason, crawl_delay = checker.check(url, mode=mode)
        print(f"\nmode={mode}")
        print(f"  allowed: {allowed}")
        print(f"  reason: {reason}")
        print(f"  crawl_delay: {crawl_delay}")


def example_fetch_with_mode():
    print("\n" + "=" * 50)
    print("示例：带 robots 策略的抓取")
    print("=" * 50)

    config = CrawlerConfig(
        robots_mode="warn",
        delay_range=(0.5, 1.0),
        timeout=15,
    )

    with Crawler(config=config) as crawler:
        result = crawler.get("https://httpbin.org/html")
        print(f"status_code: {result.status_code}")
        print(f"title: {result.text[:60]}")


if __name__ == "__main__":
    example_check_sites()
    example_modes()
    example_fetch_with_mode()
    print("\n" + "=" * 50)
    print("✅ Robots.txt 示例完成")
    print("=" * 50)
