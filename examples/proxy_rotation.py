"""
代理轮换示例
"""

import sys
sys.path.append('..')

from crawler import StealthCrawler


def example_proxy_rotation():
    """示例：使用代理轮换"""
    print("\n" + "="*50)
    print("示例：代理轮换")
    print("="*50)
    
    # 示例代理列表 (请替换为真实代理)
    proxies = [
        "http://proxy1.example.com:8080",
        "http://proxy2.example.com:8080",
        "http://proxy3.example.com:8080",
    ]
    
    # 创建带代理轮换的爬虫
    crawler = StealthCrawler(
        proxies=proxies,
        rotate_proxy=True,  # 启用代理轮换
        rotate_ua=True,     # 启用 UA 轮换
        delay_range=(1, 2),
    )
    
    print("\n发送 5 个请求，观察代理轮换...")
    
    for i in range(5):
        try:
            response = crawler.get("https://httpbin.org/ip")
            print(f"\n请求 {i+1}:")
            print(f"  状态码：{response.status_code}")
            print(f"  响应：{response.text.strip()[:200]}")
        except Exception as e:
            print(f"\n请求 {i+1} 失败：{e}")
    
    print(f"\n📊 最终统计：{crawler.get_stats()}")


def example_sticky_session():
    """示例：粘性会话 (固定代理)"""
    print("\n" + "="*50)
    print("示例：粘性会话")
    print("="*50)
    
    proxies = [
        "http://proxy1.example.com:8080",
    ]
    
    # 不启用轮换，使用固定代理
    crawler = StealthCrawler(
        proxies=proxies,
        rotate_proxy=False,  # 不轮换
        rotate_ua=True,
    )
    
    print("\n所有请求使用同一个代理...")
    
    for i in range(3):
        try:
            response = crawler.get("https://httpbin.org/ip")
            print(f"请求 {i+1}: {response.text.strip()[:150]}")
        except Exception as e:
            print(f"请求 {i+1} 失败：{e}")


if __name__ == "__main__":
    print("⚠️  注意：请替换为真实可用的代理服务器")
    print("以下示例使用占位符代理，实际运行会失败")
    print("="*50)
    
    # 注释掉实际运行，仅展示代码结构
    # example_proxy_rotation()
    # example_sticky_session()
    
    print("\n📝 代码结构已展示，请替换真实代理后运行")
