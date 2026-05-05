# I built a free MCP web search server — no API keys needed

Hey r/mcp! 👋

I got tired of every MCP search server requiring API keys (Bing, Google, SerpAPI...), so I built one that works out of the box with **zero configuration**.

## What is it?

**[heventure-search-mcp](https://github.com/HughesCuit/heventure-search-mcp)** — a free, open-source MCP web search server.

```bash
pip install heventure-search-mcp
```

## Why?

- Most MCP search servers need at least one API key
- Free tiers are limited (100-1000 searches/month)
- I wanted something that **just works** immediately

## Features

- 🔍 **Multi-engine search**: DuckDuckGo + Bing + Google (all free!)
- 🔑 **Optional API keys**: SerpAPI/Tavily for enhanced quality
- 🚀 **Async + caching**: High-performance with LRU cache
- 📦 **10-second install**: `pip install` or `uvx`

## Quick Start

Add to your Claude Desktop config:

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

## Comparison

| Feature | This Server | Brave Search | SerpAPI | Tavily |
|---------|:-----------:|:------------:|:-------:|:------:|
| No API key | ✅ | ❌ | ❌ | ❌ |
| DuckDuckGo | ✅ | - | - | - |
| Bing | ✅ | - | - | - |
| Google | ✅ | - | ✅ | ✅ |
| Free tier | ∞ | - | 100/mo | 1000/mo |
| Async | ✅ | varies | ✅ | ✅ |

## Links

- GitHub: https://github.com/HughesCuit/heventure-search-mcp
- PyPI: https://pypi.org/project/heventure-search-mcp/
- License: MIT

Would love your feedback! 🙏
