---
name: heventure-search-mcp
description: >
  Free, API-key-free web search MCP server — DuckDuckGo, Bing, Google & optional SerpAPI/Tavily.
  Install: pip install heventure-search-mcp
---

# heventure-search-mcp

A free MCP (Model Context Protocol) web search server with no API key required for core search.

## Quick Start

### Run via uvx (recommended)

```bash
uvx heventure-search-mcp
```

### Run via pip

```bash
pip install heventure-search-mcp
heventure-search-mcp
```

### Run from source

```bash
pip install git+https://github.com/HughesCuit/heventure-search-mcp.git
python -m server
```

## MCP Client Configuration

### Claude Desktop / Claude Code

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

### Hermes Agent / OpenCode / Cursor

```json
{
  "mcpServers": {
    "web-search": {
      "command": "python",
      "args": ["-m", "server"]
    }
  }
}
```

## Available Tools

### `web_search`

Search the web with multiple engines.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | yes | — | Search query |
| `max_results` | integer | no | 10 | Max results (1–20) |
| `search_engine` | string | no | `"both"` | Engine: `"duckduckgo"`, `"bing"`, `"google"`, `"serpapi"`, `"tavily"`, or `"both"` (all free engines) |

### `get_webpage_content`

Fetch text content from a URL.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | string | yes | Target webpage URL |

## Optional API Keys

Set these environment variables to enable paid search engines for higher quality results:

```bash
export SERPAPI_KEY="your_key"    # Google results via API, 100 free/month
export TAVILY_API_KEY="your_key" # AI-optimized search, 1000 free/month
```

When configured, paid engines run alongside free engines automatically.

## Search Engines

| Engine | Free | API Key | Notes |
|--------|------|---------|-------|
| DuckDuckGo | ✅ | No | Default engine, great privacy |
| Bing | ✅ | No | Rich results, good for news |
| Google | ✅ | No | Scraping-based, may hit rate limits |
| SerpAPI | ❌ | Yes | Google API results, 100 free/month |
| Tavily | ❌ | Yes | AI-optimized, 1000 free/month |

## Features

- Multi-engine parallel search with `asyncio.gather`
- Automatic result deduplication and ranking
- Search result caching (300s TTL)
- Graceful fallback on network errors
- Configurable SSL verification (`WEB_SEARCH_SSL_VERIFY`)

## License

MIT
