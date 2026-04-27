[English](./README.md) | **中文**

---

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

### 手动安装

```bash
git clone https://github.com/HughesCuit/heventure-search-mcp.git
cd heventure-search-mcp
pip install -r requirements.txt
```

## 使用方法

### 直接运行

```bash
python server.py
```

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
- `max_results` (integer, 可选): 最大结果数量 (默认: 10, 范围: 1-20)
- `search_engine` (string, 可选): 搜索引擎选择 (默认: "both")
  - `"duckduckgo"`: 仅使用DuckDuckGo搜索
  - `"bing"`: 仅使用必应搜索
  - `"google"`: 仅使用Google搜索
  - `"both"`: 同时使用所有搜索引擎

**示例:**
```json
{
  "query": "Python编程教程",
  "max_results": 5,
  "search_engine": "both"
}
```

### 2. get_webpage_content

获取指定网页的文本内容

**参数:**
- `url` (string, 必需): 要获取内容的网页URL

**示例:**
```json
{
  "url": "https://example.com"
}
```

## 技术实现

### 搜索引擎

| 引擎 | 特点 |
|------|------|
| DuckDuckGo | 免费API、隐私保护、即时答案 |
| 必应 | 丰富结果、高质量、良好补充 |
| Google | 全面结果、广泛覆盖 |

### 搜索策略

1. **DuckDuckGo**: 优先使用API，不足时使用HTML解析
2. **必应**: 通过HTML页面解析获取搜索结果
3. **Google**: HTML解析，反爬虫检测
4. **组合策略**: 合并多个引擎的结果并去重

### 内容提取

- BeautifulSoup解析HTML内容
- 自动移除脚本和样式标签
- 清理和格式化文本内容
- 限制内容长度避免过长响应

## 配置说明

### 用户代理

```python
'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
```

### 限制

- 网页内容最大长度: 2000字符
- 最大搜索结果数: 20个

## 错误处理

- 网络请求失败自动重试
- 解析错误优雅降级
- 详细的错误日志记录
- 用户友好的错误消息

## 开发

### 本地开发

```bash
git clone https://github.com/HughesCuit/heventure-search-mcp.git
cd heventure-search-mcp
pip install -e .

# 运行测试
python -m pytest tests/

# 运行基准测试
python benchmark.py
```

### 发布到PyPI

```bash
# 发布到TestPyPI（测试）
python publish.py test

# 发布到正式PyPI
python publish.py prod

# 仅构建包
python publish.py build
```

**发布前准备：**

1. 配置PyPI API Token（见 `~/.pypirc`）
2. 更新版本号（在 `pyproject.toml` 中）
3. 更新 `CHANGELOG.md`
4. 确保所有测试通过

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request来改进这个项目！
