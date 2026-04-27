#!/usr/bin/env python3
"""
MCP Web Search Server
一个无需API key的网页搜索MCP服务
"""

import asyncio
import logging
import os
import re
from urllib.parse import quote_plus

import aiohttp
from bs4 import BeautifulSoup

# Ensure brotli is available for aiohttp to handle br encoding
try:
    import brotli
except ImportError:
    pass

from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.types import (
    TextContent,
    Tool,
)

# 配置日志
logger = logging.getLogger("web-search-server")

# API Keys 配置
SERPAPI_KEY = os.environ.get("SERPAPI_KEY")  # SerpAPI API Key (https://serpapi.com)
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")  # Tavily API Key (https://tavily.com)

# SOCKS 代理支持
SOCKS_PROXY = os.environ.get("SOCKS_PROXY") or os.environ.get("socks_proxy")
aiohttp_socks = None
if SOCKS_PROXY:
    try:
        import aiohttp_socks
        logger.info(f"SOCKS proxy enabled: {SOCKS_PROXY}")
    except ImportError:
        logger.warning("aiohttp-socks not installed, SOCKS proxy unavailable")

server = Server("web-search-server")


class WebSearcher:
    """网页搜索器类"""

    # 类级别的缓存（搜索结果缓存）
    _search_cache: dict = {}
    _cache_max_size: int = 100

    # 更好的 headers 来避免被网站阻止
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",  # 不请求 brotli，避免解码问题
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }

    def __init__(self):
        self.session = None
        self.headers = self.DEFAULT_HEADERS.copy()

    @staticmethod
    def _get_cache_key(query: str, engine: str, max_results: int) -> str:
        """生成缓存键"""
        return f"{engine}:{query}:{max_results}"

    @staticmethod
    def _get_from_cache(key: str) -> list | None:
        """从缓存获取结果"""
        return WebSearcher._search_cache.get(key)

    @staticmethod
    def _set_to_cache(key: str, results: list) -> None:
        """设置缓存结果"""
        # 简单LRU：超过最大 size 时清除最早的一半
        if len(WebSearcher._search_cache) >= WebSearcher._cache_max_size:
            # 清除一半缓存
            keys_to_remove = list(WebSearcher._search_cache.keys())[
                : WebSearcher._cache_max_size // 2
            ]
            for k in keys_to_remove:
                del WebSearcher._search_cache[k]
        WebSearcher._search_cache[key] = results

    @staticmethod
    def clear_cache() -> None:
        """清空搜索缓存"""
        WebSearcher._search_cache.clear()

    async def __aenter__(self):
        # 配置SSL以避免验证问题
        # 禁用SSL验证用于开发环境
        
        # SOCKS 代理支持
        if SOCKS_PROXY and aiohttp_socks:
            connector = aiohttp_socks.ProxyConnector.from_url(SOCKS_PROXY, ssl=False)
            logger.info(f"SOCKS connector created: {SOCKS_PROXY}")
        else:
            connector = aiohttp.TCPConnector(
                ssl=False,  # 开发环境禁用SSL验证
                limit=10,
                force_close=False,
                enable_cleanup_closed=True
            )
        
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            connector=connector,
            trust_env=True,  # 信任环境变量中的代理配置
        )
        # 确保 brotli 可用用于解码
        try:
            import brotli
        except ImportError:
            pass
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def search_duckduckgo(self, query: str, max_results: int = 10) -> list:
        """使用DuckDuckGo进行搜索"""
        try:
            # DuckDuckGo即时答案API
            url = f"https://api.duckduckgo.com/?q={quote_plus(query)}&format=json&no_html=1&skip_disambig=1"

            async with self.session.get(url) as response:
                if response.status in (200, 202):
                    # 尝试获取文本，手动解析JSON
                    text = await response.text()
                    try:
                        # 尝试解析JSON
                        import json
                        data = json.loads(text)
                    except json.JSONDecodeError:
                        # 有时API返回JavaScript格式，手动提取JSON
                        import json
                        import re
                        # 尝试从JavaScript中提取JSON对象
                        match = re.search(r'\{.+\}', text, re.DOTALL)
                        if match:
                            try:
                                data = json.loads(match.group(0))
                            except json.JSONDecodeError:
                                logger.warning("DuckDuckGo API返回非JSON响应，尝试备用方法")
                                return await self.search_html_duckduckgo(query, max_results)
                        else:
                            logger.warning("DuckDuckGo API返回非JSON响应，尝试备用方法")
                            return await self.search_html_duckduckgo(query, max_results)

                    results = []

                    # 处理即时答案 (Answer)
                    if data.get("Answer"):
                        results.append(
                            {
                                "title": "DuckDuckGo即时答案",
                                "url": data.get("AnswerURL", ""),
                                "snippet": data.get("Answer", ""),
                                "type": "instant_answer",
                            }
                        )

                    # 处理摘要 (Abstract)
                    if data.get("Abstract") and len(results) < max_results:
                        results.append(
                            {
                                "title": data.get("Heading", "DuckDuckGo摘要"),
                                "url": data.get("AbstractURL", ""),
                                "snippet": data.get("Abstract", ""),
                                "type": "abstract",
                            }
                        )

                    # 处理相关主题
                    for topic in data.get("RelatedTopics", [])[
                        : max_results - len(results)
                    ]:
                        if isinstance(topic, dict) and "Text" in topic:
                            results.append(
                                {
                                    "title": topic.get("Text", "").split(" - ")[0]
                                    if " - " in topic.get("Text", "")
                                    else topic.get("Text", ""),
                                    "url": topic.get("FirstURL", ""),
                                    "snippet": topic.get("Text", ""),
                                    "type": "related_topic",
                                }
                            )

                    # 如果没有返回任何结果，尝试HTML模式
                    if not results:
                        return await self.search_html_duckduckgo(query, max_results)

                    return results
        except Exception as e:
            logger.error(f"DuckDuckGo搜索错误: {e}")
            return []

    async def search_html_duckduckgo(self, query: str, max_results: int = 10) -> list:
        """通过HTML页面搜索DuckDuckGo"""
        try:
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"

            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")

                    results = []
                    result_divs = soup.find_all("div", class_="result")

                    for div in result_divs[:max_results]:
                        title_elem = div.find("a", class_="result__a")
                        snippet_elem = div.find("a", class_="result__snippet")

                        if title_elem:
                            title = title_elem.get_text(strip=True)
                            url = title_elem.get("href", "")
                            snippet = (
                                snippet_elem.get_text(strip=True)
                                if snippet_elem
                                else ""
                            )

                            results.append(
                                {
                                    "title": title,
                                    "url": url,
                                    "snippet": snippet,
                                    "type": "web_result",
                                }
                            )

                    return results
        except Exception as e:
            logger.error(f"DuckDuckGo HTML搜索错误: {e}")
            return []

    async def search_bing(self, query: str, max_results: int = 10) -> list:
        """使用必应搜索"""
        try:
            # 使用 cn.bing.com 避免被重定向导致无限循环
            url = (
                f"https://cn.bing.com/search?q={quote_plus(query)}&count={max_results}"
            )

            async with self.session.get(
                url, allow_redirects=True, timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                if response.status == 200:
                    html = await response.text()

                    # 检测是否被阻止（CAPTCHA挑战等）
                    if (
                        "challenge" in html.lower()
                        or "solve the challenge" in html.lower()
                    ):
                        logger.warning("Bing返回了验证码挑战页面，尝试备用方法")
                        return await self.search_bing_html(query, max_results)

                    soup = BeautifulSoup(html, "html.parser")
                    results = []

                    # 新版Bing使用不同的HTML结构
                    # 尝试多种选择器
                    result_items = soup.find_all("li", class_="b_algo")

                    if not result_items:
                        # 尝试查找包含搜索结果的容器
                        result_items = soup.find_all("li", class_=re.compile(r"b_"))

                    if not result_items:
                        # 尝试 ol#b_results
                        ol = soup.find("ol", id="b_results")
                        if ol:
                            result_items = ol.find_all("li")

                    for item in result_items[:max_results]:
                        # 获取标题和链接
                        title_elem = item.find("h2")
                        if not title_elem:
                            title_elem = item.find("a", class_=re.compile(r"title"))
                        if title_elem:
                            link_elem = (
                                title_elem.find("a")
                                if title_elem.name == "h2"
                                else title_elem
                            )
                            if link_elem and link_elem.name == "a":
                                title = link_elem.get_text(strip=True)
                                url = link_elem.get("href", "")
                            else:
                                continue
                        else:
                            # 备用：直接找第一个链接
                            link_elem = item.find("a", href=True)
                            if not link_elem:
                                continue
                            title = link_elem.get_text(strip=True)
                            url = link_elem.get("href", "")

                        # 获取摘要
                        snippet = ""
                        p_elem = item.find("p")
                        if p_elem:
                            snippet = p_elem.get_text(strip=True)
                        if not snippet:
                            caption = item.find("div", class_=re.compile(r"caption"))
                            if caption:
                                snippet = caption.get_text(strip=True)
                        if not snippet:
                            item_text = item.get_text(separator=" ", strip=True)
                            if len(item_text) > len(title):
                                snippet = item_text[len(title) :].strip()[:200]

                        snippet = re.sub(r"\s+", " ", snippet)

                        if url and title:
                            results.append(
                                {
                                    "title": title,
                                    "url": url,
                                    "snippet": snippet[:200] if snippet else "",
                                    "type": "bing_result",
                                }
                            )

                    return results
        except Exception as e:
            logger.error(f"必应搜索错误: {e}")
            return []

    async def search_bing_html(self, query: str, max_results: int = 10) -> list:
        """使用Bing的HTML接口作为备用"""
        try:
            # 使用 Bing 的 HTML 接口
            url = f"https://www.bing.com/search?q={quote_plus(query)}&count={max_results}&mkt=en-US"

            async with self.session.get(
                url, allow_redirects=True, timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")
                    results = []

                    # 查找搜索结果
                    for item in soup.find_all("h2"):
                        link = item.find("a")
                        if link and link.get("href", "").startswith("http"):
                            title = link.get_text(strip=True)
                            url = link.get("href", "")

                            # 找关联的摘要
                            snippet = ""
                            next_elem = item.find_next_sibling()
                            if next_elem:
                                p = next_elem.find("p")
                                if p:
                                    snippet = p.get_text(strip=True)

                            results.append(
                                {
                                    "title": title,
                                    "url": url,
                                    "snippet": snippet[:200] if snippet else "",
                                    "type": "bing_html_result",
                                }
                            )

                            if len(results) >= max_results:
                                break

                    return results
        except Exception as e:
            logger.error(f"Bing HTML备用搜索错误: {e}")
            return []

    # ==================== API Key 可选引擎 ====================
    
    async def search_serpapi(self, query: str, max_results: int = 10) -> list:
        """使用 SerpAPI 搜索（需要 API Key）
        文档: https://serpapi.com/search-api
        免费额度: 每月 100 次
        """
        try:
            if not SERPAPI_KEY:
                logger.warning("SerpAPI Key 未配置")
                return []
            
            import aiohttp
            
            url = "https://serpapi.com/search"
            params = {
                "q": query,
                "api_key": SERPAPI_KEY,
                "num": max_results,
                "engine": "google",
            }
            
            async with self.session.get(
                url, params=params, timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    results = []
                    
                    # 解析 SerpAPI 结果
                    organic_results = data.get("organic_results", [])
                    for item in organic_results[:max_results]:
                        results.append({
                            "title": item.get("title", ""),
                            "url": item.get("link", ""),
                            "snippet": item.get("snippet", ""),
                            "type": "serpapi_result",
                        })
                    
                    logger.info(f"SerpAPI 返回 {len(results)} 条结果")
                    return results
                elif response.status == 403:
                    logger.error("SerpAPI API Key 无效或配额用尽")
                    return []
                else:
                    logger.error(f"SerpAPI 请求失败: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"SerpAPI 搜索错误: {e}")
            return []

    async def search_tavily(self, query: str, max_results: int = 10) -> list:
        """使用 Tavily 搜索（需要 API Key）
        文档: https://docs.tavily.com/
        免费额度: 每月 1000 次
        """
        try:
            if not TAVILY_API_KEY:
                logger.warning("Tavily API Key 未配置")
                return []
            
            import aiohttp
            
            url = "https://api.tavily.com/search"
            payload = {
                "query": query,
                "api_key": TAVILY_API_KEY,
                "max_results": max_results,
                "include_answer": False,
                "include_raw_content": False,
                "include_images": False,
            }
            
            async with self.session.post(
                url, json=payload, timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    results = []
                    
                    # 解析 Tavily 结果
                    results_list = data.get("results", [])
                    for item in results_list:
                        results.append({
                            "title": item.get("title", ""),
                            "url": item.get("url", ""),
                            "snippet": item.get("content", ""),
                            "type": "tavily_result",
                        })
                    
                    logger.info(f"Tavily 返回 {len(results)} 条结果")
                    return results
                elif response.status == 401:
                    logger.error("Tavily API Key 无效")
                    return []
                else:
                    logger.error(f"Tavily 请求失败: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Tavily 搜索错误: {e}")
            return []

    async def get_page_content(self, url: str) -> str:
        """获取网页内容"""
        try:
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")

                    # 移除脚本和样式
                    for script in soup(["script", "style"]):
                        script.decompose()

                    # 获取文本内容
                    text = soup.get_text()

                    # 清理文本
                    lines = (line.strip() for line in text.splitlines())
                    chunks = (
                        phrase.strip() for line in lines for phrase in line.split("  ")
                    )
                    text = " ".join(chunk for chunk in chunks if chunk)

                    return text[:2000]  # 限制长度
        except Exception as e:
            logger.error(f"获取页面内容错误: {e}")
            return ""


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """列出可用工具"""
    return [
        Tool(
            name="web_search",
            description="搜索网页内容，支持 DuckDuckGo、必应搜索引擎。可选配置 SerpAPI Key 或 Tavily API Key 提升搜索质量",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索查询字符串"},
                    "max_results": {
                        "type": "integer",
                        "description": "最大结果数量",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 20,
                    },
                    "search_engine": {
                        "type": "string",
                        "description": "搜索引擎选择",
                        "enum": ["duckduckgo", "bing", "both"],
                        "default": "both",
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_webpage_content",
            description="获取指定网页的文本内容",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "要获取内容的网页URL"}
                },
                "required": ["url"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[TextContent]:
    """处理工具调用"""
    if arguments is None:
        arguments = {}

    if name == "web_search":
        query = arguments.get("query", "")
        max_results = arguments.get("max_results", 10)
        search_engine = arguments.get("search_engine", "both")

        if not query:
            return [TextContent(type="text", text="错误：搜索查询不能为空")]

        async with WebSearcher() as searcher:
            # 并发执行多个搜索引擎搜索
            async def search_with_fallback(engine: str):
                """单个搜索引擎搜索，带备用方法"""
                if engine == "duckduckgo":
                    ddg_results = await searcher.search_duckduckgo(query, max_results)
                    if len(ddg_results) < max_results:
                        html_results = await searcher.search_html_duckduckgo(
                            query, max_results - len(ddg_results)
                        )
                        ddg_results.extend(html_results)
                    return ddg_results
                elif engine == "bing":
                    return await searcher.search_bing(query, max_results)
                elif engine == "serpapi":
                    return await searcher.search_serpapi(query, max_results)
                elif engine == "tavily":
                    return await searcher.search_tavily(query, max_results)
                return []
            
            # 根据选择的搜索引擎构建任务列表
            # 优先级：免费引擎 -> API Key 增强引擎
            engines = {
                "duckduckgo": ["duckduckgo"],
                "bing": ["bing"],
                "both": ["duckduckgo", "bing"],
            }.get(search_engine, ["duckduckgo"])
            
            # 如果有 SerpAPI Key，添加 SerpAPI 搜索（优先级最高）
            if SERPAPI_KEY:
                engines.append("serpapi")
            
            # 如果有 Tavily API Key，添加 Tavily 搜索
            if TAVILY_API_KEY:
                engines.append("tavily")

            # 并发执行所有搜索
            tasks = [search_with_fallback(e) for e in engines]
            results_list = await asyncio.gather(*tasks)

            # 合并结果
            results = []
            for r in results_list:
                results.extend(r)

            # 如果选择both，限制总结果数量
            if search_engine == "both":
                results = results[:max_results]

            if not results:
                return [TextContent(type="text", text="未找到相关搜索结果")]

            # 格式化结果
            formatted_results = []
            for i, result in enumerate(results, 1):
                formatted_results.append(
                    f"{i}. **{result['title']}**\n"
                    f"   URL: {result['url']}\n"
                    f"   摘要: {result['snippet']}\n"
                    f"   类型: {result['type']}\n"
                )

            search_engines_used = {
                "duckduckgo": "DuckDuckGo",
                "bing": "必应",
                "both": "DuckDuckGo + 必应",
            }
            
            # 添加活跃的 API 引擎
            active_engines = []
            if SERPAPI_KEY:
                active_engines.append("SerpAPI")
            if TAVILY_API_KEY:
                active_engines.append("Tavily")
            
            engine_desc = search_engines_used.get(search_engine, "DuckDuckGo")
            if active_engines:
                engine_desc += " + " + " + ".join(active_engines)

            response_text = (
                f"搜索查询: {query}\n搜索引擎: {engine_desc}\n\n"
                + "\n".join(formatted_results)
            )
            return [TextContent(type="text", text=response_text)]

    elif name == "get_webpage_content":
        url = arguments.get("url", "")

        if not url:
            return [TextContent(type="text", text="错误：URL不能为空")]

        async with WebSearcher() as searcher:
            content = await searcher.get_page_content(url)

            if not content:
                return [TextContent(type="text", text="无法获取网页内容或网页为空")]

            response_text = f"网页URL: {url}\n\n内容:\n{content}"
            return [TextContent(type="text", text=response_text)]

    else:
        return [TextContent(type="text", text=f"未知工具: {name}")]


async def main():
    # 运行服务器使用stdio传输
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="web-search-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())


# Entry point for pip/uvx (must be sync function)
def entry_point():
    """Sync entry point for package console_scripts"""
    asyncio.run(main())
