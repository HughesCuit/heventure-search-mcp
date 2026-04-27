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
            trust_env=True  # 信任环境变量中的代理配置
        )
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

    async def search_google(self, query: str, max_results: int = 10) -> list:
        """使用Google搜索"""
        try:
            url = (
                f"https://www.google.com/search?q={quote_plus(query)}&num={max_results}"
            )

            async with self.session.get(
                url, allow_redirects=True, timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                if response.status == 200:
                    html = await response.text()

                    # 检测是否被阻止
                    if (
                        "unusual traffic" in html.lower()
                        or "captcha" in html.lower()
                        or "solve the challenge" in html.lower()
                    ):
                        logger.warning("Google返回了验证码或流量异常页面")
                        return []

                    soup = BeautifulSoup(html, "html.parser")
                    results = []

                    # Google搜索结果在 <div class="g"> 或 <div class="MjjYud"> 中
                    # 新版Google使用不同的结构
                    g_results = soup.find_all(
                        "div", class_=re.compile(r"^g$|^g和尚|^ZINbbc")
                    )

                    if not g_results:
                        # 尝试其他选择器
                        g_results = soup.find_all("div", class_="MjjYud")

                    if not g_results:
                        # 旧版结构
                        g_results = soup.find_all("div", class_="g")

                    for item in g_results[:max_results]:
                        # 查找标题和链接
                        title_elem = item.find("h3")
                        if not title_elem:
                            title_elem = item.find("div", class_="BNeawe")

                        if title_elem:
                            link_elem = (
                                title_elem.find("a")
                                if title_elem.name == "h3"
                                else title_elem.find("a")
                            )
                            if link_elem:
                                title = link_elem.get_text(strip=True)
                                url = link_elem.get("href", "")

                                # 跳过 Google 内部链接
                                if not url.startswith("http") or "google.com" in url:
                                    continue
                            else:
                                continue
                        else:
                            continue

                        # 获取摘要
                        snippet = ""
                        snippet_elem = item.find(
                            "div", class_=re.compile(r"BNeawe|s|st")
                        )
                        if snippet_elem:
                            snippet = snippet_elem.get_text(strip=True)
                        if not snippet:
                            # 备用：找所有文本
                            text_parts = item.find_all("div")
                            for part in text_parts:
                                text = part.get_text(strip=True)
                                if text and len(text) > 20 and text != title:
                                    snippet = text
                                    break

                        snippet = re.sub(r"\s+", " ", snippet)[:200]

                        if url and title:
                            results.append(
                                {
                                    "title": title,
                                    "url": url,
                                    "snippet": snippet,
                                    "type": "google_result",
                                }
                            )

                    return results
        except Exception as e:
            logger.error(f"Google搜索错误: {e}")
            return []

    async def search_google_html(self, query: str, max_results: int = 10) -> list:
        """使用Google的HTML接口作为备用"""
        try:
            url = f"https://www.google.com/search?q={quote_plus(query)}&num={max_results}&hl=en-US"

            async with self.session.get(
                url, allow_redirects=True, timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")
                    results = []

                    # 查找所有包含URL的链接
                    for link in soup.find_all("a", href=True):
                        href = link.get("href", "")
                        # 只处理搜索结果链接
                        if href.startswith("/url?q="):
                            url = href[7:].split("&")[0]  # 提取实际URL
                            if "google.com" in url:
                                continue

                            # 获取链接文本作为标题
                            title = link.get_text(strip=True)
                            if not title or len(title) < 3:
                                # 尝试找子元素
                                span = link.find("span")
                                if span:
                                    title = span.get_text(strip=True)

                            if title and len(title) > 3 and url.startswith("http"):
                                results.append(
                                    {
                                        "title": title,
                                        "url": url,
                                        "snippet": "",
                                        "type": "google_html_result",
                                    }
                                )

                                if len(results) >= max_results:
                                    break

                    return results
        except Exception as e:
            logger.error(f"Google HTML备用搜索错误: {e}")
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
            description="搜索网页内容，支持DuckDuckGo和必应搜索引擎",
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
                        "enum": ["duckduckgo", "bing", "google", "both"],
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
            results = []

            if search_engine in ["duckduckgo", "both"]:
                # DuckDuckGo搜索
                ddg_results = await searcher.search_duckduckgo(query, max_results)
                if len(ddg_results) < max_results:
                    html_results = await searcher.search_html_duckduckgo(
                        query, max_results - len(ddg_results)
                    )
                    ddg_results.extend(html_results)
                results.extend(ddg_results)

            if search_engine in ["bing", "both"]:
                # 必应搜索
                bing_results = await searcher.search_bing(query, max_results)
                results.extend(bing_results)

            if search_engine in ["google", "both"]:
                # Google搜索
                google_results = await searcher.search_google(query, max_results)
                if len(google_results) < max_results:
                    html_results = await searcher.search_google_html(
                        query, max_results - len(google_results)
                    )
                    google_results.extend(html_results)
                results.extend(google_results)

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
                "google": "Google",
                "both": "DuckDuckGo + 必应 + Google",
            }

            response_text = (
                f"搜索查询: {query}\n搜索引擎: {search_engines_used[search_engine]}\n\n"
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
