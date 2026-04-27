[**中文**](./README_CN.md) | English

---

# MCP Web Search Server

A free, API-key-free web search MCP (Model Context Protocol) server supporting DuckDuckGo, Bing, and optional SerpAPI/Tavily for enhanced search quality.

## Features

- 🔍 **Multi-Engine Search**: DuckDuckGo + Bing (free, no API key required)
- 🔑 **Optional API Keys**: SerpAPI and Tavily for better search quality
- 📄 **Web Content Fetching**: Get text content from any webpage
- 🚀 **Async Processing**: High-performance asyncio-based async handling

## Installation

### PyPI (Recommended)

```bash
pip install heventure-search-mcp
heventure-search-mcp
```

### uvx

```bash
uvx heventure-search-mcp
```

### From Source

```bash
pip install git+https://github.com/HughesCuit/heventure-search-mcp.git
python -m server
```

## Usage

### MCP Client Config

```json
{
  "mcpServers": {
    "web-search": {
      "command": "python",
      "args": ["/path/to/server.py"]
    }
  }
}
```

### Trae AI

```json
{
  "mcpServers": {
    "heventure-search-mcp": {
      "command": "uvx",
      "args": ["heventure-search-mcp"]
    }
  }
}
```

## Available Tools

### web_search

Search web content with multiple engines.

**Parameters:**
- `query` (string, required): Search query
- `max_results` (integer, optional): Max results (default: 10, range: 1-20)
- `search_engine` (string, optional): Engine choice (default: "both")
  - `"duckduckgo"`: DuckDuckGo only
  - `"bing"`: Bing only
  - `"both"`: DuckDuckGo + Bing

### Optional API Keys (for Enhanced Search)

You can optionally set environment variables to enable paid search engines:

```bash
# SerpAPI (Google search results via API, 100 searches/month free)
export SERPAPI_KEY="your_serpapi_key"

# Tavily (AI-optimized search, 1000 searches/month free)
export TAVILY_API_KEY="your_tavily_api_key"
```

When API keys are configured, they will be automatically used alongside the free engines to improve search quality.

**Example:**
```json
{
  "query": "Python tutorial",
  "max_results": 5,
  "search_engine": "both"
}
```

### get_webpage_content

Get text content from a webpage.

**Parameters:**
- `url` (string, required): Target webpage URL

**Example:**
```json
{
  "url": "https://example.com"
}
```

## Error Handling

- Automatic retry on network failure
- Graceful degradation on parse errors
- User-friendly error messages

## License

MIT License

## Contributing

Issues and Pull Requests are welcome!
