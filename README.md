# 🕷️ Stealth Crawler

一个可维护的 Python 爬虫实例，支持同步 / 异步请求、代理池、robots 感知、HTML 解析、**规范化输出**、CLI、HTTP API 和内置 MCP 接口。

## 特性

- 同步 / 异步双栈
- 统一结果结构 `FetchResult`
- 代理池轮换与失败熔断
- robots.txt 检查（strict / warn / ignore）
- HTML 标题、链接、Meta 提取
- 规范化的 fetch / parse / analyze 输出
- 标准日志系统
- CLI 与 HTTP API
- API Key 鉴权 + 速率限制
- 可选 Redis 分布式限流
- HTTP API 与 MCP 同进程一体化部署
- 可容器化、可云端部署、可通过 MCP 调用

## 安装

```bash
pip install -e ".[api,stealth,mcp]"
```

如果你只想使用基础库：

```bash
pip install -e .
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

## CLI

```bash
stealth-crawler fetch https://httpbin.org/html
stealth-crawler fetch https://httpbin.org/html --json
stealth-crawler analyze https://example.com --robots-mode warn
stealth-crawler parse https://httpbin.org/html --json
stealth-crawler serve --host 0.0.0.0 --port 8080
```

`--json` 输出采用规范化结构，适合后续入库、比对或压测统计。

## HTTP API

### 认证

如果设置了 `CRAWLER_API_KEY`，请求需要携带：

```bash
X-API-Key: <your-key>
# 或
Authorization: Bearer <your-key>
```

### 速率限制

默认使用内存版限流；若要启用 Redis 分布式限流，请设置：

- `CRAWLER_RATE_LIMIT_BACKEND=redis`
- `CRAWLER_RATE_LIMIT_REDIS_URL=redis://localhost:6379/0`

### 接口

- `GET /health`
- `POST /fetch`
- `POST /parse`
- `POST /analyze`
- `GET /mcp/healthz`
- `POST /mcp`

`/fetch` 和 `/parse` 返回规范化 JSON，包含 request / response / content / parsed 等字段。

## Docker / Compose

```bash
docker build -t stealth-crawler:latest .
docker compose up --build
```

Compose 会启动：
- `redis`：分布式限流依赖
- `app`：统一的 HTTP API + MCP 服务

## 云端部署 + MCP 调用

推荐方案：

1. **单个应用容器**部署到云端
2. HTTP API 与 MCP 接口共用同一进程与同一鉴权层
3. MCP 客户端（例如 RikkaHub）通过 `Authorization: Bearer` 访问 `/mcp`

### 环境变量

- `CRAWLER_API_KEY`
- `CRAWLER_RATE_LIMIT_BACKEND`
- `CRAWLER_RATE_LIMIT_REQUESTS`
- `CRAWLER_RATE_LIMIT_WINDOW`
- `CRAWLER_RATE_LIMIT_REDIS_URL`
- `MCP_BEARER_TOKEN`
- `MCP_PUBLIC_PATHS=/mcp/healthz`

### 示例

```bash
# 本地启动统一服务
uvicorn stealth_crawler.http_api:app --host 0.0.0.0 --port 8080

# 如需兼容旧启动方式，也可以
python -m mcp_bridge.server
```

## 目录结构

```text
stealth-crawler/
├── stealth_crawler/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── http_api.py
│   ├── security.py
│   ├── config.py
│   ├── exceptions.py
│   ├── logger.py
│   ├── models.py
│   ├── proxy.py
│   ├── robots.py
│   ├── parser.py
│   ├── crawler.py
│   └── async_crawler.py
├── mcp_bridge/
│   └── server.py
├── deploy/
│   ├── cloudrun-api.yaml
│   └── cloudrun-mcp-bridge.yaml
├── examples/
│   ├── basic.py
│   └── robots_analysis.py
├── tests/
│   └── test_crawler.py
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── pyproject.toml
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
