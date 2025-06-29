# MCP Web Search Server 使用示例

本文档提供了MCP Web Search Server的详细使用示例。

## 基本使用

### 1. 启动服务器

```bash
# 使用启动脚本
./start_server.sh

# 或直接运行
python3 server.py
```

### 2. 工具调用示例

#### web_search 工具

**基本搜索:**
```json
{
  "name": "web_search",
  "arguments": {
    "query": "Python编程教程"
  }
}
```

**限制结果数量:**
```json
{
  "name": "web_search",
  "arguments": {
    "query": "机器学习算法",
    "max_results": 5
  }
}
```

**中文搜索:**
```json
{
  "name": "web_search",
  "arguments": {
    "query": "人工智能发展趋势 2024",
    "max_results": 8
  }
}
```

**英文搜索:**
```json
{
  "name": "web_search",
  "arguments": {
    "query": "artificial intelligence trends 2024",
    "max_results": 10
  }
}
```

#### get_webpage_content 工具

**获取网页内容:**
```json
{
  "name": "get_webpage_content",
  "arguments": {
    "url": "https://www.python.org"
  }
}
```

**获取新闻文章:**
```json
{
  "name": "get_webpage_content",
  "arguments": {
    "url": "https://news.ycombinator.com"
  }
}
```

## 实际应用场景

### 场景1: 技术研究

```json
// 1. 搜索相关技术
{
  "name": "web_search",
  "arguments": {
    "query": "Docker容器化最佳实践",
    "max_results": 5
  }
}

// 2. 获取具体文章内容
{
  "name": "get_webpage_content",
  "arguments": {
    "url": "https://docs.docker.com/develop/best-practices/"
  }
}
```

### 场景2: 学习资源收集

```json
// 搜索学习资源
{
  "name": "web_search",
  "arguments": {
    "query": "React.js 入门教程 2024",
    "max_results": 10
  }
}
```

### 场景3: 新闻和资讯

```json
// 搜索最新新闻
{
  "name": "web_search",
  "arguments": {
    "query": "科技新闻 今日头条",
    "max_results": 8
  }
}
```

### 场景4: 问题解决

```json
// 搜索解决方案
{
  "name": "web_search",
  "arguments": {
    "query": "Python ImportError 解决方法",
    "max_results": 6
  }
}
```

## 响应格式示例

### web_search 响应

```
搜索查询: Python编程教程

1. **Python官方教程**
   URL: https://docs.python.org/3/tutorial/
   摘要: Python官方提供的完整编程教程，适合初学者
   类型: web_result

2. **菜鸟教程 - Python基础**
   URL: https://www.runoob.com/python/python-tutorial.html
   摘要: 详细的Python基础教程，包含大量实例
   类型: web_result

3. **廖雪峰Python教程**
   URL: https://www.liaoxuefeng.com/wiki/1016959663602400
   摘要: 深入浅出的Python教程，适合进阶学习
   类型: web_result
```

### get_webpage_content 响应

```
网页URL: https://www.python.org

内容:
Python is a programming language that lets you work quickly and integrate systems more effectively. Python is powerful... and fast; plays well with others; runs everywhere; is friendly & easy to learn; is Open. These are some of the reasons people who use Python would rather not use anything else...
```

## 错误处理示例

### 空查询错误

```json
// 请求
{
  "name": "web_search",
  "arguments": {
    "query": ""
  }
}

// 响应
"错误：搜索查询不能为空"
```

### 无效URL错误

```json
// 请求
{
  "name": "get_webpage_content",
  "arguments": {
    "url": ""
  }
}

// 响应
"错误：URL不能为空"
```

### 网络错误

```json
// 请求
{
  "name": "get_webpage_content",
  "arguments": {
    "url": "https://invalid-url-that-does-not-exist.com"
  }
}

// 响应
"无法获取网页内容或网页为空"
```

## 性能优化建议

### 1. 合理设置max_results

```json
// 推荐：根据需要设置合适的结果数量
{
  "name": "web_search",
  "arguments": {
    "query": "搜索查询",
    "max_results": 5  // 通常5-10个结果就足够
  }
}
```

### 2. 避免频繁请求

```python
# 在应用中实现缓存机制
import time

last_request_time = {}
MIN_INTERVAL = 1  # 最小请求间隔（秒）

def should_allow_request(query):
    now = time.time()
    if query in last_request_time:
        if now - last_request_time[query] < MIN_INTERVAL:
            return False
    last_request_time[query] = now
    return True
```

### 3. 使用具体的搜索词

```json
// 好的搜索查询
{
  "query": "Python Flask Web开发教程 2024"
}

// 避免过于宽泛的查询
{
  "query": "编程"  // 太宽泛，结果可能不够精确
}
```

## 集成示例

### 与Claude Desktop集成

在Claude Desktop的配置文件中添加：

```json
{
  "mcpServers": {
    "web-search": {
      "command": "python3",
      "args": ["/root/mcp_dev/server.py"],
      "env": {
        "PYTHONPATH": "/root/mcp_dev"
      }
    }
  }
}
```

### 与其他MCP客户端集成

大多数MCP客户端都支持类似的配置格式，只需要指定正确的命令和参数即可。

## 故障排除

### 常见问题

1. **依赖安装失败**
   ```bash
   pip3 install --upgrade pip
   pip3 install -r requirements.txt
   ```

2. **网络连接问题**
   - 检查网络连接
   - 确认防火墙设置
   - 尝试使用代理（如果需要）

3. **编码问题**
   - 确保系统支持UTF-8编码
   - 检查Python环境的编码设置

### 调试模式

启用详细日志：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 扩展功能

### 添加新的搜索引擎

可以在`WebSearcher`类中添加新的搜索方法：

```python
async def search_bing(self, query: str, max_results: int = 10) -> list:
    # 实现Bing搜索
    pass

async def search_google(self, query: str, max_results: int = 10) -> list:
    # 实现Google搜索（需要API key）
    pass
```

### 添加内容过滤

```python
def filter_content(self, content: str) -> str:
    # 实现内容过滤逻辑
    # 例如：移除广告、过滤敏感内容等
    return filtered_content
```

这些示例应该能帮助你快速上手使用MCP Web Search Server！