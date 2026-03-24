# 部署指南

本文档说明如何将 Stealth Crawler 打包成 Docker 镜像、部署到云端，以及通过 MCP Bridge 进行调用。

---

## 1. 本地开发

### 安装依赖

```bash
pip install -e ".[api,stealth,mcp]"
```

### 启动 HTTP API

```bash
uvicorn stealth_crawler.http_api:app --host 0.0.0.0 --port 8080
```

### 启动 MCP Bridge

```bash
python -m mcp_bridge.server
```

---

## 2. Docker

### 构建镜像

```bash
docker build -t stealth-crawler:latest .
```

### 启动单容器 API

```bash
docker run --rm -p 8080:8080 \
  -e CRAWLER_API_KEY=dev-secret-change-me \
  -e CRAWLER_RATE_LIMIT_REQUESTS=60 \
  -e CRAWLER_RATE_LIMIT_WINDOW=60 \
  stealth-crawler:latest
```

### 使用 Compose 启动 API + MCP Bridge

```bash
docker compose up --build
```

Compose 中包含：
- `api`：HTTP 爬虫服务
- `mcp-bridge`：MCP Bridge 服务

---

## 3. 云端部署

推荐两种独立服务：

### A. API 服务
部署 `stealth_crawler.http_api:app`

环境变量：
- `CRAWLER_API_KEY`
- `CRAWLER_RATE_LIMIT_REQUESTS`
- `CRAWLER_RATE_LIMIT_WINDOW`

### B. MCP Bridge 服务
部署 `mcp_bridge.server`

环境变量：
- `CRAWLER_API_BASE_URL`
- `CRAWLER_API_KEY`
- `MCP_TRANSPORT=http`
- `MCP_HOST=0.0.0.0`
- `MCP_PORT=8001`

---

## 4. Cloud Run YAML 模板

仓库中提供：

- `deploy/cloudrun-api.yaml`
- `deploy/cloudrun-mcp-bridge.yaml`

把其中的以下占位符替换掉即可：
- `PROJECT_ID`
- `REPOSITORY`
- `REGION`
- `CHANGE_ME`
- `YOUR-API-DOMAIN`

---

## 5. MCP 调用链路

```text
MCP Client
  ↓
MCP Bridge
  ↓ HTTP
Cloud API
  ↓
Crawler
```

### MCP Bridge 提供的工具
- `health()`
- `fetch(url, options)`
- `parse(url, options)`
- `analyze(url, robots_mode, user_agent, timeout)`

---

## 6. 安全建议

建议至少启用：
- API Key
- 速率限制
- 云端日志审计
- 域名白名单
- 请求超时限制

---

## 7. 推荐上线顺序

1. 本地 Docker Compose 跑通
2. 云端部署 API
3. 加 API Key 和限流
4. 云端部署 MCP Bridge
5. MCP Client 接入

---

## 8. 验证方法

### Health 检查

```bash
curl http://localhost:8080/health
```

### 带鉴权的抓取

```bash
curl -X POST http://localhost:8080/fetch \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: dev-secret-change-me' \
  -d '{"url":"https://httpbin.org/html","options":{}}'
```
