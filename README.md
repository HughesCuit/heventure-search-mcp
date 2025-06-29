# MCP Web Search Server

一个无需API key的网页搜索MCP（Model Context Protocol）服务器，使用DuckDuckGo搜索引擎提供网页搜索功能。

## 功能特性

- 🔍 **网页搜索**: 使用DuckDuckGo进行网页搜索，无需API key
- 📄 **网页内容获取**: 获取指定网页的文本内容
- 🚀 **异步处理**: 基于asyncio的高性能异步处理
- 🛡️ **安全可靠**: 不需要任何外部API密钥，保护隐私
- 🌐 **多种搜索方式**: 支持API和HTML两种搜索方式

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 直接运行服务器

```bash
python server.py
```

### 作为MCP服务器使用

在你的MCP客户端配置中添加此服务器：

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

## 可用工具

### 1. web_search

搜索网页内容

**参数:**
- `query` (string, 必需): 搜索查询词
- `max_results` (integer, 可选): 最大结果数量 (默认: 10, 范围: 1-20)

**示例:**
```json
{
  "query": "Python编程教程",
  "max_results": 5
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

本服务使用DuckDuckGo作为搜索引擎，原因如下：

1. **无需API key**: DuckDuckGo提供免费的搜索API
2. **隐私保护**: 不跟踪用户搜索历史
3. **稳定可靠**: 提供稳定的搜索服务
4. **多种接口**: 支持API和HTML两种访问方式

### 搜索策略

1. **优先使用API**: 首先尝试使用DuckDuckGo的即时答案API
2. **HTML备用**: 如果API结果不足，使用HTML页面解析
3. **结果合并**: 将两种方式的结果合并，去重并排序

### 内容提取

- 使用BeautifulSoup解析HTML内容
- 自动移除脚本和样式标签
- 清理和格式化文本内容
- 限制内容长度避免过长响应

## 项目结构

```
mcp_dev/
├── server.py          # 主服务器文件
├── requirements.txt   # 项目依赖
├── README.md         # 项目说明
└── config.json       # MCP配置示例
```

## 配置说明

### 用户代理

服务器使用标准的浏览器用户代理字符串来避免被网站阻止：

```python
'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
```

### 超时设置

- 网页内容获取超时: 10秒
- 搜索请求超时: 默认aiohttp超时

### 内容限制

- 网页内容最大长度: 2000字符
- 最大搜索结果数: 20个

## 错误处理

服务器包含完善的错误处理机制：

- 网络请求失败自动重试
- 解析错误优雅降级
- 详细的错误日志记录
- 用户友好的错误消息

## 注意事项

1. **网络依赖**: 需要稳定的网络连接
2. **速率限制**: 请合理使用，避免过于频繁的请求
3. **内容准确性**: 搜索结果来自第三方，请自行验证内容准确性
4. **法律合规**: 请遵守相关法律法规和网站使用条款

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request来改进这个项目！