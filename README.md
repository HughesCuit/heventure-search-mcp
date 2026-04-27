<details>
<summary><b>点击切换到中文</b></summary>

# MCP Web Search Server

一个免费的、无需API key的网页搜索MCP（Model Context Protocol）服务器，支持DuckDuckGo、必应和Google搜索引擎。

## 功能特性

- 🔍 **多引擎搜索**: 支持DuckDuckGo、必应、Google，无需API key
- 📄 **网页内容获取**: 获取指定网页的文本内容
- 🚀 **异步处理**: 基于asyncio的高性能异步处理
- 🛡️ **安全可靠**: 不需要任何外部API密钥，保护隐私
- 🌐 **多种搜索方式**: 支持API和HTML两种搜索方式
- ⚡ **灵活选择**: 可选择单一搜索引擎或组合使用

## 安装方式

### PyPI（推荐）

```bash
pip install heventure-search-mcp
heventure-search-mcp
```

### uvx

```bash
uvx heventure-search-mcp
```

### 源码安装

```bash
pip install git+https://github.com/HughesCuit/heventure-search-mcp.git
python -m server
```

## 使用方法

### MCP客户端配置

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

### Trae AI配置

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

## 可用工具

### 1. web_search

搜索网页内容，支持多种搜索引擎

**参数:**
- `query` (string, 必需): 搜索查询词
- `max_results` (integer, 可选): 最大结果数量 (默认: 10)
- `search_engine` (string, 可选): 搜索引擎 (默认: "both")
  - `"duckduckgo"`: DuckDuckGo
  - `"bing"`: 必应
  - `"google"`: Google
  - `"both"`: 所有引擎

### 2. get_webpage_content

获取指定网页的文本内容

**参数:**
- `url` (string, 必需): 网页URL

## 技术实现

| 引擎 | 特点 |
|------|------|
| DuckDuckGo | 免费API、隐私保护、即时答案 |
| 必应 | 丰富结果、高质量 |
| Google | 全面结果、广泛覆盖 |

## 开发

```bash
git clone https://github.com/HughesCuit/heventure-search-mcp.git
cd heventure-search-mcp
pip install -e .
python -m pytest tests/
```

## 许可证

MIT License

---

</details>

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
- `max_results` (integer, optional): Max results (default: 10)
- `search_engine` (string, optional): Engine choice (default: "both")
  - `"duckduckgo"`: DuckDuckGo only
  - `"bing"`: Bing only
  - `"google"`: Google only
  - `"both"`: All engines combined

### 2. get_webpage_content

Get text content from a specified webpage.

**Parameters:**
- `url` (string, required): Target webpage URL

## Technical Details

| Engine | Features |
|--------|----------|
| DuckDuckGo | Free API, Privacy-first, Instant answers |
| Bing | Rich results, High quality |
| Google | Comprehensive results, Wide coverage |

## Development

```bash
git clone https://github.com/HughesCuit/heventure-search-mcp.git
cd heventure-search-mcp
pip install -e .
python -m pytest tests/
```

## License

MIT License
