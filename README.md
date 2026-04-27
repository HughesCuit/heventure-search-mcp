[**中文**](./README_CN.md) | English

---

# MCP Web Search Server

A free, API-key-free web search MCP (Model Context Protocol) server supporting DuckDuckGo, Bing, and Google search engines.

## Features

- 🔍 **Multi-Engine Search**: DuckDuckGo, Bing, Google support, no API key required
- 📄 **Web Content Fetching**: Get text content from any webpage
- 🚀 **Async Processing**: High-performance asyncio-based async handling
- 🛡️ **Secure & Private**: No external API keys needed, protects privacy

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
  - `"google"`: Google only
  - `"both"`: All engines combined

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
