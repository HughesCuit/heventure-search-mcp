#!/usr/bin/env python3
"""
MCP Web Search Server 测试脚本
"""

import asyncio
import json
from server import WebSearcher

async def test_web_searcher():
    """测试WebSearcher类的功能"""
    print("开始测试 WebSearcher...")
    
    async with WebSearcher() as searcher:
        # 测试DuckDuckGo API搜索
        print("\n1. 测试DuckDuckGo API搜索...")
        results = await searcher.search_duckduckgo("Python编程", 3)
        print(f"API搜索结果数量: {len(results)}")
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['title'][:50]}...")
            print(f"     URL: {result['url']}")
            print(f"     类型: {result['type']}")
        
        # 测试DuckDuckGo HTML搜索
        print("\n2. 测试DuckDuckGo HTML搜索...")
        html_results = await searcher.search_html_duckduckgo("机器学习", 3)
        print(f"HTML搜索结果数量: {len(html_results)}")
        for i, result in enumerate(html_results, 1):
            print(f"  {i}. {result['title'][:50]}...")
            print(f"     URL: {result['url']}")
        
        # 测试网页内容获取
        print("\n3. 测试网页内容获取...")
        if html_results:
            test_url = html_results[0]['url']
            if test_url:
                print(f"获取网页内容: {test_url}")
                content = await searcher.get_page_content(test_url)
                print(f"内容长度: {len(content)} 字符")
                print(f"内容预览: {content[:200]}...")
            else:
                print("没有有效的URL进行测试")
        else:
            print("没有搜索结果进行测试")

async def test_mcp_tools():
    """测试MCP工具功能"""
    print("\n\n开始测试 MCP 工具...")
    
    # 导入MCP相关模块
    from server import handle_call_tool, handle_list_tools
    
    # 测试工具列表
    print("\n1. 测试工具列表...")
    tools = await handle_list_tools()
    print(f"可用工具数量: {len(tools)}")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description}")
    
    # 测试web_search工具
    print("\n2. 测试web_search工具...")
    search_args = {
        "query": "人工智能发展趋势",
        "max_results": 5
    }
    search_result = await handle_call_tool("web_search", search_args)
    print(f"搜索结果类型: {type(search_result)}")
    if search_result:
        print(f"搜索结果长度: {len(search_result[0].text)} 字符")
        print(f"搜索结果预览: {search_result[0].text[:300]}...")
    
    # 测试get_webpage_content工具
    print("\n3. 测试get_webpage_content工具...")
    content_args = {
        "url": "https://www.python.org"
    }
    content_result = await handle_call_tool("get_webpage_content", content_args)
    print(f"内容结果类型: {type(content_result)}")
    if content_result:
        print(f"内容结果长度: {len(content_result[0].text)} 字符")
        print(f"内容结果预览: {content_result[0].text[:300]}...")

def test_json_format():
    """测试JSON格式化"""
    print("\n\n开始测试 JSON 格式化...")
    
    # 测试搜索结果格式
    sample_results = [
        {
            'title': '测试标题1',
            'url': 'https://example1.com',
            'snippet': '这是一个测试摘要',
            'type': 'web_result'
        },
        {
            'title': '测试标题2',
            'url': 'https://example2.com',
            'snippet': '这是另一个测试摘要',
            'type': 'instant_answer'
        }
    ]
    
    # 格式化结果
    formatted_results = []
    for i, result in enumerate(sample_results, 1):
        formatted_results.append(
            f"{i}. **{result['title']}**\n"
            f"   URL: {result['url']}\n"
            f"   摘要: {result['snippet']}\n"
            f"   类型: {result['type']}\n"
        )
    
    response_text = "搜索查询: 测试查询\n\n" + "\n".join(formatted_results)
    print("格式化结果:")
    print(response_text)
    
    # 测试JSON序列化
    try:
        json_str = json.dumps(sample_results, ensure_ascii=False, indent=2)
        print("\nJSON序列化成功:")
        print(json_str)
    except Exception as e:
        print(f"JSON序列化失败: {e}")

async def main():
    """主测试函数"""
    print("=" * 60)
    print("MCP Web Search Server 测试")
    print("=" * 60)
    
    try:
        # 测试WebSearcher
        await test_web_searcher()
        
        # 测试MCP工具
        await test_mcp_tools()
        
        # 测试JSON格式化
        test_json_format()
        
        print("\n" + "=" * 60)
        print("所有测试完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())