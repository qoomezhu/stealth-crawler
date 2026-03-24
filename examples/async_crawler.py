"""
异步爬虫示例
"""

import sys
sys.path.append('..')

import asyncio
from crawler import AsyncStealthCrawler


async def example_async_single():
    """示例：异步单请求"""
    print("\n" + "="*50)
    print("示例：异步单请求")
    print("="*50)
    
    crawler = AsyncStealthCrawler(delay_range=(0.5, 1))
    
    response = await crawler.get("https://httpbin.org/html")
    print(f"响应长度：{len(response)} 字节")
    print(f"统计：{crawler.get_stats()}")


async def example_async_concurrent():
    """示例：异步并发请求"""
    print("\n" + "="*50)
    print("示例：异步并发请求")
    print("="*50)
    
    urls = [
        "https://httpbin.org/html",
        "https://httpbin.org/headers",
        "https://httpbin.org/ip",
        "https://httpbin.org/user-agent",
        "https://httpbin.org/get",
    ]
    
    crawler = AsyncStealthCrawler(delay_range=(0.3, 0.8))
    
    print(f"\n并发请求 {len(urls)} 个 URL...")
    
    tasks = [crawler.get(url) for url in urls]
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    
    for i, resp in enumerate(responses):
        if isinstance(resp, Exception):
            print(f"  URL {i+1}: ❌ 失败 - {resp}")
        else:
            print(f"  URL {i+1}: ✅ 成功 - {len(resp)} 字节")
    
    print(f"\n📊 统计：{crawler.get_stats()}")


async def example_async_with_proxy():
    """示例：异步代理轮换"""
    print("\n" + "="*50)
    print("示例：异步代理轮换")
    print("="*50)
    
    proxies = [
        "http://proxy1.example.com:8080",
        "http://proxy2.example.com:8080",
    ]
    
    crawler = AsyncStealthCrawler(
        proxies=proxies,
        rotate_proxy=True,
        delay_range=(0.5, 1),
    )
    
    urls = [
        "https://httpbin.org/ip",
        "https://httpbin.org/ip",
        "https://httpbin.org/ip",
    ]
    
    print("\n使用代理轮换请求...")
    
    tasks = [crawler.get(url) for url in urls]
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    
    for i, resp in enumerate(responses):
        if isinstance(resp, Exception):
            print(f"  请求 {i+1}: ❌ 失败")
        else:
            print(f"  请求 {i+1}: ✅ {resp[:150]}...")


async def main():
    """运行所有示例"""
    await example_async_single()
    await example_async_concurrent()
    # await example_async_with_proxy()  # 需要真实代理
    
    print("\n" + "="*50)
    print("✅ 所有异步示例完成！")
    print("="*50)


if __name__ == "__main__":
    asyncio.run(main())
