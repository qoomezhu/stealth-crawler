"""
HTML 解析示例
"""

import sys
sys.path.append('..')

from crawler import StealthCrawler
from bs4 import BeautifulSoup


def example_beautifulsoup():
    """示例：使用 BeautifulSoup 解析"""
    print("\n" + "="*50)
    print("示例：BeautifulSoup 解析")
    print("="*50)
    
    crawler = StealthCrawler(delay_range=(0.5, 1))
    
    response = crawler.get("https://httpbin.org/html")
    
    # 使用 BeautifulSoup 解析
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 提取标题
    title = soup.find('title')
    print(f"页面标题：{title.text if title else 'N/A'}")
    
    # 提取所有链接
    links = soup.find_all('a')
    print(f"\n找到 {len(links)} 个链接：")
    for link in links[:5]:
        print(f"  - {link.get('href')}: {link.text[:50]}")
    
    # 提取特定元素
    h1 = soup.find('h1')
    print(f"\nH1 标题：{h1.text if h1 else 'N/A'}")


def example_extract_data():
    """示例：提取结构化数据"""
    print("\n" + "="*50)
    print("示例：提取结构化数据")
    print("="*50)
    
    crawler = StealthCrawler(delay_range=(0.5, 1))
    
    response = crawler.get("https://httpbin.org/html")
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 提取所有文本
    text = soup.get_text(strip=True)
    print(f"页面文本长度：{len(text)} 字符")
    print(f"前 200 字符：{text[:200]}...")
    
    # 提取所有图片
    images = soup.find_all('img')
    print(f"\n找到 {len(images)} 张图片")
    
    # 提取所有段落
    paragraphs = soup.find_all('p')
    print(f"找到 {len(paragraphs)} 个段落")


def example_css_selectors():
    """示例：CSS 选择器"""
    print("\n" + "="*50)
    print("示例：CSS 选择器")
    print("="*50)
    
    crawler = StealthCrawler(delay_range=(0.5, 1))
    
    response = crawler.get("https://httpbin.org/html")
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 使用 CSS 选择器
    print("CSS 选择器示例：")
    
    # 选择所有链接
    links = soup.select('a')
    print(f"\na 标签数量：{len(links)}")
    
    # 选择特定类名
    # elements = soup.select('.class-name')
    
    # 选择特定 ID
    # element = soup.select_one('#element-id')
    
    # 组合选择器
    # elements = soup.select('div.content > p')


def example_navigation():
    """示例：页面导航"""
    print("\n" + "="*50)
    print("示例：页面导航")
    print("="*50)
    
    crawler = StealthCrawler(delay_range=(0.5, 1))
    
    # 获取第一页
    response = crawler.get("https://httpbin.org/html")
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 查找导航链接
    nav_links = soup.find_all('a')
    
    print(f"找到 {len(nav_links)} 个导航链接")
    
    # 模拟点击链接
    if nav_links:
        link = nav_links[0].get('href')
        if link and link.startswith('http'):
            print(f"\n导航到：{link}")
            response2 = crawler.get(link)
            print(f"新页面状态码：{response2.status_code}")


if __name__ == "__main__":
    example_beautifulsoup()
    example_extract_data()
    example_css_selectors()
    example_navigation()
    
    print("\n" + "="*50)
    print("✅ 所有解析示例完成！")
    print("="*50)
