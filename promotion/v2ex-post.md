# 做了个免费的 MCP 搜索服务器，不需要任何 API Key

项目地址：https://github.com/HughesCuit/heventure-search-mcp

## 背景

最近在用 Claude Desktop + MCP 做开发，想给 AI 加个网页搜索能力。结果发现市面上的 MCP 搜索服务器基本都要 API Key——Bing、Google、SerpAPI、Tavily，每家都要注册、申请、配置。

我就想：有没有一个装上就能用、不需要任何 key 的？

搜了一圈没找到满意的，就自己做了一个。

## 特点

- **零配置**：`pip install heventure-search-mcp` 装完直接用
- **三引擎**：DuckDuckGo + Bing + Google，全部免费
- **可选增强**：如果需要更高质量的搜索结果，可以加 SerpAPI 或 Tavily 的 key
- **异步 + 缓存**：asyncio 高性能，LRU 缓存避免重复请求

## 用法

Claude Desktop 配置：

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

或者命令行：

```bash
pip install heventure-search-mcp
heventure-search-mcp
```

## 对比

| 功能 | 本项目 | Brave Search | SerpAPI | Tavily |
|------|:------:|:------------:|:-------:|:------:|
| 不需要 API Key | ✅ | ❌ | ❌ | ❌ |
| 免费额度 | 无限 | - | 100次/月 | 1000次/月 |
| DuckDuckGo | ✅ | - | - | - |
| Bing | ✅ | - | - | - |
| Google | ✅ | - | ✅ | ✅ |

## 技术栈

Python 3.10+ / asyncio / MCP Protocol

开源协议 MIT，欢迎 star 和 PR！
