[**中文**](./README_CN.md) | English

---

# MCP Web Search Server

A free, API-key-free web search MCP (Model Context Protocol) server supporting DuckDuckGo, Bing, and Google search engines.

## Features

- 🔍 **Multi-Engine Search**: DuckDuckGo, Bing, Google support, no API key required
- 📄 **Web Content Fetching**: Get text content from any webpage
- 🚀 **Async Processing**: High-performance asyncio-based async handling
- 🛡️ **Secure & Private**: No external API keys needed, protects privacy
- 🌐 **Multiple Search Methods**: API and HTML search modes
- ⚡ **Flexible Choice**: Use single engine or combine multiple

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

### Manual

```bash
git clone https://github.com/HughesCuit/heventure-search-mcp.git
cd heventure-search-mcp
pip install -r requirements.txt
```

## Usage

### Run Server Directly

```bash
python server.py
```

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

### Trae AI Configuration

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

### 1. web_search

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

### 2. get_webpage_content

Get text content from a specified webpage.

**Parameters:**
- `url` (string, required): Target webpage URL

**Example:**
```json
{
  "url": "https://example.com"
}
```

## Technical Details

### Search Engines

| Engine | Features |
|--------|----------|
| DuckDuckGo | Free API, Privacy-first, Instant answers |
| Bing | Rich results, High quality, Good complement |
| Google | Comprehensive results, Wide coverage |

### Search Strategy

1. **DuckDuckGo**: API first, fallback to HTML parsing
2. **Bing**: HTML page parsing
3. **Google**: HTML parsing with anti-captcha detection
4. **Combined**: Merge and dedupe results from all engines

### Content Extraction

- BeautifulSoup for HTML parsing
- Auto-remove script and style tags
- Clean and format text content
- Limit length to avoid oversized responses

## Configuration

### User Agent

```python
'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
```

### Limits

- Content max length: 2000 characters
- Max search results: 20

## Error Handling

- Automatic retry on network failure
- Graceful degradation on parse errors
- Detailed error logging
- User-friendly error messages

## Development

### Local Development

```bash
git clone https://github.com/HughesCuit/heventure-search-mcp.git
cd heventure-search-mcp
pip install -e .

# Run tests
python -m pytest tests/

# Run benchmark
python benchmark.py
```

### Publish to PyPI

```bash
# Publish to TestPyPI
python publish.py test

# Publish to PyPI
python publish.py prod

# Build only
python publish.py build
```

**Before publishing:**

1. Configure PyPI API Token (see `~/.pypirc`)
2. Update version in `pyproject.toml`
3. Update `CHANGELOG.md`
4. Ensure all tests pass

## License

MIT License

## Contributing

Issues and Pull Requests are welcome!
