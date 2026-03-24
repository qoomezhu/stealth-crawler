# 🕷️ Stealth Crawler

一个可维护的 Python 爬虫实例，支持同步 / 异步请求、代理池、robots 感知、HTML 解析与统一结果封装。

## 特性

- 同步 / 异步双栈
- 统一结果结构 `FetchResult`
- 代理池轮换与失败熔断
- robots.txt 检查（strict / warn / ignore）
- HTML 标题、链接、Meta 提取
- 标准日志系统
- CLI 与 HTTP API
- 可容器化、可云端部署

## 安装

```bash
pip install -e .
```

如果你要启用 HTTP API / Docker 运行所需依赖：

```bash
pip install -e ".[api,stealth]"
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

安装后可直接使用：

```bash
stealth-crawler fetch https://httpbin.org/html
stealth-crawler analyze https://example.com --robots-mode warn
stealth-crawler parse https://httpbin.org/html --json
```

## HTTP API

启动服务：

```bash
uvicorn stealth_crawler.http_api:app --host 0.0.0.0 --port 8080
```

接口：

- `GET /health`
- `POST /fetch`
- `POST /parse`
- `POST /analyze`

## Docker

构建镜像：

```bash
docker build -t stealth-crawler:latest .
```

运行：

```bash
docker run --rm -p 8080:8080 stealth-crawler:latest
```

## 云端部署 + MCP 调用的可行性

可以，推荐架构是：

1. **Docker 容器**中运行本仓库的 HTTP API
2. **部署到云端**（Cloud Run / ECS / Fly.io / Kubernetes 都可）
3. 再单独做一个 **MCP Bridge**，把 MCP 工具调用转成 HTTP 请求，代理到这个服务

这样做的好处：
- MCP 端只负责工具编排
- 爬虫逻辑只在云端容器内维护
- 后续可以横向扩容、加鉴权、加限流

如果你要，我可以下一步直接补一个 `mcp_bridge` 方案文件。

## 目录结构

```text
stealth-crawler/
├── stealth_crawler/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── http_api.py
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
│   ├── basic.py
│   └── robots_analysis.py
├── tests/
│   └── test_crawler.py
├── Dockerfile
├── .dockerignore
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
