# 🕷️ Stealth Crawler - 高级反爬虫爬虫实例

一个功能完整的高级 Web 爬虫实例，专为反爬虫测试和绕过检测而设计。

## ✨ 核心功能

- **🎭 User-Agent 轮换** - 自动轮换真实浏览器 User-Agent
- **🔄 代理轮换** - 支持 HTTP/HTTPS/SOCKS5 代理池
- **🔐 TLS 指纹模拟** - 使用 curl_cffi 模拟真实浏览器 TLS 指纹
- **⏱️ 智能请求节流** - 随机延迟模拟人类行为
- **🍪 Cookie 会话管理** - 自动维护会话状态
- **🔄 自动重试机制** - 失败请求自动重试
- **📊 响应解析** - 支持 BeautifulSoup/Lxml/Markdown
- **🌐 异步支持** - 支持 asyncio 高并发爬取

## 📦 安装

```bash
# 克隆仓库
git clone https://github.com/qoomezhu/stealth-crawler.git
cd stealth-crawler

# 安装依赖
pip install -r requirements.txt
```

## 🚀 快速开始

### 基础用法

```python
from crawler import StealthCrawler

# 创建爬虫实例
crawler = StealthCrawler()

# 发送请求
response = crawler.get('https://httpbin.org/html')
print(response.text)
```

### 使用代理池

```python
from crawler import StealthCrawler

proxies = [
    "http://user:pass@proxy1.example.com:8080",
    "http://user:pass@proxy2.example.com:8080",
    "http://user:pass@proxy3.example.com:8080",
]

crawler = StealthCrawler(proxies=proxies, rotate_proxy=True)
response = crawler.get('https://httpbin.org/ip')
print(response.text)
```

### 异步爬取

```python
import asyncio
from crawler import AsyncStealthCrawler

async def main():
    crawler = AsyncStealthCrawler()
    urls = [
        'https://httpbin.org/html',
        'https://httpbin.org/headers',
        'https://httpbin.org/ip',
    ]
    
    tasks = [crawler.get(url) for url in urls]
    responses = await asyncio.gather(*tasks)
    
    for resp in responses:
        print(f"Status: {resp.status_code}")

asyncio.run(main())
```

## 📁 项目结构

```
stealth-crawler/
├── crawler.py          # 主爬虫类
├── config.py           # 配置文件
├── requirements.txt    # 依赖列表
├── examples/           # 使用示例
│   ├── basic_usage.py
│   ├── proxy_rotation.py
│   └── async_crawler.py
└── README.md
```

## 🔧 配置选项

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `proxies` | list | None | 代理服务器列表 |
| `rotate_proxy` | bool | False | 是否轮换代理 |
| `rotate_ua` | bool | True | 是否轮换 User-Agent |
| `delay_range` | tuple | (1, 3) | 请求延迟范围 (秒) |
| `max_retries` | int | 3 | 最大重试次数 |
| `timeout` | int | 30 | 请求超时时间 |

## ⚠️ 使用须知

- 本工具仅供学习和研究使用
- 请遵守目标网站的 robots.txt 协议
- 请遵守相关法律法规和网站服务条款
- 请勿用于非法用途

## 📄 许可证

MIT License
