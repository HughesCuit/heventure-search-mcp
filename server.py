#!/usr/bin/env python3
"""
MCP Web Search Server
一个无需API key的网页搜索MCP服务
"""

import asyncio
import json
import logging
from typing import Any, Sequence
from urllib.parse import quote_plus
import aiohttp
from bs4 import BeautifulSoup
import re

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)
from pydantic import AnyUrl

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("web-search-server")

server = Server("web-search-server")

class WebSearcher:
    """网页搜索器类"""
    
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
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
                if response.status == 200:
                    data = await response.json()
                    results = []
                    
                    # 处理即时答案
                    if data.get('Answer'):
                        results.append({
                            'title': 'DuckDuckGo即时答案',
                            'url': data.get('AnswerURL', ''),
                            'snippet': data.get('Answer', ''),
                            'type': 'instant_answer'
                        })
                    
                    # 处理相关主题
                    for topic in data.get('RelatedTopics', [])[:max_results-len(results)]:
                        if isinstance(topic, dict) and 'Text' in topic:
                            results.append({
                                'title': topic.get('Text', '').split(' - ')[0] if ' - ' in topic.get('Text', '') else topic.get('Text', ''),
                                'url': topic.get('FirstURL', ''),
                                'snippet': topic.get('Text', ''),
                                'type': 'related_topic'
                            })
                    
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
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    results = []
                    result_divs = soup.find_all('div', class_='result')
                    
                    for div in result_divs[:max_results]:
                        title_elem = div.find('a', class_='result__a')
                        snippet_elem = div.find('a', class_='result__snippet')
                        
                        if title_elem:
                            title = title_elem.get_text(strip=True)
                            url = title_elem.get('href', '')
                            snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''
                            
                            results.append({
                                'title': title,
                                'url': url,
                                'snippet': snippet,
                                'type': 'web_result'
                            })
                    
                    return results
        except Exception as e:
            logger.error(f"DuckDuckGo HTML搜索错误: {e}")
            return []
    
    async def search_bing(self, query: str, max_results: int = 10) -> list:
        """使用必应搜索"""
        try:
            # 必应搜索URL
            url = f"https://www.bing.com/search?q={quote_plus(query)}&count={max_results}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    results = []
                    
                    # 查找搜索结果
                    result_items = soup.find_all('li', class_='b_algo')
                    
                    for item in result_items[:max_results]:
                        # 获取标题和链接
                        title_elem = item.find('h2')
                        if title_elem:
                            link_elem = title_elem.find('a')
                            if link_elem:
                                title = link_elem.get_text(strip=True)
                                url = link_elem.get('href', '')
                                
                                # 获取摘要
                                snippet_elem = item.find('p') or item.find('div', class_='b_caption')
                                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''
                                
                                # 清理摘要中的多余空格
                                snippet = re.sub(r'\s+', ' ', snippet)
                                
                                results.append({
                                    'title': title,
                                    'url': url,
                                    'snippet': snippet,
                                    'type': 'bing_result'
                                })
                    
                    return results
        except Exception as e:
            logger.error(f"必应搜索错误: {e}")
            return []
    
    async def get_page_content(self, url: str) -> str:
        """获取网页内容"""
        try:
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # 移除脚本和样式
                    for script in soup(["script", "style"]):
                        script.decompose()
                    
                    # 获取文本内容
                    text = soup.get_text()
                    
                    # 清理文本
                    lines = (line.strip() for line in text.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    text = ' '.join(chunk for chunk in chunks if chunk)
                    
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
                    "query": {
                        "type": "string",
                        "description": "搜索查询字符串"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "最大结果数量",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 20
                    },
                    "search_engine": {
                        "type": "string",
                        "description": "搜索引擎选择",
                        "enum": ["duckduckgo", "bing", "both"],
                        "default": "both"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_webpage_content",
            description="获取指定网页的文本内容",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "要获取内容的网页URL"
                    }
                },
                "required": ["url"]
            }
        )
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
                    html_results = await searcher.search_html_duckduckgo(query, max_results - len(ddg_results))
                    ddg_results.extend(html_results)
                results.extend(ddg_results)
            
            if search_engine in ["bing", "both"]:
                # 必应搜索
                bing_results = await searcher.search_bing(query, max_results)
                results.extend(bing_results)
            
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
                "both": "DuckDuckGo + 必应"
            }
            
            response_text = f"搜索查询: {query}\n搜索引擎: {search_engines_used[search_engine]}\n\n" + "\n".join(formatted_results)
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