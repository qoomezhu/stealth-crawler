"""
Stealth Crawler - 高级反爬虫爬虫

功能:
- User-Agent 轮换
- 代理轮换
- TLS 指纹模拟 (curl_cffi)
- 智能请求节流
- Cookie 会话管理
- 自动重试机制
"""

import random
import time
import asyncio
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse

try:
    from curl_cffi import requests as curl_requests
    HAS_CURL_CFFI = True
except ImportError:
    HAS_CURL_CFFI = False
    import requests

from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from config import (
    USER_AGENTS,
    DEFAULT_HEADERS,
    CRAWLER_CONFIG,
    RETRY_STATUS_CODES,
)


class StealthCrawler:
    """
     stealth 爬虫类 - 支持反检测功能
    """
    
    def __init__(
        self,
        proxies: Optional[List[str]] = None,
        rotate_proxy: bool = False,
        rotate_ua: bool = True,
        delay_range: tuple = (1, 3),
        max_retries: int = 3,
        timeout: int = 30,
    ):
        """
        初始化爬虫
        
        Args:
            proxies: 代理服务器列表
            rotate_proxy: 是否轮换代理
            rotate_ua: 是否轮换 User-Agent
            delay_range: 请求延迟范围 (秒)
            max_retries: 最大重试次数
            timeout: 请求超时时间
        """
        self.proxies = proxies or []
        self.rotate_proxy = rotate_proxy and len(proxies) > 0
        self.rotate_ua = rotate_ua
        self.delay_range = delay_range
        self.max_retries = max_retries
        self.timeout = timeout
        
        # User-Agent 管理器
        self.ua = UserAgent()
        self.current_ua = None
        
        # 代理索引
        self.proxy_index = 0
        
        # 会话管理
        self.session = self._create_session()
        
        # 统计信息
        self.stats = {
            "requests": 0,
            "success": 0,
            "failed": 0,
            "retries": 0,
        }
    
    def _create_session(self):
        """创建 HTTP 会话"""
        if HAS_CURL_CFFI:
            return curl_requests.Session()
        else:
            return requests.Session()
    
    def _get_user_agent(self) -> str:
        """获取 User-Agent"""
        if self.rotate_ua:
            # 优先使用 fake-useragent 生成真实 UA
            try:
                self.current_ua = self.ua.random
            except Exception:
                self.current_ua = random.choice(USER_AGENTS)
        else:
            self.current_ua = USER_AGENTS[0]
        
        return self.current_ua
    
    def _get_proxy(self) -> Optional[Dict[str, str]]:
        """获取代理"""
        if not self.proxies:
            return None
        
        if self.rotate_proxy:
            # 轮换代理
            proxy_url = self.proxies[self.proxy_index]
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        else:
            # 使用第一个代理
            proxy_url = self.proxies[0]
        
        return {
            "http": proxy_url,
            "https": proxy_url,
        }
    
    def _get_headers(self, custom_headers: Optional[Dict] = None) -> Dict[str, str]:
        """构建请求头"""
        headers = DEFAULT_HEADERS.copy()
        headers["User-Agent"] = self._get_user_agent()
        
        if custom_headers:
            headers.update(custom_headers)
        
        return headers
    
    def _apply_delay(self):
        """应用随机延迟"""
        delay = random.uniform(self.delay_range[0], self.delay_range[1])
        time.sleep(delay)
    
    def _should_retry(self, status_code: int) -> bool:
        """判断是否应该重试"""
        return status_code in RETRY_STATUS_CODES
    
    def get(
        self,
        url: str,
        headers: Optional[Dict] = None,
        params: Optional[Dict] = None,
        allow_redirects: bool = True,
        **kwargs
    ) -> Any:
        """
        发送 GET 请求
        
        Args:
            url: 目标 URL
            headers: 自定义请求头
            params: URL 参数
            allow_redirects: 是否跟随重定向
            
        Returns:
            响应对象
        """
        self._apply_delay()
        
        headers = self._get_headers(headers)
        proxies = self._get_proxy()
        
        retry_count = 0
        last_error = None
        
        while retry_count <= self.max_retries:
            try:
                self.stats["requests"] += 1
                
                if HAS_CURL_CFFI:
                    response = self.session.get(
                        url,
                        headers=headers,
                        params=params,
                        proxies=proxies,
                        timeout=self.timeout,
                        allow_redirects=allow_redirects,
                        impersonate="chrome120",  # TLS 指纹模拟
                        **kwargs
                    )
                else:
                    response = self.session.get(
                        url,
                        headers=headers,
                        params=params,
                        proxies=proxies,
                        timeout=self.timeout,
                        allow_redirects=allow_redirects,
                        **kwargs
                    )
                
                # 检查是否需要重试
                if self._should_retry(response.status_code):
                    retry_count += 1
                    self.stats["retries"] += 1
                    time.sleep(2 ** retry_count)  # 指数退避
                    continue
                
                self.stats["success"] += 1
                return response
                
            except Exception as e:
                last_error = e
                retry_count += 1
                self.stats["retries"] += 1
                
                if retry_count <= self.max_retries:
                    time.sleep(2 ** retry_count)
                    # 轮换代理重试
                    if self.rotate_proxy:
                        proxies = self._get_proxy()
        
        self.stats["failed"] += 1
        raise Exception(f"请求失败 after {self.max_retries} retries: {last_error}")
    
    def post(
        self,
        url: str,
        data: Optional[Dict] = None,
        json: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        **kwargs
    ) -> Any:
        """
        发送 POST 请求
        """
        self._apply_delay()
        
        headers = self._get_headers(headers)
        proxies = self._get_proxy()
        
        retry_count = 0
        last_error = None
        
        while retry_count <= self.max_retries:
            try:
                self.stats["requests"] += 1
                
                if HAS_CURL_CFFI:
                    response = self.session.post(
                        url,
                        data=data,
                        json=json,
                        headers=headers,
                        proxies=proxies,
                        timeout=self.timeout,
                        impersonate="chrome120",
                        **kwargs
                    )
                else:
                    response = self.session.post(
                        url,
                        data=data,
                        json=json,
                        headers=headers,
                        proxies=proxies,
                        timeout=self.timeout,
                        **kwargs
                    )
                
                if self._should_retry(response.status_code):
                    retry_count += 1
                    self.stats["retries"] += 1
                    time.sleep(2 ** retry_count)
                    continue
                
                self.stats["success"] += 1
                return response
                
            except Exception as e:
                last_error = e
                retry_count += 1
                self.stats["retries"] += 1
                
                if retry_count <= self.max_retries:
                    time.sleep(2 ** retry_count)
        
        self.stats["failed"] += 1
        raise Exception(f"POST 请求失败 after {self.max_retries} retries: {last_error}")
    
    def get_stats(self) -> Dict[str, int]:
        """获取统计信息"""
        return self.stats.copy()
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            "requests": 0,
            "success": 0,
            "failed": 0,
            "retries": 0,
        }


