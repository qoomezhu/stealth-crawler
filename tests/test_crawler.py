"""
单元测试
"""

import unittest
from unittest.mock import Mock, patch
import sys
sys.path.append('..')

from crawler import StealthCrawler, AsyncStealthCrawler
from config import USER_AGENTS, DEFAULT_HEADERS


class TestStealthCrawler(unittest.TestCase):
    """StealthCrawler 测试"""
    
    def setUp(self):
        """测试前准备"""
        self.crawler = StealthCrawler(delay_range=(0.1, 0.2))
    
    def test_init(self):
        """测试初始化"""
        self.assertIsInstance(self.crawler, StealthCrawler)
        self.assertTrue(self.crawler.rotate_ua)
        self.assertFalse(self.crawler.rotate_proxy)
        self.assertEqual(self.crawler.max_retries, 3)
    
    def test_get_user_agent(self):
        """测试 User-Agent 获取"""
        ua = self.crawler._get_user_agent()
        self.assertIsNotNone(ua)
        self.assertIsInstance(ua, str)
        self.assertGreater(len(ua), 10)
    
    def test_get_headers(self):
        """测试请求头构建"""
        headers = self.crawler._get_headers()
        
        self.assertIn('User-Agent', headers)
        self.assertIn('Accept', headers)
        self.assertIn('Accept-Language', headers)
    
    def test_get_headers_custom(self):
        """测试自定义请求头"""
        custom = {'X-Custom': 'value'}
        headers = self.crawler._get_headers(custom)
        
        self.assertIn('X-Custom', headers)
        self.assertEqual(headers['X-Custom'], 'value')
    
    def test_get_proxy_none(self):
        """测试无代理情况"""
        proxy = self.crawler._get_proxy()
        self.assertIsNone(proxy)
    
    def test_get_proxy_with_proxies(self):
        """测试有代理情况"""
        proxies = ['http://proxy1.com:8080', 'http://proxy2.com:8080']
        crawler = StealthCrawler(proxies=proxies, rotate_proxy=True)
        
        proxy = crawler._get_proxy()
        self.assertIsNotNone(proxy)
        self.assertIn('http', proxy)
        self.assertIn('https', proxy)
    
    def test_proxy_rotation(self):
        """测试代理轮换"""
        proxies = ['http://proxy1.com:8080', 'http://proxy2.com:8080', 'http://proxy3.com:8080']
        crawler = StealthCrawler(proxies=proxies, rotate_proxy=True)
        
        # 获取多个代理，验证轮换
        proxy1 = crawler._get_proxy()
        proxy2 = crawler._get_proxy()
        proxy3 = crawler._get_proxy()
        proxy4 = crawler._get_proxy()  # 应该循环回第一个
        
        self.assertEqual(proxy1['http'], proxies[0])
        self.assertEqual(proxy2['http'], proxies[1])
        self.assertEqual(proxy3['http'], proxies[2])
        self.assertEqual(proxy4['http'], proxies[0])  # 循环
    
    def test_should_retry(self):
        """测试重试判断"""
        self.assertTrue(self.crawler._should_retry(429))
        self.assertTrue(self.crawler._should_retry(500))
        self.assertTrue(self.crawler._should_retry(503))
        self.assertFalse(self.crawler._should_retry(200))
        self.assertFalse(self.crawler._should_retry(404))
    
    def test_stats(self):
        """测试统计功能"""
        stats = self.crawler.get_stats()
        
        self.assertIn('requests', stats)
        self.assertIn('success', stats)
        self.assertIn('failed', stats)
        self.assertIn('retries', stats)
        
        # 重置
        self.crawler.reset_stats()
        stats = self.crawler.get_stats()
        
        self.assertEqual(stats['requests'], 0)
        self.assertEqual(stats['success'], 0)


class TestAsyncStealthCrawler(unittest.TestCase):
    """AsyncStealthCrawler 测试"""
    
    def setUp(self):
        """测试前准备"""
        self.crawler = AsyncStealthCrawler(delay_range=(0.1, 0.2))
    
    def test_init(self):
        """测试初始化"""
        self.assertIsInstance(self.crawler, AsyncStealthCrawler)
        self.assertTrue(self.crawler.rotate_ua)
    
    def test_get_user_agent(self):
        """测试 User-Agent 获取"""
        ua = self.crawler._get_user_agent()
        self.assertIsNotNone(ua)
        self.assertIsInstance(ua, str)
    
    def test_get_headers(self):
        """测试请求头构建"""
        headers = self.crawler._get_headers()
        self.assertIn('User-Agent', headers)


class TestConfig(unittest.TestCase):
    """配置测试"""
    
    def test_user_agents_not_empty(self):
        """测试 User-Agent 列表不为空"""
        self.assertGreater(len(USER_AGENTS), 0)
    
    def test_user_agents_valid(self):
        """测试 User-Agent 格式有效"""
        for ua in USER_AGENTS:
            self.assertIn('Mozilla', ua)
    
    def test_default_headers(self):
        """测试默认请求头"""
        self.assertIn('Accept', DEFAULT_HEADERS)
        self.assertIn('Accept-Language', DEFAULT_HEADERS)


if __name__ == '__main__':
    unittest.main()
