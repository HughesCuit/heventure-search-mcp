# Changelog

## [Unreleased]

### Added
- 添加搜索方法和缓存操作的单元测试，覆盖 Google、SerpAPI、Tavily 和 _safe_get

### Fixed
- 修复 `__version__` 与 `pyproject.toml` 版本不同步问题：使用 `importlib.metadata` 从包元数据动态读取版本，消除手动维护 (#15)
- 修复 `get_page_content` 未使用 `_safe_get` 导致的重定向未处理和 timeout 类型不一致问题 (#16)
- brotli 导入去重：删除 `__aenter__` 中的重复导入，统一为模块顶部导入，添加 debug 日志确认加载状态
- 在 `pyproject.toml` 中注册 `integration` pytest mark，消除 `PytestUnknownMarkWarning` 警告
- 修复 SSL_VERIFY 取反逻辑错误：`not SSL_VERIFY` 导致生产环境关闭 SSL 验证、开发环境反而开启，移除多余的 `not`
- 修复 `pyproject.toml` 中 `target-version` 误设为项目版本号 `"1.4.2"`，改为正确的 Python 版本 `"py312"`，恢复 ruff check 功能
- 修复 server.py 中的 ruff lint 问题：清理空白行空格（W293）、排序导入（I001）、替换 `asyncio.TimeoutError` 为 `TimeoutError`（UP041）
- 清理遗留的 setup.py 文件

### 已完成
- ✅ **修复 server_version 与项目版本同步**: server.py 中的 server_version 现在使用 `__version__` 变量，与 pyproject.toml 保持一致 (1.4.0)
- Google 搜索引擎支持（已完成）
- 搜索结果去重与排序优化
- ✅ **SSL 验证配置化**: 新增 `WEB_SEARCH_SSL_VERIFY` 环境变量，支持生产环境启用 SSL 验证（默认 `true`）









## [1.4.7] - 2026-04-30

### Changed
- 自动发布版本 1.4.7
- 包含最新代码更新

## [1.4.6] - 2026-04-30

### Changed
- 自动发布版本 1.4.6
- 包含最新代码更新

## [1.4.5] - 2026-04-29

### Changed
- 自动发布版本 1.4.5
- 包含最新代码更新

## [1.4.4] - 2026-04-29

### Changed
- 自动发布版本 1.4.4
- 包含最新代码更新

## [1.4.3] - 2026-04-29

### Changed
- 自动发布版本 1.4.3
- 包含最新代码更新

## [1.4.2] - 2026-04-29

### Changed
- 自动发布版本 1.4.2
- 包含最新代码更新

## [1.4.1] - 2026-04-29

### Changed
- 自动发布版本 1.4.1
- 包含最新代码更新

## [1.4.0] - 2026-04-27

### Changed
- 自动发布版本 1.4.0
- 包含最新代码更新

## [1.4.0] - 2026-04-27

### 新增
- 🆕 **Google 搜索引擎支持**: 新增 Google 搜索引擎，可通过 `search_engine="google"` 使用
- 🔧 **修复 Bing 无限重定向循环**: 新增 `_safe_get` 方法手动处理重定向，解决 Bing 的 aiohttp TooManyRedirects 问题

### 改进
- 🔄 **多引擎扩展**: "both" 配置现在包含 DuckDuckGo + Google + 必应三个引擎
- 🛡️ **重定向安全保护**: 新增手动重定向下发方法，避免搜索时的无限循环
- 📝 更新工具描述，反映 Google 搜索引擎支持
- 🎯 优化搜索结果提取逻辑，支持多种 HTML 结构

## [1.3.0] - 2026-04-27

### 新增
- 🆕 **Tavily API 支持**: 新增 Tavily 搜索引擎（需 API Key，每月 1000 次免费）
- 🔧 **SerpAPI 增强**: 恢复 SerpAPI 搜索支持并优化错误处理
- ⚡ **多引擎并发**: 使用 asyncio.gather 同时执行多引擎搜索
- 🔄 **非 API 引擎重构**: 移除 Google，保留 DuckDuckGo + Bing 免 API 方案

### 改进
- 📝 更新工具描述，反映 SerpAPI/Tavily 可选 API 引擎
- 🔧 修复 pyproject.toml 中 ruff target-version 配置错误（"1.2.4" → "py310"）
- 🧹 自动修复 18 处代码风格问题（W293 空白行尾空格）
- 📋 更新 CHANGELOG 记录 v1.3.0 完整变更
- 🐍 提升最低 Python 版本要求到 3.10
## [1.2.4] - 2026-04-27

### Changed
- 自动发布版本 1.2.4
- 包含最新代码更新

## [1.2.3] - 2026-04-27

### Changed
- 自动发布版本 1.2.3
- 包含最新代码更新

## [1.2.2] - 2026-04-27

### Changed
- 自动发布版本 1.2.2
- 包含最新代码更新

## [1.2.1] - 2026-04-27

### Changed
- 自动发布版本 1.2.1
- 包含最新代码更新

## [1.2.0] - 2026-04-27

### Changed
- 自动发布版本 1.2.0
- 包含最新代码更新

## [1.1.3] - 2026-04-26

### Changed
- 自动发布版本 1.1.3
- 包含最新代码更新

## [1.1.2] - 2026-04-26

### Changed
- 自动发布版本 1.1.2
- 包含最新代码更新

## [1.1.1] - 2025-06-29

### Changed
- 自动发布版本 1.1.1
- 包含最新代码更新

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
## [Unreleased] - 2026-04-27

### 自动化改进
- 🆕 自动改进循环执行
- ✅ 日常维护，所有检查通过
