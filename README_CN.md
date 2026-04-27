[English](./README.md) | **中文**

---

# MCP Web Search Server

一个免费的、无需API key的网页搜索MCP（Model Context Protocol）服务器，支持DuckDuckGo、必应，以及可选的 SerpAPI/Tavily 以提升搜索质量。

## 功能特性

- 🔍 **多引擎搜索**: DuckDuckGo + 必应（免费，无需 API Key）
- 🔑 **可选 API Key**: 配置 SerpAPI 或 Tavily 提升搜索质量
- 📄 **网页内容获取**: 获取指定网页的文本内容
- 🚀 **异步处理**: 基于asyncio的高性能异步处理

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

## 可用工具

### web_search

搜索网页内容，支持多种搜索引擎

**参数:**
- `query` (string, 必需): 搜索查询词
- `max_results` (integer, 可选): 最大结果数量 (默认: 10, 范围: 1-20)
- `search_engine` (string, 可选): 搜索引擎选择 (默认: "both")
  - `"duckduckgo"`: 仅使用DuckDuckGo搜索
  - `"bing"`: 仅使用必应搜索
  - `"both"`: DuckDuckGo + 必应

### 可选 API Key（提升搜索质量）

您可以通过设置环境变量来启用付费搜索服务：

```bash
# SerpAPI（通过 API 获取 Google 搜索结果，每月免费 100 次）
export SERPAPI_KEY="your_serpapi_key"

# Tavily（AI 优化搜索，每月免费 1000 次）
export TAVILY_API_KEY="your_tavily_api_key"
```

配置 API Key 后，系统会自动与免费引擎一起使用以提升搜索质量。

**示例:**
```json
{
  "query": "Python编程教程",
  "max_results": 5,
  "search_engine": "both"
}
```

### get_webpage_content

获取指定网页的文本内容

**参数:**
- `url` (string, 必需): 要获取内容的网页URL

**示例:**
```json
{
  "url": "https://example.com"
}
```

## 错误处理

- 网络请求失败自动重试
- 解析错误优雅降级
- 用户友好的错误消息

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request来改进这个项目！
