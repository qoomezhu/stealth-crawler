"""
基础用法示例
"""

import sys
sys.path.append('..')

from crawler import StealthCrawler, scrape


def example_1_basic():
    """示例 1: 基础请求"""
    print("\n" + "="*50)
    print("示例 1: 基础请求")
    print("="*50)
    
    crawler = StealthCrawler(delay_range=(0.5, 1))
    
    response = crawler.get("https://httpbin.org/html")
    print(f"状态码：{response.status_code}")
    print(f"响应长度：{len(response.text)} 字节")
    print(f"统计：{crawler.get_stats()}")


def example_2_custom_headers():
    """示例 2: 自定义请求头"""
    print("\n" + "="*50)
    print("示例 2: 自定义请求头")
    print("="*50)
    
    crawler = StealthCrawler(delay_range=(0.5, 1))
    
    custom_headers = {
        "X-Custom-Header": "MyValue",
        "Referer": "https://google.com",
    }
    
    response = crawler.get(
        "https://httpbin.org/headers",
        headers=custom_headers
    )
    print(f"响应：{response.text[:500]}...")


def example_3_quick_scrape():
    """示例 3: 快速爬取"""
    print("\n" + "="*50)
    print("示例 3: 快速爬取函数")
    print("="*50)
    
    response = scrape("https://httpbin.org/ip", delay_range=(0.5, 1))
    print(f"IP 信息：{response.text}")


def example_4_post_request():
    """示例 4: POST 请求"""
    print("\n" + "="*50)
    print("示例 4: POST 请求")
    print("="*50)
    
    crawler = StealthCrawler(delay_range=(0.5, 1))
    
    data = {
        "username": "testuser",
        "email": "test@example.com",
    }
    
    response = crawler.post(
        "https://httpbin.org/post",
        data=data
    )
    print(f"POST 响应：{response.text[:500]}...")


if __name__ == "__main__":
    example_1_basic()
    example_2_custom_headers()
    example_3_quick_scrape()
    example_4_post_request()
    
    print("\n" + "="*50)
    print("✅ 所有示例完成！")
    print("="*50)
