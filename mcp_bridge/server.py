from __future__ import annotations

import os

from stealth_crawler.http_api import app, mcp

MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "http").strip().lower()
MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.getenv("MCP_PORT", "8001"))


if __name__ == "__main__":
    if MCP_TRANSPORT == "http":
        import uvicorn

        uvicorn.run(app, host=MCP_HOST, port=MCP_PORT)
    else:
        mcp.run()
