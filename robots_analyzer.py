"""
Robots.txt 检测和绕过模块

功能:
- 检测目标网站的 robots.txt
- 分析爬取限制
- 提供绕过策略建议
"""

import re
from urllib.parse import urlparse, urljoin
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

try:
    from curl_cffi import requests as curl_requests
    HAS_CURL_CFFI = True
except ImportError:
    HAS_CURL_CFFI = False
    import requests


@dataclass
class RobotsRule:
    """Robots.txt 规则"""
    user_agent: str
    disallowed: List[str]
    allowed: List[str]
    crawl_delay: Optional[float] = None


class RobotsAnalyzer:
    """
    Robots.txt 分析器
    
    用于检测和分析目标网站的爬取限制
    """
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.robots_cache: Dict[str, str] = {}
    
    def fetch_robots_txt(self, base_url: str) -> Optional[str]:
        """
        获取 robots.txt 内容
        
        Args:
            base_url: 网站 URL
            
        Returns:
            robots.txt 内容或 None
        """
        parsed = urlparse(base_url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        
        try:
            if HAS_CURL_CFFI:
                response = curl_requests.get(
                    robots_url,
                    timeout=self.timeout,
                    impersonate="chrome120"
                )
            else:
                response = requests.get(robots_url, timeout=self.timeout)
            
            if response.status_code == 200:
                self.robots_cache[base_url] = response.text
                return response.text
            elif response.status_code == 404:
                print(f"[INFO] {base_url} 没有 robots.txt")
                return None
            else:
                print(f"[WARN] 获取 robots.txt 失败: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"[ERROR] 获取 robots.txt 异常: {e}")
            return None
    
    def parse_robots_txt(self, content: str) -> List[RobotsRule]:
        """
        解析 robots.txt 内容
        
        Args:
            content: robots.txt 文本内容
            
        Returns:
            规则列表
        """
        rules = []
        current_user_agent = None
        current_disallowed = []
        current_allowed = []
        current_crawl_delay = None
        
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # 跳过空行和注释
            if not line or line.startswith('#'):
                continue
            
            # 解析 User-agent
            if line.lower().startswith('user-agent:'):
                # 保存之前的规则
                if current_user_agent:
                    rules.append(RobotsRule(
                        user_agent=current_user_agent,
                        disallowed=current_disallowed.copy(),
                        allowed=current_allowed.copy(),
                        crawl_delay=current_crawl_delay
                    ))
                
                current_user_agent = line.split(':', 1)[1].strip()
                current_disallowed = []
                current_allowed = []
                current_crawl_delay = None
            
            # 解析 Disallow
            elif line.lower().startswith('disallow:'):
                path = line.split(':', 1)[1].strip()
                if path:
                    current_disallowed.append(path)
            
            # 解析 Allow
            elif line.lower().startswith('allow:'):
                path = line.split(':', 1)[1].strip()
                if path:
                    current_allowed.append(path)
            
            # 解析 Crawl-delay
            elif line.lower().startswith('crawl-delay:'):
                try:
                    current_crawl_delay = float(line.split(':', 1)[1].strip())
                except ValueError:
                    pass
        
        # 保存最后的规则
        if current_user_agent:
            rules.append(RobotsRule(
                user_agent=current_user_agent,
                disallowed=current_disallowed,
                allowed=current_allowed,
                crawl_delay=current_crawl_delay
            ))
        
        return rules
    
    def is_allowed(self, url: str, rules: List[RobotsRule], user_agent: str = "*") -> Tuple[bool, str]:
        """
        检查 URL 是否被允许爬取
        
        Args:
            url: 目标 URL
            rules: 规则列表
            user_agent: User-Agent
            
        Returns:
            (是否允许, 原因)
        """
        parsed = urlparse(url)
        path = parsed.path
        if parsed.query:
            path += f"?{parsed.query}"
        
        # 查找匹配的规则
        matched_rules = []
        for rule in rules:
            if rule.user_agent == "*" or rule.user_agent.lower() in user_agent.lower():
                matched_rules.append(rule)
        
        if not matched_rules:
            return True, "无匹配规则"
        
        # 检查是否被禁止
        for rule in matched_rules:
            for disallowed in rule.disallowed:
                if self._path_matches(path, disallowed):
                    # 检查是否有更具体的 Allow 规则
                    for allowed in rule.allowed:
                        if self._path_matches(path, allowed) and len(allowed) > len(disallowed):
                            return True, f"被 Allow 规则覆盖: {allowed}"
                    return False, f"被 Disallow 规则禁止: {disallowed}"
        
        return True, "未被禁止"
    
    def _path_matches(self, path: str, pattern: str) -> bool:
        """
        检查路径是否匹配模式
        
        Args:
            path: URL 路径
            pattern: robots.txt 模式
            
        Returns:
            是否匹配
        """
        # 处理通配符
        pattern = pattern.replace('*', '.*')
        pattern = pattern.replace('?', '\\?')
        
        # 处理结束符
        if pattern.endswith('$'):
            pattern = pattern[:-1] + '$'
        else:
            pattern = pattern + '.*'
        
        try:
            return bool(re.match(pattern, path))
        except re.error:
            return path.startswith(pattern.replace('.*', ''))
    
    def analyze_site(self, url: str) -> Dict:
        """
        分析网站的爬取限制
        
        Args:
            url: 网站 URL
            
        Returns:
            分析结果
        """
        robots_content = self.fetch_robots_txt(url)
        
        if not robots_content:
            return {
                "url": url,
                "has_robots_txt": False,
                "rules": [],
                "summary": "网站没有 robots.txt，可以自由爬取"
            }
        
        rules = self.parse_robots_txt(robots_content)
        
        # 统计信息
        total_disallowed = sum(len(r.disallowed) for r in rules)
        total_allowed = sum(len(r.allowed) for r in rules)
        crawl_delays = [r.crawl_delay for r in rules if r.crawl_delay]
        
        summary = self._generate_summary(rules, total_disallowed, total_allowed, crawl_delays)
        
        return {
            "url": url,
            "has_robots_txt": True,
            "rules": rules,
            "total_disallowed": total_disallowed,
            "total_allowed": total_allowed,
            "crawl_delays": crawl_delays,
            "summary": summary,
            "raw_content": robots_content
        }
    
    def _generate_summary(self, rules, total_disallowed, total_allowed, crawl_delays) -> str:
        """生成分析摘要"""
        lines = []
        lines.append(f"发现 {len(rules)} 条规则")
        lines.append(f"禁止路径: {total_disallowed} 个")
        lines.append(f"允许路径: {total_allowed} 个")
        
        if crawl_delays:
            lines.append(f"爬取延迟: {min(crawl_delays)}-{max(crawl_delays)} 秒")
        
        return " | ".join(lines)
    
    def get_bypass_suggestions(self, analysis: Dict) -> List[str]:
        """
        获取绕过建议
        
        Args:
            analysis: 分析结果
            
        Returns:
            绕过策略建议列表
        """
        suggestions = []
        
        if not analysis["has_robots_txt"]:
            suggestions.append("✅ 无 robots.txt 限制，可直接爬取")
            return suggestions
        
        rules = analysis["rules"]
        
        # 检查是否有严格的禁止规则
        has_strict_rules = any(
            len(r.disallowed) > 0 and r.disallowed != ['/']
            for r in rules
        )
        
        if has_strict_rules:
            suggestions.append("⚠️ 网站有爬取限制，建议策略：")
            suggestions.append("  1. 使用代理轮换分散请求")
            suggestions.append("  2. 设置合理的请求延迟 (建议 3-5 秒)")
            suggestions.append("  3. 轮换 User-Agent 模拟不同浏览器")
            suggestions.append("  4. 避免爬取明确禁止的路径")
            suggestions.append("  5. 使用 TLS 指纹模拟避免检测")
        
        # 检查爬取延迟
        if analysis.get("crawl_delays"):
            min_delay = min(analysis["crawl_delays"])
            suggestions.append(f"⏱️ 建议请求延迟: {min_delay}+ 秒")
        
        return suggestions


class RobotsBypassCrawler:
    """
    支持 Robots.txt 绕过的爬虫
    
    提供三种模式:
    1. strict - 严格遵守 robots.txt
    2. warn - 警告但不阻止
    3. ignore - 完全忽略 robots.txt
    """
    
    MODE_STRICT = "strict"
    MODE_WARN = "warn"
    MODE_IGNORE = "ignore"
    
    def __init__(
        self,
        mode: str = "warn",
        respect_crawl_delay: bool = True,
    ):
        """
        初始化
        
        Args:
            mode: robots.txt 处理模式
            respect_crawl_delay: 是否遵守爬取延迟
        """
        self.mode = mode
        self.respect_crawl_delay = respect_crawl_delay
        self.analyzer = RobotsAnalyzer()
        self.site_analysis: Dict = {}
    
    def check_url(self, url: str, user_agent: str = "*") -> Tuple[bool, str]:
        """
        检查 URL 是否可以爬取
        
        Args:
            url: 目标 URL
            user_agent: User-Agent
            
        Returns:
            (是否可以爬取, 原因)
        """
        # 获取网站分析
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        if base_url not in self.site_analysis:
            self.site_analysis[base_url] = self.analyzer.analyze_site(base_url)
        
        analysis = self.site_analysis[base_url]
        
        # 忽略模式
        if self.mode == self.MODE_IGNORE:
            return True, "忽略 robots.txt 模式"
        
        # 无 robots.txt
        if not analysis["has_robots_txt"]:
            return True, "无 robots.txt"
        
        # 检查是否允许
        allowed, reason = self.analyzer.is_allowed(url, analysis["rules"], user_agent)
        
        # 警告模式
        if self.mode == self.MODE_WARN and not allowed:
            print(f"[WARN] URL 被 robots.txt 禁止: {reason}")
            print(f"[WARN] 但将继续爬取 (警告模式)")
            return True, f"警告: {reason}"
        
        return allowed, reason
    
    def get_recommended_delay(self, url: str) -> float:
        """
        获取推荐的请求延迟
        
        Args:
            url: 目标 URL
            
        Returns:
            推荐延迟秒数
        """
        if not self.respect_crawl_delay:
            return 1.0  # 默认延迟
        
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        if base_url not in self.site_analysis:
            self.site_analysis[base_url] = self.analyzer.analyze_site(base_url)
        
        analysis = self.site_analysis[base_url]
        
        if analysis.get("crawl_delays"):
            return max(analysis["crawl_delays"])
        
        return 2.0  # 默认安全延迟


# 便捷函数
def analyze_robots(url: str) -> Dict:
    """
    快速分析网站的 robots.txt
    
    Example:
        result = analyze_robots('https://example.com')
        print(result['summary'])
    """
    analyzer = RobotsAnalyzer()
    return analyzer.analyze_site(url)


if __name__ == "__main__":
    # 测试示例
    print("🕷️ Robots.txt 分析器测试")
    print("=" * 50)
    
    # 测试网站
    test_urls = [
        "https://www.baidu.com",
        "https://www.taobao.com",
        "https://www.zhihu.com",
    ]
    
    analyzer = RobotsAnalyzer()
    
    for url in test_urls:
        print(f"\n分析: {url}")
        print("-" * 40)
        
        result = analyzer.analyze_site(url)
        
        print(f"状态: {'有 robots.txt' if result['has_robots_txt'] else '无 robots.txt'}")
        
        if result['has_robots_txt']:
            print(f"摘要: {result['summary']}")
            
            # 获取绕过建议
            suggestions = analyzer.get_bypass_suggestions(result)
            for suggestion in suggestions:
                print(suggestion)