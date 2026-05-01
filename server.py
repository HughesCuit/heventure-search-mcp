#!/usr/bin/env python3
"""
MCP Web Search Server
一个无需API key的网页搜索MCP服务
"""

import asyncio
import importlib.metadata
import logging
import json
import os
import re
from urllib.parse import quote_plus, urlencode

import aiohttp
from bs4 import BeautifulSoup

# Ensure brotli is available for aiohttp to handle br encoding
try:
    import brotli  # noqa: F401

    logging.getLogger("web-search-server").debug("brotli loaded successfully")
except ImportError:
    pass

from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.types import (
    TextContent,
    Tool,
)

try:
    __version__ = importlib.metadata.version("heventure-search-mcp")
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0"

# 配置日志
logger = logging.getLogger("web-search-server")

# API Keys 配置
SERPAPI_KEY = os.environ.get("SERPAPI_KEY")  # SerpAPI API Key (https://serpapi.com)
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")  # Tavily API Key (https://tavily.com)

# SSL 验证配置 (true=启用验证, false=禁用验证，用于开发环境)
SSL_VERIFY = os.environ.get("WEB_SEARCH_SSL_VERIFY", "true").lower() == "true"

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
        # 配置SSL验证
        # SSL_VERIFY=True 时启用验证，SSL_VERIFY=False 时禁用验证（用于开发环境）
        ssl_context = SSL_VERIFY  # ssl=False 禁用验证，True/ssl.SSLContext 启用验证

        # SOCKS 代理支持
        if SOCKS_PROXY and aiohttp_socks:
            connector = aiohttp_socks.ProxyConnector.from_url(
                SOCKS_PROXY, ssl=ssl_context
            )
            logger.info(f"SOCKS connector created: {SOCKS_PROXY}")
        else:
            connector = aiohttp.TCPConnector(
                ssl=ssl_context,  # 根据 WEB_SEARCH_SSL_VERIFY 环境变量配置
                limit=10,
                force_close=False,
                enable_cleanup_closed=True,
            )

        self.session = aiohttp.ClientSession(
            headers=self.headers,
            connector=connector,
            trust_env=True,  # 信任环境变量中的代理配置
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def _safe_get(
        self, url: str, max_redirects: int = 5, **kwargs
    ) -> aiohttp.ClientResponse | None:
        """安全地发送HTTP GET请求，手动跟随重定向以避免无限循环

        aiohttp 的默认重定向处理在某些站点（如 Bing）上会导致 TooManyRedirects 异常。
        此方法手动跟随重定向，限制重定向次数，并支持相对URL解析。

        修复: 增加了 mkt 参数剥离逻辑，防止 Bing 的 mkt 参数导致的重定向循环
        (bing.com ↔ cn.bing.com 通过 mkt=zh-CN 参数形成无限循环)
        """
        from urllib.parse import parse_qs, urlencode, urlparse

        current_url = url
        redirect_count = 0
        redirect_history = []  # 记录访问过的 URL 用于检测循环

        while redirect_count < max_redirects:
            try:
                async with self.session.get(
                    current_url, allow_redirects=False, **kwargs
                ) as response:
                    # 如果是重定向（301, 302, 303, 307, 308）
                    if response.status in (301, 302, 303, 307, 308):
                        location = response.headers.get("Location", "")
                        if not location:
                            return response

                        # 解析相对URL
                        if location.startswith("/"):
                            parsed = urlparse(current_url)
                            location = f"{parsed.scheme}://{parsed.netloc}{location}"

                        # 剥离 mkt 参数以防止 Bing 重定向循环
                        parsed = urlparse(location)
                        qs = parse_qs(parsed.query)
                        if "mkt" in qs:
                            del qs["mkt"]

                        # 规范化 Bing 域名：将 bing.com 和 cn.bing.com 统一为 www.bing.com
                        # 这样可以打破两者之间的重定向循环
                        netloc = parsed.netloc
                        if netloc in ("bing.com", "cn.bing.com"):
                            netloc = "www.bing.com"
                        elif netloc.startswith("www.") and "bing" in netloc:
                            netloc = "www.bing.com"

                        new_query = urlencode(qs, doseq=True)
                        location = f"{parsed.scheme}://{netloc}{parsed.path}?{new_query}".rstrip(
                            "?"
                        )

                        # 通用循环检测：检查 URL 是否已在历史中
                        if current_url in [h[0] for h in redirect_history]:
                            logger.warning(f"检测到重定向循环，URL: {current_url}")
                            return None
                        redirect_history.append((current_url, response.status))
                        redirect_count += 1
                        current_url = location
                        logger.debug(f"Redirect {redirect_count}: {current_url}")
                        continue
                    # 非重定向响应，返回响应对象供调用者读取
                    return response
            except Exception as e:
                logger.error(f"请求失败 {current_url}: {e}")
                return None

        # 超过最大重定向次数
        logger.warning(f"超过最大重定向次数 ({max_redirects})，URL: {url}")
        return None

    async def search_duckduckgo(self, query: str, max_results: int = 10) -> list:
        """使用DuckDuckGo进行搜索"""
        try:
            # DuckDuckGo即时答案API
            url = f"https://api.duckduckgo.com/?q={quote_plus(query)}&format=json&no_html=1&skip_disambig=1"

            async with self.session.get(
                url, timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status in (200, 202):
                    # 尝试获取文本，手动解析JSON
                    text = await response.text()
                    try:
                        data = json.loads(text)
                    except json.JSONDecodeError:
                        # 尝试从JavaScript中提取JSON对象
                        match = re.search(r"\{.+\}", text, re.DOTALL)
                        if match:
                            try:
                                data = json.loads(match.group(0))
                            except json.JSONDecodeError:
                                logger.warning(
                                    "DuckDuckGo API返回非JSON响应，尝试备用方法"
                                )
                                return await self.search_html_duckduckgo(
                                    query, max_results
                                )
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
                else:
                    logger.warning(
                        f"DuckDuckGo API 返回非预期状态码: {response.status}"
                    )
                    return await self.search_html_duckduckgo(query, max_results)
        except Exception as e:
            logger.error(f"DuckDuckGo搜索错误: {e}")
            return []

    async def search_html_duckduckgo(self, query: str, max_results: int = 10) -> list:
        """通过HTML页面搜索DuckDuckGo"""
        try:
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"

            async with self.session.get(
                url, timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
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
                else:
                    logger.warning(
                        f"DuckDuckGo HTML 返回非预期状态码: {response.status}"
                    )
                    return []
        except Exception as e:
            logger.error(f"DuckDuckGo HTML搜索错误: {e}")
            return []

    async def search_bing(self, query: str, max_results: int = 10) -> list:
        """使用必应搜索

        修复: 使用手动重定向处理避免 aiohttp TooManyRedirects 异常 (Bing 的重定向循环问题)
        注意: 不在 URL 中使用 mkt 参数，因为 Bing 会通过 mkt=zh-CN 在 bing.com 和 cn.bing.com
        之间形成无限重定向循环 (_safe_get 会自动剥离该参数)
        """
        try:
            # 不使用 mkt 参数，避免 Bing 重定向循环问题
            url = (
                f"https://www.bing.com/search?q={quote_plus(query)}&count={max_results}"
            )

            response = await self._safe_get(
                url, max_redirects=5, timeout=aiohttp.ClientTimeout(total=10)
            )
            if response is None or response.status != 200:
                logger.warning(
                    f"必应搜索失败: {response.status if response else 'None'}"
                )
                # 尝试 cn.bing.com 作为备用
                cn_url = f"https://cn.bing.com/search?q={quote_plus(query)}&count={max_results}"
                response = await self._safe_get(
                    cn_url, max_redirects=5, timeout=aiohttp.ClientTimeout(total=10)
                )

            if response is None:
                return []

            # 只有在状态码为 200 时才读取响应体
            if response.status != 200:
                logger.warning(f"必应返回非200状态码: {response.status}")
                return []

            html = await response.text()

            # 检测是否被阻止（CAPTCHA挑战等）
            if (
                "challenge" in html.lower()
                or "solve the challenge" in html.lower()
                or "captcha" in html.lower()
            ):
                logger.warning("Bing返回了验证码挑战页面，无法获取搜索结果")
                return []

            soup = BeautifulSoup(html, "html.parser")
            results = []

            # Bing 的 HTML 结构可能因地区/时间而变化
            # 尝试多种选择器以兼容不同版本
            result_items = []

            # 新版 Bing: 查找 id="b_results" → li 元素
            ol = soup.find("ol", id="b_results")
            if ol:
                result_items = ol.find_all("li", recursive=False)

            # 备用: class b_algo
            if not result_items:
                result_items = soup.find_all("li", class_="b_algo")

            # 备用: 任何包含 h2 和 a 标签的 li
            if not result_items:
                for li in soup.find_all("li"):
                    if li.find("h2") and li.find("h2").find("a"):
                        result_items.append(li)
                        if len(result_items) >= max_results * 2:
                            break

            # 备用: 提取所有看起来像搜索结果的 h2 > a 组合
            if not result_items:
                for h2 in soup.find_all("h2"):
                    link = h2.find("a")
                    if link and link.get("href", "").startswith("https://"):
                        # 使用假的结构
                        result_items.append(h2.parent if h2.parent.name == "li" else h2)
                        if len(result_items) >= max_results * 2:
                            break

            for item in result_items[:max_results]:
                # 获取标题和链接
                title_elem = item.find("h2")
                if not title_elem:
                    title_elem = item.find("a", class_=re.compile(r"title"))

                title = ""
                url = ""

                if title_elem:
                    link_elem = (
                        title_elem.find("a") if title_elem.name == "h2" else title_elem
                    )
                    if link_elem and link_elem.name == "a":
                        title = link_elem.get_text(strip=True)
                        url = link_elem.get("href", "")
                else:
                    # 备用：直接找第一个链接
                    link_elem = item.find("a", href=True)
                    if link_elem:
                        title = link_elem.get_text(strip=True)
                        url = link_elem.get("href", "")

                if not url or not title:
                    continue

                # 获取摘要
                snippet = ""
                p_elem = item.find("p")
                if p_elem:
                    snippet = p_elem.get_text(strip=True)
                if not snippet:
                    for p in soup.find_all("p"):
                        p_text = p.get_text(strip=True)
                        if len(p_text) > 20 and p_text not in title:
                            snippet = p_text
                            break
                if not snippet:
                    caption = item.find("div", class_=re.compile(r"caption"))
                    if caption:
                        snippet = caption.get_text(strip=True)
                if not snippet:
                    item_text = item.get_text(separator=" ", strip=True)
                    if len(item_text) > len(title):
                        snippet = item_text[len(title) :].strip()[:200]

                snippet = re.sub(r"\s+", " ", snippet)

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

    async def search_google(self, query: str, max_results: int = 10) -> list:
        """使用 Google 搜索（通过HTML页面解析）

        注意: Google 可能会返回验证码或拒绝非浏览器请求，
        特别是在非桌面环境中。此方法为尽力而为，不保证始终可用。
        建议使用 DuckDuckGo 作为默认搜索引擎。
        """
        try:
            params = urlencode(
                {
                    "q": query,
                    "num": min(max_results, 10),
                    "hl": "en",
                }
            )
            google_headers = {
                **self.headers,
                "Accept-Language": "en-US,en;q=0.9",
            }

            # 按优先级尝试不同域名
            urls_to_try = [
                f"https://www.google.com/search?{params}",
                f"https://www.google.com.hk/search?{params}",
                f"https://www.google.co.jp/search?{params}",
            ]

            for url in urls_to_try:
                try:
                    # 使用 _safe_get 避免重定向问题
                    response = await self._safe_get(
                        url,
                        max_redirects=3,
                        headers=google_headers,
                        timeout=aiohttp.ClientTimeout(total=10),
                    )
                    if response is None or response.status != 200:
                        continue

                    html = await response.text()

                    # 检测阻止
                    if not html or len(html) < 500:
                        logger.warning("Google 返回了空白或过短的页面，跳过")
                        continue
                    if "captcha" in html.lower():
                        logger.warning("Google 返回了验证码页面，跳过")
                        continue

                    soup = BeautifulSoup(html, "html.parser")
                    results = []

                    # Google 搜索结果在 div#search 或 div#main 中
                    search_div = (
                        soup.find("div", id="search")
                        or soup.find("div", id="main")
                        or soup
                    )

                    # 方法1: 从 h3 中提取（标准搜索结果）
                    for h3 in search_div.find_all("h3"):
                        link = h3.find_parent("a")
                        if not link:
                            link = h3.find("a")
                        if not link:
                            continue

                        href = link.get("href", "")
                        # 处理 Google 的 /url?q= 重定向链接
                        if href.startswith("/url?q="):
                            from urllib.parse import parse_qs, urlparse

                            parsed = urlparse(href)
                            qs = parse_qs(parsed.query)
                            href = qs.get("q", [href])[0]
                        elif href.startswith("/"):
                            href = "https://www.google.com" + href

                        if not href.startswith("http"):
                            continue

                        title = h3.get_text(strip=True)
                        if not title:
                            continue

                        # 查找摘要
                        snippet = ""
                        parent = link
                        for _ in range(5):
                            parent = parent.find_parent()
                            if parent is None:
                                break
                            for cls_pattern in [
                                r"st|aCOpRe",
                                r"VwiC3b",
                                r"lEBKPb",
                                r"BNeawe",
                            ]:
                                snippet_div = parent.find(
                                    "span", class_=re.compile(cls_pattern)
                                )
                                if snippet_div:
                                    snippet = snippet_div.get_text(strip=True)
                                    break
                            if snippet:
                                break

                        results.append(
                            {
                                "title": title,
                                "url": href,
                                "snippet": snippet[:300] if snippet else "",
                                "type": "google_result",
                            }
                        )

                        if len(results) >= max_results:
                            break

                    if results:
                        logger.info(f"Google 搜索返回 {len(results)} 条结果")
                        return results
                    else:
                        logger.info("Google 搜索返回 0 条结果")

                except (TimeoutError, aiohttp.ClientError) as e:
                    logger.warning(f"Google 搜索 URL ({url}) 失败: {e}")
                    continue

            return []

        except Exception as e:
            logger.error(f"Google 搜索错误: {e}")
            return []

    async def search_serpapi(self, query: str, max_results: int = 10) -> list:
        """使用 SerpAPI 搜索（需要 API Key）
        文档: https://serpapi.com/search-api
        免费额度: 每月 100 次
        """
        try:
            if not SERPAPI_KEY:
                logger.warning("SerpAPI Key 未配置")
                return []

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
                        results.append(
                            {
                                "title": item.get("title", ""),
                                "url": item.get("link", ""),
                                "snippet": item.get("snippet", ""),
                                "type": "serpapi_result",
                            }
                        )

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
                        results.append(
                            {
                                "title": item.get("title", ""),
                                "url": item.get("url", ""),
                                "snippet": item.get("content", ""),
                                "type": "tavily_result",
                            }
                        )

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
            response = await self._safe_get(
                url, max_redirects=3, timeout=aiohttp.ClientTimeout(total=10)
            )
            if response is None or response.status != 200:
                return ""

            html = await response.text()
            soup = BeautifulSoup(html, "html.parser")

            # 移除脚本和样式
            for script in soup(["script", "style"]):
                script.decompose()

            # 获取文本内容
            text = soup.get_text()

            # 清理文本
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
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
            description="搜索网页内容，支持 DuckDuckGo、Google、必应搜索引擎。可选配置 SerpAPI Key 或 Tavily API Key 提升搜索质量和质量和稳定性",
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
                        "description": "搜索引擎选择：duckduckgo / bing / google / both",
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
            # 并发执行多个搜索引擎搜索
            async def search_with_fallback(engine: str):
                """单个搜索引擎搜索，带备用方法"""
                if engine == "duckduckgo":
                    ddg_results = await searcher.search_duckduckgo(query, max_results)
                    if not ddg_results or len(ddg_results) < max_results:
                        html_results = await searcher.search_html_duckduckgo(
                            query, max_results - len(ddg_results or [])
                        )
                        if isinstance(ddg_results, list):
                            ddg_results.extend(html_results)
                        else:
                            ddg_results = html_results or []
                    return ddg_results
                elif engine == "bing":
                    return await searcher.search_bing(query, max_results)
                elif engine == "google":
                    return await searcher.search_google(query, max_results)
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
                "google": ["google"],
                "both": ["duckduckgo", "google", "bing"],
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

            # 如果选择 both，限制总结果数量
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
                "both": "DuckDuckGo + Google + 必应",
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
                server_version=__version__,
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
