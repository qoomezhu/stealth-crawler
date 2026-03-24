from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from urllib.parse import urljoin


class HTMLParser:
    @staticmethod
    def soup(html: str) -> BeautifulSoup:
        return BeautifulSoup(html, "html.parser")

    @staticmethod
    def title(html: str) -> str:
        soup = HTMLParser.soup(html)
        return soup.title.text.strip() if soup.title and soup.title.text else ""

    @staticmethod
    def links(html: str, base_url: Optional[str] = None) -> List[str]:
        soup = HTMLParser.soup(html)
        results: List[str] = []
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"].strip()
            results.append(urljoin(base_url, href) if base_url else href)
        return results

    @staticmethod
    def meta(html: str) -> Dict[str, str]:
        soup = HTMLParser.soup(html)
        result: Dict[str, str] = {}
        for tag in soup.find_all("meta"):
            key = tag.get("name") or tag.get("property")
            value = tag.get("content")
            if key and value:
                result[key] = value
        return result