class AsyncStealthCrawler:
    """
    异步 stealth 爬虫类
    """
    
    def __init__(
        self,
        proxies: Optional[List[str]] = None,
        rotate_proxy: bool = False,
        rotate_ua: bool = True,
        delay_range: tuple = (1, 3),
        max_retries: int = 3,
        timeout: int = 30,
    ):
        self.proxies = proxies or []
        self.rotate_proxy = rotate_proxy and len(proxies) > 0
        self.rotate_ua = rotate_ua
        self.delay_range = delay_range
        self.max_retries = max_retries
        self.timeout = timeout
        
        self.ua = UserAgent()
        self.proxy_index = 0
        self.stats = {
            "requests": 0,
            "success": 0,
            "failed": 0,
            "retries": 0,
        }
    
    def _get_user_agent(self) -> str:
        if self.rotate_ua:
            try:
                return self.ua.random
            except Exception:
                return random.choice(USER_AGENTS)
        return USER_AGENTS[0]
    
    def _get_proxy(self) -> Optional[str]:
        if not self.proxies:
            return None
        
        if self.rotate_proxy:
            proxy_url = self.proxies[self.proxy_index]
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        else:
            proxy_url = self.proxies[0]
        
        return proxy_url
    
    def _get_headers(self, custom_headers: Optional[Dict] = None) -> Dict[str, str]:
        headers = DEFAULT_HEADERS.copy()
        headers["User-Agent"] = self._get_user_agent()
        if custom_headers:
            headers.update(custom_headers)
        return headers
    
    async def _apply_delay(self):
        delay = random.uniform(self.delay_range[0], self.delay_range[1])
        await asyncio.sleep(delay)
    
    async def get(
        self,
        url: str,
        headers: Optional[Dict] = None,
        params: Optional[Dict] = None,
        allow_redirects: bool = True,
        **kwargs
    ) -> Any:
        """异步 GET 请求"""
        await self._apply_delay()
        
        headers = self._get_headers(headers)
        proxy = self._get_proxy()
        
        retry_count = 0
        last_error = None
        
        while retry_count <= self.max_retries:
            try:
                self.stats["requests"] += 1
                
                async with aiohttp.ClientSession() as session:
                    if proxy:
                        connector = aiohttp.TCPConnector()
                        async with session.get(
                            url,
                            headers=headers,
                            params=params,
                            proxy=proxy,
                            timeout=aiohttp.ClientTimeout(total=self.timeout),
                            allow_redirects=allow_redirects,
                            **kwargs
                        ) as response:
                            if response.status in RETRY_STATUS_CODES:
                                retry_count += 1
                                self.stats["retries"] += 1
                                await asyncio.sleep(2 ** retry_count)
                                continue
                            
                            self.stats["success"] += 1
                            return await response.text()
            
            except Exception as e:
                last_error = e
                retry_count += 1
                self.stats["retries"] += 1
                
                if retry_count <= self.max_retries:
                    await asyncio.sleep(2 ** retry_count)
        
        self.stats["failed"] += 1
        raise Exception(f"异步请求失败 after {self.max_retries} retries: {last_error}")
    
    def get_stats(self) -> Dict[str, int]:
        return self.stats.copy()


# 便捷函数
def scrape(url: str, **kwargs) -> Any:
    """
    快速爬取函数
    
    Example:
        response = scrape('https://example.com')
        print(response.text)
    """
    crawler = StealthCrawler(**kwargs)
    return crawler.get(url)


if __name__ == "__main__":
    # 测试示例
    print("🕷️ Stealth Crawler 测试")
    print("=" * 50)
    
    crawler = StealthCrawler(delay_range=(0.5, 1))
    
    try:
        response = crawler.get("https://httpbin.org/html")
        print(f"✅ 请求成功！状态码：{response.status_code}")
        print(f"📊 响应长度：{len(response.text)} 字节")
        print(f"\n📈 统计信息：{crawler.get_stats()}")
    except Exception as e:
        print(f"❌ 请求失败：{e}")
