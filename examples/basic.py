from stealth_crawler import Crawler, AsyncCrawler, HTMLParser


def main():
    with Crawler() as crawler:
        result = crawler.get("https://httpbin.org/html")
        print("sync status:", result.status_code)
        print("title:", HTMLParser.title(result.text))


if __name__ == "__main__":
    main()
