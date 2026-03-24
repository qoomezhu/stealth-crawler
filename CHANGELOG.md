# Stealth Crawler - 更新日志

## v1.1.0 - Robots.txt 分析功能

### 新增功能

#### 🤖 Robots.txt 分析器 (`robots_analyzer.py`)

- **自动检测**: 自动获取和解析目标网站的 robots.txt
- **规则分析**: 分析 Disallow/Allow/Crawl-delay 规则
- **路径检查**: 检查特定 URL 是否被允许爬取
- **绕过建议**: 提供针对性的绕过策略建议

#### 🎛️ 三种处理模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| `strict` | 严格遵守 robots.txt | 合规爬取、学术研究 |
| `warn` | 警告但不阻止 | 测试、调试 |
| `ignore` | 完全忽略 robots.txt | 压力测试、反爬测试 |

#### 🧠 智能爬虫 (`smart_crawler.py`)

- 集成 Robots.txt 分析
- 自动调整请求延迟
- 提供详细的检查报告

---

## 使用方法

### 1. 分析网站 robots.txt

```python
from robots_analyzer import analyze_robots

# 快速分析
result = analyze_robots('https://example.com')
print(result['summary'])
```

### 2. 检查特定路径

```python
from robots_analyzer import RobotsAnalyzer

analyzer = RobotsAnalyzer()
result = analyzer.analyze_site('https://example.com')

# 检查路径
allowed, reason = analyzer.is_allowed(
    'https://example.com/admin',
    result['rules']
)
print(f"允许: {allowed}, 原因: {reason}")
```

### 3. 使用智能爬虫

```python
from smart_crawler import SmartStealthCrawler

# 严格遵守模式
crawler = SmartStealthCrawler(robots_mode='strict')
response = crawler.get('https://example.com')

# 警告模式 (继续爬取但会警告)
crawler = SmartStealthCrawler(robots_mode='warn')
response = crawler.get('https://example.com/search')

# 忽略模式 (完全忽略 robots.txt)
crawler = SmartStealthCrawler(robots_mode='ignore')
response = crawler.get('https://example.com/admin')

# 查看报告
crawler.print_robots_report()
```

### 4. 快速爬取

```python
from smart_crawler import smart_scrape

# 忽略 robots.txt
response = smart_scrape('https://example.com', robots_mode='ignore')

# 严格遵守
response = smart_scrape('https://example.com', robots_mode='strict')
```

---

## 反爬压力测试

### 测试场景

```python
from smart_crawler import SmartStealthCrawler

# 创建忽略模式的爬虫用于压力测试
crawler = SmartStealthCrawler(
    robots_mode='ignore',  # 忽略 robots.txt
    rotate_proxy=True,     # 轮换代理
    rotate_ua=True,        # 轮换 User-Agent
    delay_range=(0.5, 1),  # 短延迟
    max_retries=5,         # 多次重试
)

# 压力测试
urls = ['https://target-site.com/page/' + str(i) for i in range(100)]

for url in urls:
    try:
        response = crawler.get(url)
        print(f"✅ {url}: {response.status_code}")
    except Exception as e:
        print(f"❌ {url}: {e}")

# 查看统计
crawler.print_robots_report()
print(f"\n请求统计: {crawler.get_stats()}")
```

---

## 文件结构更新

```
stealth-crawler/
├── crawler.py              # 基础爬虫
├── smart_crawler.py        # 智能爬虫 (新增)
├── robots_analyzer.py      # Robots.txt 分析器 (新增)
├── config.py
├── examples/
│   ├── robots_analysis.py  # Robots.txt 示例 (新增)
│   └── ...
└── ...
```