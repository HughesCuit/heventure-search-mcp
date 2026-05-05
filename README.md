<!-- mcp-name: io.github.HughesCuit/heventure-search-mcp -->
[**中文**](./README_CN.md) | English

---

[![PyPI version](https://img.shields.io/pypi/v/heventure-search-mcp.svg)](https://pypi.org/project/heventure-search-mcp/)
[![Python](https://img.shields.io/pypi/pyversions/heventure-search-mcp.svg)](https://pypi.org/project/heventure-search-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://img.shields.io/pypi/dm/heventure-search-mcp.svg)](https://pypi.org/project/heventure-search-mcp/)

# 🔍 MCP Web Search Server

> **Free forever. No API key required.** A web search MCP server that works out of the box with Claude Desktop, Cursor, and any MCP-compatible AI tool.

```bash
pip install heventure-search-mcp
```

## ✨ Why?

Most MCP search servers require you to sign up for API keys (Bing, Google, SerpAPI...). This one works **immediately** — zero configuration, zero cost, zero sign-ups.

| Feature | This Server | Others |
|---------|:-----------:|:------:|
| No API key needed | ✅ | ❌ |
| DuckDuckGo (free) | ✅ | varies |
| Bing (free) | ✅ | ❌ |
| Google (free) | ✅ | ❌ |
| Optional SerpAPI/Tavily | ✅ | ✅ |
| Async + caching | ✅ | varies |
| Install in 10 seconds | ✅ | varies |

## 🚀 Quick Start

### Option 1: Claude Desktop / Cursor

Add to your MCP config:

```json
{
  "mcpServers": {
    "web-search": {
      "command": "uvx",
      "args": ["heventure-search-mcp"]
    }
  }
}
```

### Option 2: Command Line

```bash
pip install heventure-search-mcp
heventure-search-mcp
```

### Option 3: Docker

```bash
docker run -p 8080:8080 heventure-search-mcp
```

## 🔧 Available Tools

### `web_search`

Search the web with multiple engines simultaneously.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | *required* | Search query |
| `max_results` | int | 10 | Number of results (1-20) |
| `search_engine` | string | `"both"` | `duckduckgo`, `bing`, `google`, or `both` |

### `get_page_content`

Extract readable text from any webpage.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | string | *required* | Page URL to fetch |

## 🔑 Optional: Enhanced Search

The free engines work great for most use cases. For higher quality results, you can optionally add paid API keys:

```bash
# SerpAPI — 100 free searches/month
export SERPAPI_KEY="your_key"

# Tavily — 1,000 free searches/month  
export TAVILY_API_KEY="your_key"
```

## 🏗️ Architecture

- **Engines**: DuckDuckGo, Bing, Google, SerpAPI, Tavily
- **Caching**: LRU cache with 300s TTL (100 entries max)
- **Protocol**: MCP (Model Context Protocol)
- **Runtime**: Python 3.10+ with asyncio

## 🤝 Contributing

Issues and Pull Requests are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License — use it however you want.
