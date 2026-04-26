"""
测试用例 for heventure-search-mcp
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 直接导入 server 模块
import importlib.util
spec = importlib.util.spec_from_file_location("server", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server.py"))
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)

WebSearcher = server.WebSearcher


class TestWebSearcher:
    """WebSearcher 测试类"""

    @pytest.fixture
    def searcher(self):
        """创建 WebSearcher 实例"""
        return WebSearcher()

    @pytest.mark.asyncio
    async def test_search_duckduckgo(self, searcher):
        """测试 DuckDuckGo 搜索"""
        # 使用 mock 模拟 API 响应
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'Answer': 'Test Answer',
            'AnswerURL': 'https://example.com',
            'RelatedTopics': [
                {'Text': 'Result 1 - https://example.com/1', 'FirstURL': 'https://example.com/1'},
                {'Text': 'Result 2 - https://example.com/2', 'FirstURL': 'https://example.com/2'},
            ]
        })

        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response), __aexit__=AsyncMock(return_value=None)))
        searcher.session = mock_session

        results = await searcher.search_duckduckgo("test query", max_results=5)
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_duckduckgo_empty(self, searcher):
        """测试 DuckDuckGo 空结果"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'Answer': '',
            'RelatedTopics': []
        })

        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response), __aexit__=AsyncMock(return_value=None)))
        searcher.session = mock_session

        results = await searcher.search_duckduckgo("test query")
        assert results == []

    @pytest.mark.asyncio
    async def test_search_duckduckgo_error(self, searcher):
        """测试 DuckDuckGo 搜索错误处理"""
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(side_effect=Exception("Network error"))
        searcher.session = mock_session

        results = await searcher.search_duckduckgo("test query")
        assert results == []

    @pytest.mark.asyncio
    async def test_search_html_duckduckgo(self, searcher):
        """测试 DuckDuckGo HTML 搜索"""
        html_content = """
        <html>
            <div class="result">
                <a class="result__a" href="https://example.com/1">Test Title 1</a>
                <a class="result__snippet">Test snippet 1</a>
            </div>
            <div class="result">
                <a class="result__a" href="https://example.com/2">Test Title 2</a>
                <a class="result__snippet">Test snippet 2</a>
            </div>
        </html>
        """

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=html_content)

        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response), __aexit__=AsyncMock(return_value=None)))
        searcher.session = mock_session

        results = await searcher.search_html_duckduckgo("test query", max_results=5)
        assert len(results) == 2
        assert results[0]['type'] == 'web_result'

    @pytest.mark.asyncio
    async def test_search_bing(self, searcher):
        """测试必应搜索"""
        html_content = """
        <html>
            <li class="b_algo">
                <h2><a href="https://example.com/1">Bing Result 1</a></h2>
                <p>Bing snippet 1</p>
            </li>
            <li class="b_algo">
                <h2><a href="https://example.com/2">Bing Result 2</a></h2>
                <p>Bing snippet 2</p>
            </li>
        </html>
        """

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=html_content)

        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response), __aexit__=AsyncMock(return_value=None)))
        searcher.session = mock_session

        results = await searcher.search_bing("test query", max_results=5)
        assert len(results) == 2
        assert results[0]['type'] == 'bing_result'

    @pytest.mark.asyncio
    async def test_get_page_content(self, searcher):
        """测试获取网页内容"""
        html_content = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <script>console.log('test');</script>
                <p>Main content here</p>
            </body>
        </html>
        """

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=html_content)

        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response), __aexit__=AsyncMock(return_value=None)))
        searcher.session = mock_session

        content = await searcher.get_page_content("https://example.com")
        assert "Main content here" in content
        assert "console.log" not in content  # 脚本应该被移除

    @pytest.mark.asyncio
    async def test_get_page_content_error(self, searcher):
        """测试获取网页内容错误处理"""
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(side_effect=Exception("Network error"))
        searcher.session = mock_session

        content = await searcher.get_page_content("https://example.com")
        assert content == ""


class TestWebSearcherIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_duckduckgo_live_search(self):
        """真实 DuckDuckGo API 测试（需要网络）"""
        async with WebSearcher() as searcher:
            results = await searcher.search_duckduckgo("Python programming", max_results=3)
            assert isinstance(results, list)
            # DuckDuckGo API 可能返回空结果，这是正常的
            print(f"Live search results: {len(results)}")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_bing_live_search(self):
        """真实必应搜索测试（需要网络）"""
        async with WebSearcher() as searcher:
            results = await searcher.search_bing("Python programming", max_results=3)
            assert isinstance(results, list)
            print(f"Bing results: {len(results)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
