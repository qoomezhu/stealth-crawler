# 部署与 MCP 调用方案

## 结论

可以。当前仓库已经具备两层能力：

1. **Docker 镜像**：将爬虫能力封装成容器
2. **HTTP API**：对外提供 `/fetch`、`/parse`、`/analyze` 接口

这意味着后续你可以把容器部署到云端，然后再用一个单独的 **MCP Bridge** 把 MCP 工具调用转成 HTTP 请求。

---

## 推荐架构

```text
MCP Client / LLM
      ↓
MCP Bridge Server
      ↓ HTTP
Cloud Docker Service
      ↓
Stealth Crawler API
      ↓
目标网站
```

---

## 为什么要这样分层

### 1. Docker 容器只负责业务能力
- 抓取
- 解析
- robots 检查
- 代理池

### 2. MCP Bridge 只负责工具协议
- 把 `fetch(url)`、`parse(url)`、`analyze(url)` 变成 MCP tools
- 负责参数校验、鉴权、日志、限流

### 3. 云端服务只暴露 HTTP
- 易于部署
- 易于扩容
- 易于观测
- 更容易接入 API Gateway / WAF / Auth

---

## 部署步骤

### Step 1: 构建 Docker 镜像

```bash
docker build -t stealth-crawler:latest .
```

### Step 2: 运行容器

```bash
docker run --rm -p 8080:8080 stealth-crawler:latest
```

### Step 3: 云端部署

可以部署到：
- Cloud Run
- ECS / Fargate
- Fly.io
- Kubernetes
- 任何支持容器的平台

### Step 4: MCP Bridge 对接

MCP Bridge 只需要把 MCP 工具映射到这些 HTTP 接口：

- `crawl.fetch` → `POST /fetch`
- `crawl.parse` → `POST /parse`
- `crawl.analyze` → `POST /analyze`
- `crawl.health` → `GET /health`

---

## 建议的安全措施

### 必加
- API Key / Bearer Token
- IP 白名单
- 请求超时
- 并发限制
- 日志审计

### 建议
- 请求体大小限制
- 目标域名白名单
- 失败重试上限
- 响应缓存

---

## MCP Bridge 可实现的工具示例

```text
crawl.fetch
crawl.parse
crawl.analyze
crawl.health
```

调用侧只需要给出：
- url
- robots_mode
- timeout
- proxies（可选）
- headers（可选）

---

## 结论

**能做，而且这是最合理的实现方式。**

如果你愿意，我下一步可以继续直接帮你补一个 **MCP Bridge 代码骨架**，让它真正能对接到这套云端 API。
