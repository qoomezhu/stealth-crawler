"""
集成 Robots.txt 分析的爬虫
"""

import sys
sys.path.append('..')

import time
from typing import Optional, List, Dict

from crawler import StealthCrawler
from robots_analyzer import RobotsAnalyzer, RobotsBypassCrawler


class SmartStealthCrawler(StealthCrawler):
    """
    智能 Stealth 爬虫 - 集成 Robots.txt 分析
    
    功能:
    - 自动检测目标网站的 robots.txt
    - 支持三种模式: strict/warn/ignore
    - 自动调整请求延迟
    - 提供绕过建议
    """
    
    MODE_STRICT = "strict"
    MODE_WARN = "warn"
    MODE_IGNORE = "ignore"
    
    def __init__(
        self,
        robots_mode: str = "warn",
        respect_crawl_delay: bool = True,
        proxies: Optional[List[str]] = None,
        rotate_proxy: bool = False,
        rotate_ua: bool = True,
        delay_range: tuple = (1, 3),
        max_retries: int = 3,
        timeout: int = 30,
    ):
        """
        初始化智能爬虫
        
        Args:
            robots_mode: robots.txt 处理模式
                - strict: 严格遵守
                - warn: 警告但不阻止
                - ignore: 完全忽略
            respect_crawl_delay: 是否遵守爬取延迟
            proxies: 代理列表
            rotate_proxy: 是否轮换代理
            rotate_ua: 是否轮换 User-Agent
            delay_range: 默认延迟范围
            max_retries: 最大重试次数
            timeout: 超时时间
        """
        super().__init__(
            proxies=proxies,
            rotate_proxy=rotate_proxy,
            rotate_ua=rotate_ua,
            delay_range=delay_range,
            max_retries=max_retries,
            timeout=timeout,
        )
        
        self.robots_mode = robots_mode
        self.respect_crawl_delay = respect_crawl_delay
        self.robots_analyzer = RobotsAnalyzer()
        self.site_analysis: Dict = {}
        self.robots_stats = {
            "checked": 0,
            "blocked": 0,
            "warned": 0,
            "bypassed": 0,
        }
    
    def _get_base_url(self, url: str) -> str:
        """获取网站基础 URL"""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"
    
    def _check_robots(self, url: str) -> tuple:
        """
        检查 robots.txt
        
        Returns:
            (allowed, reason, recommended_delay)
        """
        base_url = self._get_base_url(url)
        
        # 缓存分析结果
        if base_url not in self.site_analysis:
            self.site_analysis[base_url] = self.robots_analyzer.analyze_site(base_url)
        
        analysis = self.site_analysis[base_url]
        self.robots_stats["checked"] += 1
        
        # 忽略模式
        if self.robots_mode == self.MODE_IGNORE:
            self.robots_stats["bypassed"] += 1
            return True, "忽略 robots.txt", self.delay_range[0]
        
        # 无 robots.txt
        if not analysis["has_robots_txt"]:
            return True, "无 robots.txt", self.delay_range[0]
        
        # 检查是否允许
        allowed, reason = self.robots_analyzer.is_allowed(
            url, analysis["rules"], self.current_ua or "*"
        )
        
        # 获取推荐延迟
        recommended_delay = self.delay_range[0]
        if self.respect_crawl_delay and analysis.get("crawl_delays"):
            recommended_delay = max(analysis["crawl_delays"])
        
        # 处理结果
        if not allowed:
            if self.robots_mode == self.MODE_WARN:
                self.robots_stats["warned"] += 1
                print(f"\n[WARN] robots.txt 禁止: {reason}")
                print(f"[WARN] 但将继续爬取 (warn 模式)")
                return True, f"警告: {reason}", recommended_delay
            else:
                self.robots_stats["blocked"] += 1
                return False, reason, recommended_delay
        
        return True, reason, recommended_delay
    
    def get(self, url: str, **kwargs):
        """
        发送 GET 请求 (带 robots.txt 检查)
        
        Args:
            url: 目标 URL
            
        Returns:
            响应对象
        """
        # 检查 robots.txt
        allowed, reason, recommended_delay = self._check_robots(url)
        
        if not allowed:
            raise Exception(f"robots.txt 禁止爬取: {reason}")
        
        # 调整延迟
        original_delay = self.delay_range
        if self.respect_crawl_delay:
            self.delay_range = (recommended_delay, recommended_delay + 2)
        
        try:
            response = super().get(url, **kwargs)
            return response
        finally:
            self.delay_range = original_delay
    
    def get_robots_report(self) -> Dict:
        """获取 robots.txt 检查报告"""
        return {
            "mode": self.robots_mode,
            "stats": self.robots_stats.copy(),
            "sites_analyzed": list(self.site_analysis.keys()),
        }
    
    def print_robots_report(self):
        """打印 robots.txt 检查报告"""
        report = self.get_robots_report()
        
        print("\n" + "="*50)
        print("📊 Robots.txt 检查报告")
        print("="*50)
        print(f"模式: {report['mode']}")
        print(f"检查次数: {report['stats']['checked']}")
        print(f"阻止次数: {report['stats']['blocked']}")
        print(f"警告次数: {report['stats']['warned']}")
        print(f"绕过次数: {report['stats']['bypassed']}")
        print(f"分析网站数: {len(report['sites_analyzed'])}")
        
        if report['sites_analyzed']:
            print(f"\n已分析网站:")
            for site in report['sites_analyzed']:
                print(f"  - {site}")


# 便捷函数
def smart_scrape(url: str, robots_mode: str = "warn", **kwargs):
    """
    智能爬取函数
    
    Example:
        # 忽略 robots.txt
        response = smart_scrape('https://example.com', robots_mode='ignore')
        
        # 严格遵守
        response = smart_scrape('https://example.com', robots_mode='strict')
    """
    crawler = SmartStealthCrawler(robots_mode=robots_mode, **kwargs)
    return crawler.get(url)


if __name__ == "__main__":
    print("🕷️ 智能 Stealth 爬虫测试")
    print("="*50)
    
    # 测试三种模式
    modes = ["strict", "warn", "ignore"]
    
    for mode in modes:
        print(f"\n测试模式: {mode}")
        print("-" * 40)
        
        crawler = SmartStealthCrawler(
            robots_mode=mode,
            delay_range=(0.5, 1),
        )
        
        try:
            response = crawler.get("https://httpbin.org/html")
            print(f"✅ 请求成功！状态码：{response.status_code}")
        except Exception as e:
            print(f"❌ 请求失败：{e}")
        
        crawler.print_robots_report()