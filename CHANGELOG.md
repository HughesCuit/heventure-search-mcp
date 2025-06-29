# 更新日志

本文档记录了项目的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [未发布]

### 计划中
- 更多搜索引擎支持
- 搜索结果缓存功能
- 高级搜索过滤器

## [1.1.0] - 2024-01-XX

### 新增
- 🔍 **必应搜索支持**: 新增必应搜索引擎，提供更丰富的搜索结果
- ⚡ **多引擎选择**: 支持选择DuckDuckGo、必应或同时使用两个搜索引擎
- 🎯 **灵活搜索策略**: 新增`search_engine`参数，可选择"duckduckgo"、"bing"或"both"
- 📊 **结果来源标识**: 搜索结果中标明来源搜索引擎
- 🔧 **优化搜索逻辑**: 改进搜索结果合并和去重机制

### 改进
- 📝 更新工具描述，反映多引擎支持
- 📚 完善README文档，添加必应搜索使用说明
- 🏷️ 更新项目关键词，包含"bing"标签
- 🎨 优化搜索结果显示格式

### 技术改进
- 🛠️ 重构`web_search`工具处理逻辑
- 🔄 优化搜索引擎调用策略
- 📈 提升搜索结果质量和多样性

## [1.0.0] - 2024-01-XX

### 新增
- 准备发布到PyPI
- 添加自动化发布脚本
- 完善包配置文件

## [1.0.0] - 2024-01-XX

### 新增
- 🔍 **网页搜索功能**: 使用DuckDuckGo进行网页搜索，无需API key
- 📄 **网页内容获取**: 获取指定URL的网页内容并转换为Markdown格式
- 🌐 **中文搜索支持**: 优化的中文搜索体验
- 🛡️ **智能内容过滤**: 自动过滤广告和无关内容
- ⚡ **异步处理**: 高性能的异步网络请求
- 🔧 **灵活配置**: 支持用户代理、超时等参数配置
- 📊 **完整测试套件**: 包含单元测试和基准测试
- 📚 **详细文档**: 完整的使用说明和部署指南

### 技术特性
- 基于MCP (Model Context Protocol) 协议
- 使用aiohttp进行异步HTTP请求
- BeautifulSoup4进行HTML解析
- 支持多种安装方式（uvx、pip、手动）
- 完善的错误处理和日志记录

### 工具
- `web_search`: 网页搜索工具
- `get_webpage_content`: 网页内容获取工具

### 文件结构
```
heventure-search-mcp/
├── server.py              # 主服务器文件
├── config.json            # 配置文件
├── requirements.txt       # 依赖列表
├── test_server.py         # 测试脚本
├── benchmark.py           # 基准测试
├── quick_benchmark.py     # 快速基准测试
├── benchmark_report.py    # 基准测试报告
├── README.md              # 项目说明
├── BENCHMARK.md           # 基准测试文档
├── DEPLOYMENT.md          # 部署指南
├── examples.md            # 使用示例
└── 脚本文件/
    ├── start_server.sh    # 服务器启动脚本
    └── run_benchmark.sh   # 基准测试脚本
```

### 配置选项
- `user_agent`: 自定义用户代理
- `timeout`: 请求超时时间
- `max_content_length`: 最大内容长度
- `max_results`: 最大搜索结果数

### 兼容性
- Python 3.8+
- 支持 Linux、macOS、Windows
- 无需外部API密钥

---

## 版本说明

- **主版本号**: 不兼容的API修改
- **次版本号**: 向下兼容的功能性新增
- **修订号**: 向下兼容的问题修正

## 贡献指南

如果您想为本项目做出贡献，请：

1. Fork 本仓库
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的修改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

请确保您的代码：
- 通过所有测试
- 遵循项目的代码风格
- 包含适当的文档
- 更新相关的CHANGELOG条目