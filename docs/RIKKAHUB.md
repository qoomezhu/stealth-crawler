# RikkaHub 连接 Stealth Crawler MCP 的推荐方式

本文件专门给 RikkaHub 使用。目标是让 RikkaHub 通过 **Authorization: Bearer** 访问你远程部署的 MCP Bridge。

---

## 1. 远端 MCP 地址

假设你的 Bridge 部署在：

```text
https://your-bridge-domain.example.com/mcp
```

那么 RikkaHub 连接时需要在请求头里携带：

```http
Authorization: Bearer your-mcp-token
```

其中 `your-mcp-token` 必须和服务端环境变量 `MCP_BEARER_TOKEN` 一致。

---

## 2. 推荐配置示例

如果 RikkaHub 使用类似 JSON 的 MCP Server 配置，可以参考：

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

---

## 3. 服务端环境变量

部署 MCP Bridge 时，建议设置：

```bash
CRAWLER_API_BASE_URL=https://your-api-domain.example.com
CRAWLER_API_KEY=your-upstream-api-key
MCP_TRANSPORT=http
MCP_BEARER_TOKEN=your-mcp-token
MCP_PUBLIC_PATHS=/healthz
```

---

## 4. 接口说明

RikkaHub 只需要连接 MCP Bridge，不需要直接调用 crawler API。

MCP Bridge 暴露的工具：
- `health()`
- `fetch(url, options)`
- `parse(url, options)`
- `analyze(url, robots_mode, user_agent, timeout)`

---

## 5. 调试建议

### 先用 curl 验证

```bash
curl -i https://your-bridge-domain.example.com/mcp \
  -H 'Authorization: Bearer your-mcp-token'
```

### 再在 RikkaHub 中接入

如果 `curl` 可以拿到 200/合法 MCP 响应，再在 RikkaHub 中添加相同的 URL 与 Authorization 头。

---

## 6. 常见错误

- **401 Unauthorized**：token 不一致，或请求头没有带 `Bearer`
- **404 Not Found**：MCP 路径写错，确认是 `/mcp`
- **502/503**：Bridge 没起来，或者云端反代配置有误
