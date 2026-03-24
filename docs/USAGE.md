# Stealth Crawler 使用指南

## 目录

1. [快速开始](#快速开始)
2. [核心功能](#核心功能)
3. [高级配置](#高级配置)
4. [最佳实践](#最佳实践)
5. [常见问题](#常见问题)

---

## 快速开始

### 安装

```bash
git clone https://github.com/qoomezhu/stealth-crawler.git
cd stealth-crawler
pip install -r requirements.txt
```

### 基础用法

```python
from crawler import StealthCrawler

# 创建爬虫
crawler = StealthCrawler()

# 发送请求
response = crawler.get('https://example.com')
print(response.text)
```

---

## 核心功能

### 1. User-Agent 轮换

自动轮换真实浏览器 User-Agent，避免被检测：

```python
crawler = StealthCrawler(rotate_ua=True)

# 每次请求自动使用不同的 UA
for i in range(5):
    response = crawler.get('https://httpbin.org/user-agent')
    print(response.text)
```

### 2. 代理轮换

支持 HTTP/HTTPS/SOCKS5 代理池：

```python
proxies = [
    "http://user:pass@proxy1.example.com:8080",
    "http://user:pass@proxy2.example.com:8080",
    "socks5://user:pass@proxy3.example.com:1080",
]

crawler = StealthCrawler(
    proxies=proxies,
    rotate_proxy=True  # 启用轮换
)
```

### 3. TLS 指纹模拟

使用 `curl_cffi` 模拟真实浏览器 TLS 指纹：

```python
# 自动使用 Chrome 120 TLS 指纹
crawler = StealthCrawler()
response = crawler.get('https://tls.peet.ws/api/all')
```

### 4. 请求节流

随机延迟模拟人类行为：

```python
crawler = StealthCrawler(
    delay_range=(2, 5)  # 2-5 秒随机延迟
)
```

### 5. 自动重试

失败请求自动重试，支持指数退避：

```python
crawler = StealthCrawler(
    max_retries=5  # 最大重试 5 次
)
```

---

## 高级配置

### 自定义请求头

```python
custom_headers = {
    'Referer': 'https://google.com',
    'X-Custom-Header': 'value',
}

response = crawler.get(
    'https://example.com',
    headers=custom_headers
)
```

### POST 请求

```python
data = {
    'username': 'test',
    'password': '123456',
}

response = crawler.post(
    'https://example.com/login',
    data=data
)
```

### 异步爬取

```python
import asyncio
from crawler import AsyncStealthCrawler

async def main():
    crawler = AsyncStealthCrawler()
    
    urls = ['https://example.com/page1', 'https://example.com/page2']
    tasks = [crawler.get(url) for url in urls]
    responses = await asyncio.gather(*tasks)
    
    for resp in responses:
        print(len(resp))

asyncio.run(main())
```

---

## 最佳实践

### 1. 尊重 robots.txt

```python
from urllib.robotparser import RobotFileParser

rp = RobotFileParser()
rp.set_url('https://example.com/robots.txt')
rp.read()

if rp.can_fetch('MyBot', 'https://example.com/page'):
    crawler.get('https://example.com/page')
```

### 2. 合理设置延迟

```python
# 推荐：2-5 秒随机延迟
crawler = StealthCrawler(delay_range=(2, 5))
```

### 3. 使用高质量代理

```python
# 推荐：使用付费住宅代理
proxies = [
    'http://user:pass@residential-proxy.com:8080',
]
```

### 4. 监控统计信息

```python
# 发送请求后检查统计
stats = crawler.get_stats()
print(f"成功率：{stats['success'] / stats['requests'] * 100:.1f}%")
```

### 5. 错误处理

```python
try:
    response = crawler.get('https://example.com')
except Exception as e:
    print(f"请求失败：{e}")
    # 处理错误
```

---

## 常见问题

### Q: 如何避免被封禁？

A:
- 使用代理轮换
- 设置合理的请求延迟
- 轮换 User-Agent
- 模拟真实浏览器行为

### Q: 支持哪些代理协议？

A: 支持 HTTP、HTTPS、SOCKS4、SOCKS5。

### Q: 如何处理 CAPTCHA？

A: 本库不直接处理 CAPTCHA，建议：
- 使用第三方 CAPTCHA 解决服务
- 降低请求频率
- 使用住宅代理

### Q: 异步爬虫和同步爬虫的区别？

A:
- 同步：适合简单场景，易于调试
- 异步：适合高并发场景，效率更高

---

## 许可证

MIT License
