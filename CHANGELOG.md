# Changelog / 更新日志

All notable changes to this project will be documented in this file.

Format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

本文档记录了项目的所有重要变更。格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [Unreleased]

### Added
- 添加搜索方法和缓存操作的单元测试，覆盖 Google、SerpAPI、Tavily 和 _safe_get
- `both` 模式多引擎搜索结果 URL 去重，避免重复条目 (#20)
- 添加 `handle_list_tools` 和 `handle_call_tool` MCP 协议入口函数的单元测试，覆盖空查询、不同引擎、API Key 引擎自动附加、URL 去重、未知工具等场景 (#21)

#### English
- Added unit tests for search methods and cache operations, covering Google, SerpAPI, Tavily, and `_safe_get`
- URL deduplication in `both` mode for multi-engine search results, preventing duplicate entries (#20)
- Added unit tests for `handle_list_tools` and `handle_call_tool` MCP protocol entry points, covering empty queries, different engines, auto-attached API key engines, URL dedup, unknown tools, and more (#21)

### Fixed
- 从必装依赖中移除 lxml（server.py 从未使用 lxml 解析器，全部使用 html.parser），改为可选依赖 `lxml-parser` (#22)
- 将 aiohttp-socks 和 tavily 从必装依赖移至可选依赖 (`socks` / `tavily`)，降低安装负担 (#3)
- 修复 `web_search` 工具描述文字重复：「质量和质量和稳定性」→「质量和稳定性」(#19)
- 修复 `__version__` 与 `pyproject.toml` 版本不同步问题：使用 `importlib.metadata` 从包元数据动态读取版本，消除手动维护 (#15)
- 修复 `get_page_content` 未使用 `_safe_get` 导致的重定向未处理和 timeout 类型不一致问题 (#16)
- 为 `search_duckduckgo`、`search_html_duckduckgo` 和 `search_bing` 添加请求超时 (`timeout=aiohttp.ClientTimeout(total=10)`)，防止网络异常时 MCP 服务器长时间挂起 (#17)
- 删除 `search_duckduckgo` 方法中重复的 `import json` / `import re` 语句，统一为模块顶部导入 (#18)
- brotli 导入去重：删除 `__aenter__` 中的重复导入，统一为模块顶部导入，添加 debug 日志确认加载状态
- 在 `pyproject.toml` 中注册 `integration` pytest mark，消除 `PytestUnknownMarkWarning` 警告
- 修复 SSL_VERIFY 取反逻辑错误：`not SSL_VERIFY` 导致生产环境关闭 SSL 验证、开发环境反而开启，移除多余的 `not`
- 修复 `pyproject.toml` 中 `target-version` 误设为项目版本号 `"1.4.2"`，改为正确的 Python 版本 `"py312"`，恢复 ruff check 功能
- 修复 server.py 中的 ruff lint 问题：清理空白行空格（W293）、排序导入（I001）、替换 `asyncio.TimeoutError` 为 `TimeoutError`（UP041）
- 清理遗留的 setup.py 文件

#### English
- Removed `lxml` from required dependencies (server.py never uses the lxml parser; all parsing uses html.parser). Moved to optional dependency `lxml-parser` (#22)
- Moved `aiohttp-socks` and `tavily` from required to optional dependencies (`socks` / `tavily`), reducing install burden (#3)
- Fixed duplicate text in `web_search` tool description: "质量和质量和稳定性" → "质量和稳定性" (#19)
- Fixed `__version__` out of sync with `pyproject.toml` version: now uses `importlib.metadata` to dynamically read version from package metadata, eliminating manual maintenance (#15)
- Fixed `get_webpage_content` not using `_safe_get`, causing unhandled redirects and inconsistent timeout type (#16)
- Added request timeouts to `search_duckduckgo`, `search_html_duckduckgo`, and `search_bing` (`timeout=aiohttp.ClientTimeout(total=10)`) to prevent long hangs during network anomalies (#17)
- Removed duplicate `import json` / `import re` statements in `search_duckduckgo` method, unified to module-level imports (#18)
- Deduplicated brotli import: removed duplicate import in `__aenter__`, unified to module-level import, added debug log to confirm loading state
- Registered `integration` pytest mark in `pyproject.toml` to eliminate `PytestUnknownMarkWarning`
- Fixed inverted SSL_VERIFY logic: `not SSL_VERIFY` disabled SSL verification in production and enabled it in dev — removed the erroneous `not`
- Fixed `target-version` in `pyproject.toml` erroneously set to project version `"1.4.2"`, corrected to Python version `"py312"`, restoring ruff check functionality
- Fixed ruff lint issues in server.py: trailing whitespace (W293), import sorting (I001), replaced `asyncio.TimeoutError` with `TimeoutError` (UP041)
- Cleaned up legacy `setup.py` file

---

## [1.4.12] - 2026-05-04
<!-- Auto-released -->
## [1.4.11] - 2026-05-03
## [1.4.10] - 2026-05-02
## [1.4.9] - 2026-05-01
## [1.4.8] - 2026-04-30
## [1.4.7] - 2026-04-30
## [1.4.6] - 2026-04-30
## [1.4.5] - 2026-04-29
## [1.4.4] - 2026-04-29
## [1.4.3] - 2026-04-29
## [1.4.2] - 2026-04-29
## [1.4.1] - 2026-04-29

---

## [1.4.0] - 2026-04-27

### Added
- 🆕 **Google Search Engine Support**: New Google search engine, accessible via `search_engine="google"`
- 🔧 **Fixed Bing Infinite Redirect Loop**: New `_safe_get` method to manually handle redirects, solving Bing's aiohttp TooManyRedirects issue

### Improved
- 🔄 **Multi-Engine Expansion**: "both" config now includes DuckDuckGo + Google + Bing
- 🛡️ **Redirect Safety Protection**: New manual redirect handler to prevent infinite loops
- 📝 Updated tool descriptions to reflect Google search engine support
- 🎯 Optimized search result extraction logic to support multiple HTML structures

#### 中文
### 新增
- 🆕 **Google 搜索引擎支持**: 新增 Google 搜索引擎，可通过 `search_engine="google"` 使用
- 🔧 **修复 Bing 无限重定向循环**: 新增 `_safe_get` 方法手动处理重定向，解决 Bing 的 aiohttp TooManyRedirects 问题

### 改进
- 🔄 **多引擎扩展**: "both" 配置现在包含 DuckDuckGo + Google + 必应三个引擎
- 🛡️ **重定向安全保护**: 新增手动重定向下发方法，避免搜索时的无限循环
- 📝 更新工具描述，反映 Google 搜索引擎支持
- 🎯 优化搜索结果提取逻辑，支持多种 HTML 结构

---

## [1.3.0] - 2026-04-27

### Added
- 🆕 **Tavily API Support**: New Tavily search engine (requires API key, 1000 searches/month free)
- 🔧 **SerpAPI Enhancement**: Restored SerpAPI search support with improved error handling
- ⚡ **Multi-Engine Concurrency**: Using `asyncio.gather` to execute multi-engine searches in parallel
- 🔄 **Non-API Engine Refactor**: Removed Google, kept DuckDuckGo + Bing as the free API-less option

### Improved
- 📝 Updated tool descriptions to reflect SerpAPI/Tavily optional API engines
- 🔧 Fixed `target-version` in `pyproject.toml` from `"1.2.4"` to `"py310"`, restoring ruff check
- 🧹 Auto-fixed 18 code style issues (W293 trailing whitespace)
- 📋 Updated CHANGELOG for v1.3.0 complete changes
- 🐍 Raised minimum Python version to 3.10

#### 中文
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

---

## [1.1.0] - 2024-01-XX

### Added
- 🔍 **Bing Search Support**: New Bing search engine providing richer results
- ⚡ **Multi-Engine Selection**: Choose DuckDuckGo, Bing, or both
- 🎯 **Flexible Search Strategy**: New `search_engine` parameter: `"duckduckgo"`, `"bing"`, or `"both"`
- 📊 **Result Source Identification**: Search results now indicate source engine
- 🔧 **Optimized Search Logic**: Improved result merging and deduplication

### Improved
- 📝 Updated tool descriptions for multi-engine support
- 📚 Enhanced README with Bing search documentation
- 🏷️ Updated project keywords with "bing" tag
- 🎨 Optimized search result display format

### Technical
- 🛠️ Refactored `web_search` tool handling logic
- 🔄 Optimized search engine invocation strategy
- 📈 Improved search result quality and diversity

---

## [1.0.0] - 2024-01-XX

### Added
- 🔍 **Web Search**: DuckDuckGo web search, no API key required
- 📄 **Web Content Fetching**: Get webpage content and convert to Markdown
- 🌐 **Chinese Search Support**: Optimized Chinese search experience
- 🛡️ **Smart Content Filtering**: Automatic ad and irrelevant content filtering
- ⚡ **Async Processing**: High-performance async HTTP requests
- 🔧 **Flexible Configuration**: User agent, timeout, and other parameter settings
- 📊 **Complete Test Suite**: Unit tests and benchmarks included
- 📚 **Detailed Documentation**: Full usage and deployment guides

### Technical Features
- Built on MCP (Model Context Protocol) protocol
- Async HTTP via aiohttp
- HTML parsing with BeautifulSoup4
- Multiple installation methods (uvx, pip, manual)
- Robust error handling and logging

### Tools
- `web_search`: Web search tool
- `get_webpage_content`: Web content fetching tool

---

## Contributing / 贡献指南

We welcome Issues and Pull Requests!

欢迎提交 Issue 和 Pull Request 来改进这个项目！
