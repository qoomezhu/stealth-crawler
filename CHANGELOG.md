# Stealth Crawler - 更新日志

## v2.2.0 - RikkaHub Bearer Auth / Remote MCP Endpoint

### 新增

- `mcp_bridge/server.py`：HTTP MCP endpoint 支持 `Authorization: Bearer` 鉴权
- `docs/RIKKAHUB.md`：RikkaHub 专用接入说明
- `docs/MCP_CLIENTS.md`：补充远程 Bearer 连接示例

### 改进

- `docker-compose.yml` 增加 `MCP_BEARER_TOKEN`
- `deploy/cloudrun-mcp-bridge.yaml` 增加 Bearer Token 环境变量
- `README.md` 与 `docs/DEPLOYMENT.md` 同步更新
- `pyproject.toml` 中 `fastmcp` 版本提升到支持 `http_app()` 的版本

---

## v2.1.1 - MCP Bridge / Docker / Security

### 新增

- `stealth_crawler/cli.py`：统一 CLI
- `stealth_crawler/http_api.py`：HTTP API
- `stealth_crawler/security.py`：API Key 鉴权 + 内存限流
- `mcp_bridge/server.py`：MCP Bridge（通过 MCP 调用远端 API）
- `docker-compose.yml`：本地 API + Bridge 联调模板
- `deploy/cloudrun-api.yaml` / `deploy/cloudrun-mcp-bridge.yaml`：云端部署模板
- `.env.example`：环境变量模板

### 改进

- 清理根目录旧模块，统一为包结构
- `pyproject.toml` 增加 `mcp` extra
- Docker 镜像支持 API 与 MCP Bridge 运行
- README 与部署文档同步更新

---

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

---

## 反爬压力测试

### 测试场景

```python
from smart_crawler import SmartStealthCrawler

# 创建忽略模式的爬虫用于压力测试
crawler = SmartStealthCrawler(
    robots_mode='ignore',  # 🚨 完全忽略 robots.txt
    rotate_proxy=True,     # 轮换代理
    rotate_ua=True,        # 轮换 User-Agent
    delay_range=(0.5, 1),  # 短延迟
    max_retries=5,         # 多次重试
)
```

---

## 文件结构更新

```text
stealth-crawler/
├── stealth_crawler/
├── mcp_bridge/
├── deploy/
├── examples/
├── tests/
└── ...
```
