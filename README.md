# 🕷️ Stealth Crawler

一个可维护的 Python 爬虫实例，支持同步 / 异步请求、代理池、robots 感知、HTML 解析与统一结果封装。

## 特性

- 同步 / 异步双栈
- 统一结果结构 `FetchResult`
- 代理池轮换与失败熔断
- robots.txt 检查（strict / warn / ignore）
- HTML 标题、链接、Meta 提取
- 标准日志系统
- 可直接作为库使用，也可继续扩展为 CLI

## 安装

```bash
pip install -e .
```

如果你想使用更强的 TLS 指纹模拟能力：

```bash
pip install -e ".[stealth]"
```

## 快速开始

### 同步

```python
from stealth_crawler import Crawler, HTMLParser

with Crawler() as crawler:
    result = crawler.get("https://httpbin.org/html")
    print(result.status_code)
    print(HTMLParser.title(result.text))
```

### 异步

```python
import asyncio
from stealth_crawler import AsyncCrawler

async def main():
    async with AsyncCrawler() as crawler:
        result = await crawler.get("https://httpbin.org/html")
        print(result.status_code)

asyncio.run(main())
```

## 目录结构

```text
stealth-crawler/
├── stealth_crawler/
│   ├── __init__.py
│   ├── config.py
│   ├── exceptions.py
│   ├── logger.py
│   ├── models.py
│   ├── proxy.py
│   ├── robots.py
│   ├── parser.py
│   ├── crawler.py
│   └── async_crawler.py
├── examples/
│   └── basic.py
├── tests/
│   └── test_crawler.py
└── pyproject.toml
```

## 配置示例

```python
from stealth_crawler import Crawler, CrawlerConfig

config = CrawlerConfig(
    timeout=20,
    max_retries=3,
    delay_range=(1, 2),
    robots_mode="warn",
)

crawler = Crawler(config=config)
```

## 说明

- `strict`：严格遵守 robots.txt
- `warn`：发现限制时告警，但继续执行
- `ignore`：跳过 robots 检查

## 开发

```bash
pytest -q
```

## 许可证

MIT
