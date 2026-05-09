"""
heventure-search-mcp
一个无需API key的网页搜索MCP服务
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("heventure-search-mcp")
except PackageNotFoundError:
    __version__ = "0.0.0"

__author__ = "HughesCuit"
__description__ = "一个无需API key的网页搜索MCP服务器"
