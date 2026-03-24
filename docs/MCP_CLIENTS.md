# MCP Client 配置示例

本文档给出如何把 `stealth-crawler` 接入常见 MCP 客户端的配置示例。

> 建议结构：
> - **本地开发**：直接以 `python -m mcp_bridge.server` 启动 stdio MCP Bridge
> - **远端调用**：把 `MCP_TRANSPORT=http` 的 Bridge 部署到云端，再让客户端连接 URL，并携带 `Authorization: Bearer`

---

## 1) Claude Desktop / 其他支持 stdio 的 MCP 客户端

如果你想直接在本机跑 Bridge：

```json
{
  "mcpServers": {
    "stealth-crawler": {
      "command": "python",
      "args": ["-m", "mcp_bridge.server"],
      "env": {
        "CRAWLER_API_BASE_URL": "http://127.0.0.1:8080",
        "CRAWLER_API_KEY": "dev-secret-change-me"
      }
    }
  }
}
```

### 说明

- `command`：启动 Python
- `args`：运行 `mcp_bridge.server`
- `CRAWLER_API_BASE_URL`：你的 HTTP API 地址
- `CRAWLER_API_KEY`：与 API 服务一致的共享密钥

---

## 2) RikkaHub 远程 MCP 连接示例

如果你的 RikkaHub 支持 MCP Server 的 URL + 自定义请求头，推荐这样配置：

```json
{
  "mcpServers": {
    "stealth-crawler": {
      "url": "https://your-bridge-domain.example.com/mcp",
      "headers": {
        "Authorization": "Bearer your-mcp-token"
      }
    }
  }
}
```

### 说明

- `url`：指向你远程部署的 MCP Bridge `/mcp`
- `Authorization`：必须使用 `Bearer <token>` 格式
- `your-mcp-token`：应与服务器端 `MCP_BEARER_TOKEN` 保持一致

> 如果 RikkaHub 的配置界面不是 JSON，而是表单/环境变量形式，只要最终请求头中能注入 `Authorization: Bearer ...` 即可。

---

## 3) Cursor 配置示例

Cursor 通常使用类似的 `mcpServers` 配置：

```json
{
  "mcpServers": {
    "stealth-crawler": {
      "command": "python",
      "args": ["-m", "mcp_bridge.server"],
      "env": {
        "CRAWLER_API_BASE_URL": "https://your-api-domain.example.com",
        "CRAWLER_API_KEY": "replace-with-real-key",
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

### 云端 Bridge 连接方式

如果你部署的是 HTTP 模式的 Bridge：

```json
{
  "mcpServers": {
    "stealth-crawler": {
      "url": "https://your-bridge-domain.example.com/mcp",
      "headers": {
        "Authorization": "Bearer replace-with-real-key"
      }
    }
  }
}
```

> 是否支持 `url` 方式，取决于你的 MCP 客户端是否支持 HTTP transport。

---

## 4) FastMCP Python Client 示例

如果你要在 Python 里直接调用 MCP：

```python
import asyncio
from fastmcp import Client

async def main():
    client = Client("http://127.0.0.1:8001/mcp")

    async with client:
        await client.ping()
        tools = await client.list_tools()
        print(tools)

        result = await client.call_tool("health", {})
        print(result)

asyncio.run(main())
```

---

## 5) Pydantic AI / FastMCPToolset 示例

如果你要在 Agent 里挂载这个 MCP Bridge：

```python
from pydantic_ai import Agent
from pydantic_ai.toolsets.fastmcp import FastMCPToolset

toolset = FastMCPToolset("http://127.0.0.1:8001/mcp")
agent = Agent("openai:gpt-5.2", toolsets=[toolset])
```

---

## 6) 推荐的本地开发配置

### `.env`

```bash
CRAWLER_API_BASE_URL=http://127.0.0.1:8080
CRAWLER_API_KEY=dev-secret-change-me
CRAWLER_RATE_LIMIT_REQUESTS=60
CRAWLER_RATE_LIMIT_WINDOW=60
MCP_TRANSPORT=stdio
MCP_BEARER_TOKEN=dev-mcp-token-change-me
```

### 启动顺序

```bash
# 1. 启动 HTTP API
uvicorn stealth_crawler.http_api:app --host 0.0.0.0 --port 8080

# 2. 启动 MCP Bridge
python -m mcp_bridge.server
```

---

## 7) 部署到云端后的推荐配置

### API

- `CRAWLER_API_KEY`：务必替换成随机强密钥
- `CRAWLER_RATE_LIMIT_REQUESTS`：根据你期望的吞吐量调整
- `CRAWLER_RATE_LIMIT_WINDOW`：一般 60 秒

### Bridge

- `CRAWLER_API_BASE_URL`：云端 API 地址
- `CRAWLER_API_KEY`：与 API 一致
- `MCP_BEARER_TOKEN`：RikkaHub / MCP 客户端访问 Bridge 的 token
- `MCP_TRANSPORT=http`：如果你要远程访问 Bridge
- `MCP_HOST=0.0.0.0`
- `MCP_PORT=8001`

---

## 8) 工具映射

Bridge 当前暴露的 MCP tools：

- `health()`
- `fetch(url, options)`
- `parse(url, options)`
- `analyze(url, robots_mode, user_agent, timeout)`

---

## 9) 注意事项

1. 本地 `stdio` 模式最适合 Claude Desktop / Cursor 本地接入。
2. 云端建议使用 `Authorization: Bearer` + API Key + 限流。
3. 如果你的客户端只支持 stdio，不要把 Bridge 放成 HTTP 再去接。
4. 如果你使用 HTTP Bridge，建议再加一层反代或网关鉴权。
