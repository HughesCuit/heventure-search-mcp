#!/usr/bin/env python3
"""
MCP Web Search Server

一个无需API key的网页搜索MCP服务器，使用DuckDuckGo搜索引擎提供网页搜索功能。
"""

__version__ = "1.0.0"
__author__ = "HughesCuit"
__description__ = "一个无需API key的网页搜索MCP服务器"

# 导出主要组件
from .server import WebSearcher, main

__all__ = ["WebSearcher", "main", "__version__", "__author__", "__description__"]