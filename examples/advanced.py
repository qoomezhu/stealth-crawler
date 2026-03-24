"""
高级功能示例
"""

import sys
sys.path.append('..')

import time
from crawler import StealthCrawler


def example_retry_mechanism():
    """示例：重试机制"""
    print("\n" + "="*50)
    print("示例：重试机制")
    print("="*50)
    
    # 配置重试次数
    crawler = StealthCrawler(
        max_retries=5,
        delay_range=(0.5, 1),
    )
    
    print(f"最大重试次数：{crawler.max_retries}")
    
    # 故意请求一个可能失败的 URL
    try:
        response = crawler.get("https://httpbin.org/status/429")
        print(f"响应状态码：{response.status_code}")
    except Exception as e:
        print(f"请求失败（预期）：{e}")
    
    print(f"统计：{crawler.get_stats()}")


def example_rate_limiting():
    """示例：请求限流"""
    print("\n" + "="*50)
    print("示例：请求限流")
    print("="*50)
    
    # 配置延迟范围
    crawler = StealthCrawler(
        delay_range=(2, 4),  # 2-4 秒延迟
        rotate_ua=True,
    )
    
    print("发送 3 个请求，每个间隔 2-4 秒...")
    
    start_time = time.time()
    
    for i in range(3):
        response = crawler.get("https://httpbin.org/ip")
        elapsed = time.time() - start_time
        print(f"  请求 {i+1}: 状态码 {response.status_code}, 累计耗时 {elapsed:.1f}s")
    
    total_time = time.time() - start_time
    print(f"\n总耗时：{total_time:.1f}s")
    print(f"统计：{crawler.get_stats()}")


def example_session_persistence():
    """示例：会话持久化"""
    print("\n" + "="*50)
    print("示例：会话持久化")
    print("="*50)
    
    crawler = StealthCrawler(delay_range=(0.5, 1))
    
    # 第一次请求 - 建立会话
    print("第一次请求...")
    response1 = crawler.get("https://httpbin.org/cookies/set/test_cookie/test_value")
    print(f"设置 Cookie: {response1.status_code}")
    
    # 第二次请求 - 使用相同会话
    print("\n第二次请求（携带 Cookie）...")
    response2 = crawler.get("https://httpbin.org/cookies")
    print(f"Cookie 信息：{response2.text}")


def example_stats_tracking():
    """示例：统计跟踪"""
    print("\n" + "="*50)
    print("示例：统计跟踪")
    print("="*50)
    
    crawler = StealthCrawler(delay_range=(0.3, 0.8))
    
    # 发送多个请求
    urls = [
        "https://httpbin.org/html",
        "https://httpbin.org/headers",
        "https://httpbin.org/ip",
        "https://httpbin.org/user-agent",
    ]
    
    print(f"发送 {len(urls)} 个请求...")
    
    for url in urls:
        try:
            response = crawler.get(url)
            print(f"  ✅ {url.split('/')[-1]}: {response.status_code}")
        except Exception as e:
            print(f"  ❌ {url}: {e}")
    
    # 获取统计
    stats = crawler.get_stats()
    print(f"\n📊 最终统计：")
    print(f"  总请求数：{stats['requests']}")
    print(f"  成功数：{stats['success']}")
    print(f"  失败数：{stats['failed']}")
    print(f"  重试次数：{stats['retries']}")
    
    # 重置统计
    crawler.reset_stats()
    print(f"\n重置后统计：{crawler.get_stats()}")


def example_custom_impersonation():
    """示例：自定义浏览器模拟"""
    print("\n" + "="*50)
    print("示例：浏览器模拟")
    print("="*50)
    
    crawler = StealthCrawler(
        delay_range=(0.5, 1),
        rotate_ua=True,
    )
    
    # 检查 User-Agent
    print(f"当前 User-Agent：{crawler.current_ua or '未设置'}")
    
    # 发送请求
    response = crawler.get("https://httpbin.org/user-agent")
    print(f"\n服务器看到的 User-Agent：{response.text}")


if __name__ == "__main__":
    example_retry_mechanism()
    example_rate_limiting()
    example_session_persistence()
    example_stats_tracking()
    example_custom_impersonation()
    
    print("\n" + "="*50)
    print("✅ 所有高级示例完成！")
    print("="*50)
