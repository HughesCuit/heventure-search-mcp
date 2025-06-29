#!/usr/bin/env python3
"""
Setup script for MCP Web Search Server
"""

from setuptools import setup, find_packages
import os

# Read README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="heventure-search-mcp",
    version="1.0.0",
    author="HughesCuit",
    description="一个无需API key的网页搜索MCP服务器",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/HughesCuit/heventure-search-mcp",
    packages=find_packages(),
    py_modules=["server"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "heventure-search-mcp=server:main",
        ],
    },
    keywords="mcp search web duckduckgo api",
    project_urls={
        "Bug Reports": "https://github.com/HughesCuit/heventure-search-mcp/issues",
        "Source": "https://github.com/HughesCuit/heventure-search-mcp",
        "Documentation": "https://github.com/HughesCuit/heventure-search-mcp#readme",
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.json", "*.sh"],
    },
)