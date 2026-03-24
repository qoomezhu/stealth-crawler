# MCP Bridge for Stealth Crawler

This directory contains the bridge that exposes the crawler API as MCP tools.

## Run locally

```bash
pip install -e ".[mcp]"
python -m mcp_bridge.server
```

## Run as HTTP MCP server

```bash
MCP_TRANSPORT=http MCP_PORT=8001 python -m mcp_bridge.server
```

## Available tools

- `health()`
- `fetch(url, options)`
- `parse(url, options)`
- `analyze(url, robots_mode, user_agent, timeout)`

## Environment variables

- `CRAWLER_API_BASE_URL`: URL of the deployed crawler API
- `CRAWLER_API_KEY`: shared API key used by the bridge and the API
- `MCP_TRANSPORT`: `stdio` or `http`
- `MCP_HOST`: host for HTTP transport
- `MCP_PORT`: port for HTTP transport
