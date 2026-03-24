"""
Robots.txt 分析和绕过示例
"""

import sys
sys.path.append('..')

from robots_analyzer import RobotsAnalyzer, RobotsBypassCrawler, analyze_robots


def example_analyze_robots():
    """示例：分析 robots.txt"""
    print("\n" + "="*50)
    print("示例：分析网站 robots.txt")
    print("="*50)
    
    analyzer = RobotsAnalyzer()
    
    # 分析多个网站
    websites = [
        "https://www.baidu.com",
        "https://www.taobao.com",
        "https://www.zhihu.com",
        "https://www.github.com",
    ]
    
    for site in websites:
        print(f"\n📍 分析: {site}")
        print("-" * 40)
        
        result = analyzer.analyze_site(site)
        
        if result['has_robots_txt']:
            print(f"✅ 发现 robots.txt")
            print(f"   禁止路径: {result['total_disallowed']} 个")
            print(f"   允许路径: {result['total_allowed']} 个")
            
            if result.get('crawl_delays'):
                print(f"   爬取延迟: {result['crawl_delays']}")
        else:
            print(f"❌ 无 robots.txt")


def example_bypass_modes():
    """示例：三种绕过模式"""
    print("\n" + "="*50)
    print("示例：Robots.txt 绕过模式")
    print("="*50)
    
    # 三种模式
    modes = {
        "strict": "严格遵守 robots.txt",
        "warn": "警告但不阻止",
        "ignore": "完全忽略 robots.txt",
    }
    
    for mode, desc in modes.items():
        print(f"\n模式 [{mode}]: {desc}")
        print("-" * 40)
        
        crawler = RobotsBypassCrawler(mode=mode)
        
        # 测试 URL
        test_url = "https://www.baidu.com/search"
        
        allowed, reason = crawler.check_url(test_url)
        print(f"URL: {test_url}")
        print(f"允许爬取: {'✅' if allowed else '❌'}")
        print(f"原因: {reason}")


def example_quick_analyze():
    """示例：快速分析"""
    print("\n" + "="*50)
    print("示例：快速分析函数")
    print("="*50)
    
    result = analyze_robots("https://www.github.com")
    
    print(f"\n网站: {result['url']}")
    print(f"摘要: {result['summary']}")
    
    if result['has_robots_txt']:
        print(f"\n原始内容:")
        print(result['raw_content'][:500] + "...")


def example_get_recommendations():
    """示例：获取绕过建议"""
    print("\n" + "="*50)
    print("示例：获取绕过建议")
    print("="*50)
    
    analyzer = RobotsAnalyzer()
    
    sites = [
        "https://www.zhihu.com",
        "https://www.taobao.com",
    ]
    
    for site in sites:
        print(f"\n📍 {site}")
        print("-" * 40)
        
        result = analyzer.analyze_site(site)
        suggestions = analyzer.get_bypass_suggestions(result)
        
        for suggestion in suggestions:
            print(suggestion)


def example_check_specific_path():
    """示例：检查特定路径"""
    print("\n" + "="*50)
    print("示例：检查特定路径是否允许爬取")
    print("="*50)
    
    analyzer = RobotsAnalyzer()
    
    # 先分析网站
    result = analyzer.analyze_site("https://www.baidu.com")
    
    # 检查不同路径
    test_paths = [
        "/",
        "/search",
        "/news",
        "/img/logo.png",
    ]
    
    print(f"\n检查 baidu.com 的路径:")
    for path in test_paths:
        url = f"https://www.baidu.com{path}"
        allowed, reason = analyzer.is_allowed(url, result['rules'])
        status = "✅ 允许" if allowed else "❌ 禁止"
        print(f"  {path}: {status} - {reason}")


if __name__ == "__main__":
    example_analyze_robots()
    example_bypass_modes()
    example_quick_analyze()
    example_get_recommendations()
    example_check_specific_path()
    
    print("\n" + "="*50)
    print("✅ 所有 Robots.txt 示例完成！")
    print("="*50)