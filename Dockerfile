FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md requirements.txt ./
COPY stealth_crawler ./stealth_crawler
COPY mcp_bridge ./mcp_bridge

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir ".[api,stealth,mcp]"

EXPOSE 8080

CMD ["uvicorn", "stealth_crawler.http_api:app", "--host", "0.0.0.0", "--port", "8080"]
