---
name: heventure-search-mcp
description: >
  Use when: agent needs web search (multi-engine: DuckDuckGo/Bing/Google, free, no API key). Install: pip install heventure-search-mcp
---

# heventure-search-mcp

A free MCP (Model Context Protocol) web search server with no API key required for core search.

## ⚡ Environment Variables

Set these **before** starting the server to enable paid search engines:

| Variable | Required By | Free Tier | Get Key |
|----------|-------------|-----------|---------|
| `SERPAPI_KEY` | `serpapi` engine | 100 req/month | [serpapi.com](https://serpapi.com) |
| `TAVILY_API_KEY` | `tavily` engine | 1000 req/month | [tavily.com](https://tavily.com) |

> **Note:** Free engines (DuckDuckGo, Bing, Google) work without any API key.
> Without these env vars, `serpapi`/`tavily` engines will silently fail.

Example:
```bash
export SERPAPI_KEY="your_key"
export TAVILY_API_KEY="your_key"
```

## TRIGGER when...

Load this MCP server when **any** of the following conditions apply:

1. **User or agent needs to search the web** — e.g. "search for X", "find information about Y", "look up Z online"
2. **Built-in `web_search` tool is unavailable or fails** — this MCP provides a fallback with multiple engines
3. **Configuring an MCP server** — the user wants to set up `web-search` as an MCP tool in Claude Desktop, Hermes Agent, Cursor, or similar
4. **Need free, API-key-free search** — DuckDuckGo/Bing/Google engines work without any keys
5. **Need to fetch webpage content** — the `get_webpage_content` tool extracts text from URLs

**Do NOT load when:**

- Built-in `web_search` is already working and the user has no preference for MCP tools
- The user wants to configure or deploy Firecrawl (use `firecrawl-self-hosted` skill instead)
- The user is asking about search engine internals or API implementation details (not usage)

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
| `search_engine` | string | no | `"both"` | Engine: `"duckduckgo"` / `"bing"` / `"google"` (free) / `"serpapi"` (needs SERPAPI_KEY) / `"tavily"` (needs TAVILY_API_KEY) / `"both"` (free engines only) |

#### `search_engine="both"` behavior

When set to `"both"` (the default), the server:

1. Runs **DuckDuckGo + Google + Bing** in parallel via `asyncio.gather`
2. Appends **SerpAPI** / **Tavily** if their API keys (`SERPAPI_KEY`, `TAVILY_API_KEY`) are set
3. Merges all results and **deduplicates by URL**
4. Sorts by engine priority: SerpAPI/Tavily (0) → Google (1) → Bing (2) → DuckDuckGo (3)
5. **Truncates to the top `max_results`** — so even though 3–5 engines run in parallel, the final list is capped

For single-engine mode (e.g. `"duckduckgo"`), only that engine runs and results are returned as-is (no truncation).

### `get_webpage_content`

Fetch text content from a URL.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | string | yes | Target webpage URL |

## Search Engines

| Engine | Free | API Key | Notes |
|--------|------|---------|-------|
| DuckDuckGo | ✅ | No | Default engine, great privacy |
| Bing | ✅ | No | Rich results, good for news |
| Google | ✅ | No | Scraping-based, may hit rate limits |
| SerpAPI | ❌ | Yes | Google API results, 100 free/month |
| Tavily | ❌ | Yes | AI-optimized, 1000 free/month |

## Error Handling & Timeouts

### CAPTCHA Detection

The server detects CAPTCHA/challenge pages and gracefully degrades:

| Engine | Detection Method | Behavior |
|--------|-----------------|----------|
| Bing | Scans HTML for `challenge`, `solve the challenge`, `captcha` (case-insensitive) | Returns empty results with warning log |
| Google | Scans HTML for `captcha` (case-insensitive) | Skips that domain, tries next domain variant (`.com` → `.com.hk` → `.co.jp`) |

CAPTCHA detection is a best-effort heuristic — it may not catch all challenge formats.

### Request Timeouts

| Engine | Timeout | Notes |
|--------|---------|-------|
| DuckDuckGo (API + HTML) | 10s | Per-request total timeout |
| Bing | 10s | Per-request total timeout, fallback to `cn.bing.com` on failure |
| Google | 10s | Per-request total timeout, tries 3 domains in sequence |
| SerpAPI | 30s | API call with JSON response |
| Tavily | 30s | API call with JSON response |
| `get_webpage_content` | 10s | Single page fetch |
| Shared aiohttp session | 30s | Global fallback for any request without explicit timeout |

### Retry Strategy

Two retry mechanisms exist, both with identical defaults:

| Method | Used By | Retries | Delay | Retryable Errors |
|--------|---------|---------|-------|-------------------|
| `_safe_get_with_retry` | Bing, Google | 1 (total 2 attempts) | 1.0s | TimeoutError, ClientError, ConnectionError, OSError |
| `_request_with_retry` | DuckDuckGo (API + HTML) | 1 (total 2 attempts) | 1.0s | TimeoutError, ClientError, ConnectionError, OSError |

Paid engines (SerpAPI, Tavily) do NOT retry — they rely on their own API reliability.

### Other Error Scenarios

| Scenario | Behavior |
|----------|----------|
| **SSRF protection** | Blocks private/loopback/link-local/reserved IPs. DNS rebinding: resolves hostname and checks resolved IPs before connecting. |
| **Redirect loops** | Tracks visited URLs, breaks on cycles. Bing-specific: strips `mkt` parameter and normalizes `bing.com`/`cn.bing.com` → `www.bing.com`. Max 5 redirects. |
| **Unicode decode errors** | Falls back to raw `bytes.decode('utf-8', errors='replace')` |
| **Non-HTML content** | `get_webpage_content` rejects PDF, images, etc. (checks `Content-Type: text/html`) |
| **Empty response** | Google skips pages shorter than 500 chars |
| **Cache** | 300s TTL, max 100 entries, LRU eviction. Avoids re-fetching within TTL window. |
| **DuckDuckGo API fallback** | If JSON API fails or returns empty, falls back to HTML scraping (`html.duckduckgo.com`) |

## License

MIT
