"""
测试用例 for heventure-search-mcp
"""

import os
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 直接导入 server 模块
import importlib.util

spec = importlib.util.spec_from_file_location(
    "server",
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server.py"
    ),
)
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)

WebSearcher = server.WebSearcher


class TestWebSearcher:
    """WebSearcher 测试类"""

    @pytest.fixture
    def searcher(self):
        """创建 WebSearcher 实例（每个测试清空缓存）"""
        WebSearcher.clear_cache()
        return WebSearcher()

    @pytest.mark.asyncio
    async def test_search_duckduckgo(self, searcher):
        """测试 DuckDuckGo 搜索"""
        # 使用 mock 模拟 API 响应 —— 代码用 response.text() + json.loads()
        import json as _json

        data = {
            "Answer": "Test Answer",
            "AnswerURL": "https://example.com",
            "RelatedTopics": [
                {
                    "Text": "Result 1 - https://example.com/1",
                    "FirstURL": "https://example.com/1",
                },
                {
                    "Text": "Result 2 - https://example.com/2",
                    "FirstURL": "https://example.com/2",
                },
            ],
        }

        async def async_text():
            return _json.dumps(data)

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = async_text

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_response)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_cm)
        searcher.session = mock_session

        results = await searcher.search_duckduckgo("test query", max_results=5)
        assert isinstance(results, list)
        assert len(results) >= 1  # 应该有 Answer + RelatedTopics

    @pytest.mark.asyncio
    async def test_search_duckduckgo_empty(self, searcher):
        """测试 DuckDuckGo 空结果"""
        import json as _json

        async def async_text():
            return _json.dumps({"Answer": "", "RelatedTopics": []})

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = async_text

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_response)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_cm)
        searcher.session = mock_session

        results = await searcher.search_duckduckgo("test query")
        assert results == []

    @pytest.mark.asyncio
    async def test_search_duckduckgo_error(self, searcher):
        """测试 DuckDuckGo 搜索错误处理"""
        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=Exception("Network error"))
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

        # 创建正确的 mock - text() 需要是 async 函数
        async def async_text():
            return html_content

        # 创建正确的异步上下文管理器 mock
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = async_text

        # 创建一个支持 async with 的 mock
        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_response)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_cm)
        searcher.session = mock_session

        results = await searcher.search_html_duckduckgo("test query", max_results=5)
        assert len(results) == 2
        assert results[0]["type"] == "web_result"

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

        # 创建正确的 mock - text() 需要是 async 函数
        async def async_text():
            return html_content

        # 创建正确的异步上下文管理器 mock
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = async_text

        # 创建一个支持 async with 的 mock
        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_response)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_cm)
        searcher.session = mock_session

        results = await searcher.search_bing("test query", max_results=5)
        assert len(results) == 2
        assert results[0]["type"] == "bing_result"

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

        # 创建正确的 mock - text() 需要是 async 函数
        async def async_text():
            return html_content

        # 创建正确的异步上下文管理器 mock
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = async_text

        # 创建一个支持 async with 的 mock
        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_response)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_cm)
        searcher.session = mock_session

        content = await searcher.get_page_content("https://example.com")
        assert "Main content here" in content
        assert "console.log" not in content  # 脚本应该被移除

    @pytest.mark.asyncio
    async def test_get_page_content_error(self, searcher):
        """测试获取网页内容错误处理"""
        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=Exception("Network error"))
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
            results = await searcher.search_duckduckgo(
                "Python programming", max_results=3
            )
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


class TestSearchGoogle:
    """Google 搜索测试"""

    @pytest.fixture
    def searcher(self):
        WebSearcher.clear_cache()
        return WebSearcher()

    @pytest.mark.asyncio
    async def test_search_google(self, searcher):
        """测试 Google 搜索返回正确结果"""
        google_html = (
            """
        <html>
            <body>
                <div id="search">
                    <a href="https://example.com/1"><h3>Result Title 1</h3></a>
                    <a href="https://example.com/2"><h3>Result Title 2</h3></a>
                    <a href="https://example.com/3"><h3>Result Title 3</h3></a>
                </div>
            </body>
        </html>
        """
            + "<!-- "
            + "x" * 600
            + " -->"
        )

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=google_html)
        searcher._safe_get = AsyncMock(return_value=mock_response)

        results = await searcher.search_google("test query", max_results=10)
        assert len(results) == 3
        for r in results:
            assert r["type"] == "google_result"
            assert "title" in r
            assert "url" in r
            assert "snippet" in r
            assert r["url"].startswith("http")
        assert results[0]["title"] == "Result Title 1"
        assert results[0]["url"] == "https://example.com/1"

    @pytest.mark.asyncio
    async def test_search_google_empty(self, searcher):
        """测试 Google 搜索返回空结果（无 h3 标签）"""
        empty_html = (
            "<html><body><div id='search'><p>No results here</p></div></body></html>"
            + "<!-- "
            + "x" * 600
            + " -->"
        )
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=empty_html)
        searcher._safe_get = AsyncMock(return_value=mock_response)

        results = await searcher.search_google("test query")
        assert results == []

    @pytest.mark.asyncio
    async def test_search_google_captcha(self, searcher):
        """测试 Google 返回验证码页面时返回空结果"""
        captcha_html = (
            "<html><body>Please solve the captcha to continue</body></html>"
            + "<!-- "
            + "x" * 600
            + " -->"
        )
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=captcha_html)
        searcher._safe_get = AsyncMock(return_value=mock_response)

        results = await searcher.search_google("test query")
        assert results == []

    @pytest.mark.asyncio
    async def test_search_google_error(self, searcher):
        """测试 Google 搜索异常处理"""
        searcher._safe_get = AsyncMock(side_effect=Exception("Network error"))

        results = await searcher.search_google("test query")
        assert results == []


class TestSafeGet:
    """_safe_get 测试类"""

    @pytest.fixture
    def searcher(self):
        WebSearcher.clear_cache()
        return WebSearcher()

    @pytest.mark.asyncio
    async def test_safe_get_normal_response(self, searcher):
        """测试正常 200 响应直接返回"""
        mock_response = AsyncMock()
        mock_response.status = 200

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_response)
        mock_cm.__aexit__ = AsyncMock(return_value=None)
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_cm)
        searcher.session = mock_session

        result = await searcher._safe_get("https://example.com")
        assert result == mock_response
        mock_session.get.assert_called_once_with(
            "https://example.com", allow_redirects=False
        )

    @pytest.mark.asyncio
    async def test_safe_get_redirect_follow(self, searcher):
        """测试 302 重定向被正确跟随"""
        redirect_response = AsyncMock()
        redirect_response.status = 302
        redirect_response.headers = {"Location": "https://example.com/final"}

        final_response = AsyncMock()
        final_response.status = 200

        call_count = 0

        def side_effect(url, **kwargs):
            nonlocal call_count
            call_count += 1
            cm = MagicMock()
            if call_count == 1:
                cm.__aenter__ = AsyncMock(return_value=redirect_response)
            else:
                cm.__aenter__ = AsyncMock(return_value=final_response)
            cm.__aexit__ = AsyncMock(return_value=None)
            return cm

        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=side_effect)
        searcher.session = mock_session

        result = await searcher._safe_get("https://example.com/start")
        assert result == final_response
        assert mock_session.get.call_count == 2

    @pytest.mark.asyncio
    async def test_safe_get_redirect_loop(self, searcher):
        """测试重定向循环检测"""
        resp_b = AsyncMock()
        resp_b.status = 302
        resp_b.headers = {"Location": "https://example.com/B"}

        call_count = 0

        def side_effect(url, **kwargs):
            nonlocal call_count
            call_count += 1
            cm = MagicMock()
            cm.__aenter__ = AsyncMock(return_value=resp_b)
            cm.__aexit__ = AsyncMock(return_value=None)
            return cm

        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=side_effect)
        searcher.session = mock_session

        result = await searcher._safe_get("https://example.com/A")
        assert result is None

    @pytest.mark.asyncio
    async def test_safe_get_max_redirects(self, searcher):
        """测试超过最大重定向次数返回 None"""
        resp = AsyncMock()
        resp.status = 302
        resp.headers = {"Location": "https://example.com/next"}

        call_count = 0

        def side_effect(url, **kwargs):
            nonlocal call_count
            call_count += 1
            cm = MagicMock()
            cm.__aenter__ = AsyncMock(return_value=resp)
            cm.__aexit__ = AsyncMock(return_value=None)
            return cm

        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=side_effect)
        searcher.session = mock_session

        result = await searcher._safe_get("https://example.com/start", max_redirects=3)
        assert result is None
        assert mock_session.get.call_count == 3

    @pytest.mark.asyncio
    async def test_safe_get_mkt_redirect_stripping(self, searcher):
        """测试重定向时 mkt 参数被正确剥离"""
        redirect_response = AsyncMock()
        redirect_response.status = 302
        redirect_response.headers = {
            "Location": "https://example.com/search?q=test&mkt=zh-CN"
        }

        final_response = AsyncMock()
        final_response.status = 200

        call_count = 0

        def side_effect(url, **kwargs):
            nonlocal call_count
            call_count += 1
            cm = MagicMock()
            if call_count == 1:
                cm.__aenter__ = AsyncMock(return_value=redirect_response)
            else:
                cm.__aenter__ = AsyncMock(return_value=final_response)
            cm.__aexit__ = AsyncMock(return_value=None)
            return cm

        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=side_effect)
        searcher.session = mock_session

        result = await searcher._safe_get("https://example.com/start")
        assert result == final_response
        # 验证第二次请求的 URL 中 mkt 参数被剥离
        second_call_url = mock_session.get.call_args_list[1][0][0]
        assert "mkt" not in second_call_url
        assert "q=test" in second_call_url


class TestCache:
    """缓存操作测试"""

    def setup_method(self):
        """每个测试前清空缓存"""
        WebSearcher.clear_cache()

    def test_cache_set_and_get(self):
        """测试缓存写入和读取"""
        key = "test_key"
        results = [{"title": "Test", "url": "https://example.com"}]
        WebSearcher._set_to_cache(key, results)
        assert WebSearcher._get_from_cache(key) == results

    def test_cache_miss(self):
        """测试缓存未命中返回 None"""
        assert WebSearcher._get_from_cache("nonexistent_key") is None

    def test_cache_clear(self):
        """测试清空缓存"""
        WebSearcher._set_to_cache("key1", [{"title": "A"}])
        WebSearcher._set_to_cache("key2", [{"title": "B"}])
        assert WebSearcher._get_from_cache("key1") is not None
        WebSearcher.clear_cache()
        assert WebSearcher._get_from_cache("key1") is None
        assert WebSearcher._get_from_cache("key2") is None

    def test_cache_lru_eviction(self):
        """测试缓存超过最大大小时触发淘汰"""
        for i in range(WebSearcher._cache_max_size):
            WebSearcher._set_to_cache(f"key_{i}", [{"title": f"Result {i}"}])
        assert len(WebSearcher._search_cache) == WebSearcher._cache_max_size

        # 写入第 101 个条目，触发淘汰（清除前 50 个）
        WebSearcher._set_to_cache("overflow_key", [{"title": "Overflow"}])
        assert len(WebSearcher._search_cache) < WebSearcher._cache_max_size + 1
        # overflow_key 应该存在
        assert WebSearcher._get_from_cache("overflow_key") is not None

    def test_cache_ttl_expiry(self):
        """测试缓存 TTL 过期后返回 None"""
        import time

        key = "ttl_test"
        results = [{"title": "TTL Test"}]
        WebSearcher._set_to_cache(key, results)
        assert WebSearcher._get_from_cache(key) == results

        # 手动修改时间戳使其过期
        results_stored, old_ts = WebSearcher._search_cache[key]
        WebSearcher._search_cache[key] = (results, old_ts - WebSearcher._cache_ttl_seconds - 1)

        # 应该返回 None 并清理过期条目
        assert WebSearcher._get_from_cache(key) is None
        assert key not in WebSearcher._search_cache

    def test_cache_key_generation(self):
        """测试缓存键生成"""
        key1 = WebSearcher._get_cache_key("test query", "google", 10)
        key2 = WebSearcher._get_cache_key("test query", "bing", 10)
        key3 = WebSearcher._get_cache_key("test query", "google", 5)
        assert key1 != key2  # 不同引擎
        assert key1 != key3  # 不同 max_results
        assert key1 == WebSearcher._get_cache_key("test query", "google", 10)

    @pytest.mark.asyncio
    async def test_cache_hit_skips_network(self):
        """测试缓存命中时不发起网络请求"""
        WebSearcher._set_to_cache(
            "duckduckgo:cached query:5",
            [{"title": "Cached", "url": "https://cached.com", "snippet": "", "type": "cached"}],
        )
        async with WebSearcher() as searcher:
            results = await searcher.search_duckduckgo("cached query", max_results=5)
            assert len(results) == 1
            assert results[0]["title"] == "Cached"


class TestSearchSerpAPI:
    """SerpAPI 搜索测试"""

    @pytest.fixture
    def searcher(self):
        WebSearcher.clear_cache()
        return WebSearcher()

    @pytest.mark.asyncio
    async def test_search_serpapi_no_key(self, searcher, monkeypatch):
        """测试 SerpAPI Key 未配置时返回空结果"""
        monkeypatch.setattr(server, "SERPAPI_KEY", None)
        results = await searcher.search_serpapi("test query")
        assert results == []

    @pytest.mark.asyncio
    async def test_search_serpapi(self, searcher, monkeypatch):
        """测试 SerpAPI 搜索结果解析"""
        monkeypatch.setattr(server, "SERPAPI_KEY", "test-api-key")
        api_response = {
            "organic_results": [
                {
                    "title": "SerpAPI Result 1",
                    "link": "https://example.com/1",
                    "snippet": "Snippet 1",
                },
                {
                    "title": "SerpAPI Result 2",
                    "link": "https://example.com/2",
                    "snippet": "Snippet 2",
                },
            ]
        }

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=api_response)

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_response)
        mock_cm.__aexit__ = AsyncMock(return_value=None)
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_cm)
        searcher.session = mock_session

        results = await searcher.search_serpapi("test query", max_results=10)
        assert len(results) == 2
        assert results[0]["title"] == "SerpAPI Result 1"
        assert results[0]["url"] == "https://example.com/1"
        assert results[0]["snippet"] == "Snippet 1"
        assert results[0]["type"] == "serpapi_result"
        assert results[1]["type"] == "serpapi_result"


class TestSearchTavily:
    """Tavily 搜索测试"""

    @pytest.fixture
    def searcher(self):
        WebSearcher.clear_cache()
        return WebSearcher()

    @pytest.mark.asyncio
    async def test_search_tavily_no_key(self, searcher, monkeypatch):
        """测试 Tavily API Key 未配置时返回空结果"""
        monkeypatch.setattr(server, "TAVILY_API_KEY", None)
        results = await searcher.search_tavily("test query")
        assert results == []

    @pytest.mark.asyncio
    async def test_search_tavily(self, searcher, monkeypatch):
        """测试 Tavily 搜索结果解析"""
        monkeypatch.setattr(server, "TAVILY_API_KEY", "test-api-key")
        api_response = {
            "results": [
                {
                    "title": "Tavily Result 1",
                    "url": "https://example.com/1",
                    "content": "Content 1",
                },
                {
                    "title": "Tavily Result 2",
                    "url": "https://example.com/2",
                    "content": "Content 2",
                },
            ]
        }

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=api_response)

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_response)
        mock_cm.__aexit__ = AsyncMock(return_value=None)
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_cm)
        searcher.session = mock_session

        results = await searcher.search_tavily("test query", max_results=10)
        assert len(results) == 2
        assert results[0]["title"] == "Tavily Result 1"
        assert results[0]["url"] == "https://example.com/1"
        assert results[0]["snippet"] == "Content 1"
        assert results[0]["type"] == "tavily_result"
        assert results[1]["type"] == "tavily_result"

    @pytest.mark.asyncio
    async def test_search_tavily_error(self, searcher, monkeypatch):
        """测试 Tavily 搜索异常处理"""
        monkeypatch.setattr(server, "TAVILY_API_KEY", "test-api-key")
        mock_session = MagicMock()
        mock_session.post = MagicMock(side_effect=Exception("Network error"))
        searcher.session = mock_session

        results = await searcher.search_tavily("test query")
        assert results == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


class TestHandleListTools:
    """Test handle_list_tools MCP dispatch"""

    @pytest.mark.asyncio
    async def test_list_tools_returns_two_tools(self):
        """Verify handle_list_tools returns web_search and get_webpage_content"""
        tools = await server.handle_list_tools()
        assert len(tools) == 2
        names = [t.name for t in tools]
        assert "web_search" in names
        assert "get_webpage_content" in names

    @pytest.mark.asyncio
    async def test_list_tools_web_search_schema(self):
        """Verify web_search tool has correct input schema"""
        tools = await server.handle_list_tools()
        ws = next(t for t in tools if t.name == "web_search")
        schema = ws.inputSchema
        assert schema["type"] == "object"
        assert "query" in schema["properties"]
        assert "query" in schema["required"]
        assert schema["properties"]["query"]["type"] == "string"

    @pytest.mark.asyncio
    async def test_list_tools_get_webpage_content_schema(self):
        """Verify get_webpage_content tool has correct input schema"""
        tools = await server.handle_list_tools()
        gpc = next(t for t in tools if t.name == "get_webpage_content")
        schema = gpc.inputSchema
        assert schema["type"] == "object"
        assert "url" in schema["properties"]
        assert "url" in schema["required"]


class TestHandleCallTool:
    """Test handle_call_tool MCP dispatch"""

    @pytest.mark.asyncio
    async def test_web_search_empty_query(self):
        """Empty query returns error message"""
        result = await server.handle_call_tool("web_search", {"query": ""})
        assert len(result) == 1
        assert "不能为空" in result[0].text

    @pytest.mark.asyncio
    async def test_web_search_no_query_key(self):
        """Missing query key returns error message"""
        result = await server.handle_call_tool("web_search", {})
        assert len(result) == 1
        assert "不能为空" in result[0].text

    @pytest.mark.asyncio
    async def test_web_search_none_arguments(self):
        """None arguments treated as empty dict, returns error"""
        result = await server.handle_call_tool("web_search", None)
        assert len(result) == 1
        assert "不能为空" in result[0].text

    @pytest.mark.asyncio
    async def test_web_search_duckduckgo_engine(self, monkeypatch):
        """DuckDuckGo engine search with mocked results"""
        mock_results = [
            {
                "title": "R1",
                "url": "https://a.com/1",
                "snippet": "S1",
                "type": "duckduckgo_result",
            },
        ]

        async def mock_search(self_inner, query, max_results=10):
            return mock_results

        async def mock_init(self_inner):
            return self_inner

        async def mock_close(self_inner, exc_type=None, exc_val=None, exc_tb=None):
            pass

        monkeypatch.setattr(WebSearcher, "__aenter__", mock_init)
        monkeypatch.setattr(WebSearcher, "__aexit__", mock_close)
        monkeypatch.setattr(WebSearcher, "search_duckduckgo", mock_search)
        monkeypatch.setattr(
            WebSearcher, "search_html_duckduckgo", AsyncMock(return_value=[])
        )

        result = await server.handle_call_tool(
            "web_search",
            {"query": "test", "search_engine": "duckduckgo", "max_results": 5},
        )
        assert len(result) == 1
        assert "R1" in result[0].text
        assert "https://a.com/1" in result[0].text

    @pytest.mark.asyncio
    async def test_duckduckgo_no_redundant_html_fallback(self, monkeypatch):
        """验证 search_with_fallback 不再冗余调用 search_html_duckduckgo

        search_duckduckgo() 内部已有三层回退到 HTML，
        外层不应再重复调用 search_html_duckduckgo()。
        """
        mock_results = [
            {
                "title": "R1",
                "url": "https://a.com/1",
                "snippet": "S1",
                "type": "duckduckgo_result",
            },
        ]
        html_mock = AsyncMock(return_value=[])

        async def mock_search(self_inner, query, max_results=10):
            return mock_results

        async def mock_init(self_inner):
            return self_inner

        async def mock_close(self_inner, exc_type=None, exc_val=None, exc_tb=None):
            pass

        monkeypatch.setattr(WebSearcher, "__aenter__", mock_init)
        monkeypatch.setattr(WebSearcher, "__aexit__", mock_close)
        monkeypatch.setattr(WebSearcher, "search_duckduckgo", mock_search)
        monkeypatch.setattr(WebSearcher, "search_html_duckduckgo", html_mock)

        result = await server.handle_call_tool(
            "web_search",
            {"query": "test", "search_engine": "duckduckgo", "max_results": 5},
        )
        assert len(result) == 1
        assert "R1" in result[0].text
        # 关键断言：外层不应调用 search_html_duckduckgo
        html_mock.assert_not_called()

    @pytest.mark.asyncio
    async def test_web_search_bing_engine(self, monkeypatch):
        """Bing engine search with mocked results"""
        mock_results = [
            {
                "title": "B1",
                "url": "https://b.com/1",
                "snippet": "BS1",
                "type": "bing_result",
            },
        ]

        async def mock_search(self_inner, query, max_results=10):
            return mock_results

        async def mock_init(self_inner):
            return self_inner

        async def mock_close(self_inner, exc_type=None, exc_val=None, exc_tb=None):
            pass

        monkeypatch.setattr(WebSearcher, "__aenter__", mock_init)
        monkeypatch.setattr(WebSearcher, "__aexit__", mock_close)
        monkeypatch.setattr(WebSearcher, "search_bing", mock_search)

        result = await server.handle_call_tool(
            "web_search", {"query": "test", "search_engine": "bing", "max_results": 5}
        )
        assert len(result) == 1
        assert "B1" in result[0].text

    @pytest.mark.asyncio
    async def test_web_search_google_engine(self, monkeypatch):
        """Google engine search with mocked results"""
        mock_results = [
            {
                "title": "G1",
                "url": "https://g.com/1",
                "snippet": "GS1",
                "type": "google_result",
            },
        ]

        async def mock_search(self_inner, query, max_results=10):
            return mock_results

        async def mock_init(self_inner):
            return self_inner

        async def mock_close(self_inner, exc_type=None, exc_val=None, exc_tb=None):
            pass

        monkeypatch.setattr(WebSearcher, "__aenter__", mock_init)
        monkeypatch.setattr(WebSearcher, "__aexit__", mock_close)
        monkeypatch.setattr(WebSearcher, "search_google", mock_search)

        result = await server.handle_call_tool(
            "web_search", {"query": "test", "search_engine": "google", "max_results": 5}
        )
        assert len(result) == 1
        assert "G1" in result[0].text

    @pytest.mark.asyncio
    async def test_web_search_both_engine(self, monkeypatch):
        """Both engine runs duckduckgo + google + bing concurrently"""
        ddg_results = [
            {
                "title": "DDG1",
                "url": "https://ddg.com/1",
                "snippet": "DS1",
                "type": "duckduckgo_result",
            },
        ]
        google_results = [
            {
                "title": "G1",
                "url": "https://g.com/1",
                "snippet": "GS1",
                "type": "google_result",
            },
        ]
        bing_results = [
            {
                "title": "B1",
                "url": "https://b.com/1",
                "snippet": "BS1",
                "type": "bing_result",
            },
        ]

        async def mock_ddg(self_inner, query, max_results=10):
            return ddg_results

        async def mock_html_ddg(self_inner, query, max_results=10):
            return []

        async def mock_google(self_inner, query, max_results=10):
            return google_results

        async def mock_bing(self_inner, query, max_results=10):
            return bing_results

        async def mock_init(self_inner):
            return self_inner

        async def mock_close(self_inner, exc_type=None, exc_val=None, exc_tb=None):
            pass

        monkeypatch.setattr(WebSearcher, "__aenter__", mock_init)
        monkeypatch.setattr(WebSearcher, "__aexit__", mock_close)
        monkeypatch.setattr(WebSearcher, "search_duckduckgo", mock_ddg)
        monkeypatch.setattr(WebSearcher, "search_html_duckduckgo", mock_html_ddg)
        monkeypatch.setattr(WebSearcher, "search_google", mock_google)
        monkeypatch.setattr(WebSearcher, "search_bing", mock_bing)

        result = await server.handle_call_tool(
            "web_search", {"query": "test", "search_engine": "both", "max_results": 10}
        )
        assert len(result) == 1
        text = result[0].text
        assert "DDG1" in text
        assert "G1" in text
        assert "B1" in text

    @pytest.mark.asyncio
    async def test_web_search_with_serpapi_key(self, monkeypatch):
        """When SERPAPI_KEY is set, serpapi engine is appended"""
        monkeypatch.setattr(server, "SERPAPI_KEY", "test-key")
        monkeypatch.setattr(server, "TAVILY_API_KEY", None)

        serpapi_results = [
            {
                "title": "SP1",
                "url": "https://sp.com/1",
                "snippet": "SS1",
                "type": "serpapi_result",
            },
        ]

        async def mock_serpapi(self_inner, query, max_results=10):
            return serpapi_results

        async def mock_ddg(self_inner, query, max_results=10):
            return []

        async def mock_html_ddg(self_inner, query, max_results=10):
            return []

        async def mock_init(self_inner):
            return self_inner

        async def mock_close(self_inner, exc_type=None, exc_val=None, exc_tb=None):
            pass

        monkeypatch.setattr(WebSearcher, "__aenter__", mock_init)
        monkeypatch.setattr(WebSearcher, "__aexit__", mock_close)
        monkeypatch.setattr(WebSearcher, "search_duckduckgo", mock_ddg)
        monkeypatch.setattr(WebSearcher, "search_html_duckduckgo", mock_html_ddg)
        monkeypatch.setattr(WebSearcher, "search_google", AsyncMock(return_value=[]))
        monkeypatch.setattr(WebSearcher, "search_bing", AsyncMock(return_value=[]))
        monkeypatch.setattr(WebSearcher, "search_serpapi", mock_serpapi)

        result = await server.handle_call_tool(
            "web_search",
            {"query": "test", "search_engine": "duckduckgo", "max_results": 5},
        )
        assert len(result) == 1
        assert "SP1" in result[0].text

    @pytest.mark.asyncio
    async def test_web_search_no_results(self, monkeypatch):
        """All engines return empty results"""

        async def mock_ddg(self_inner, query, max_results=10):
            return []

        async def mock_html_ddg(self_inner, query, max_results=10):
            return []

        async def mock_init(self_inner):
            return self_inner

        async def mock_close(self_inner, exc_type=None, exc_val=None, exc_tb=None):
            pass

        monkeypatch.setattr(WebSearcher, "__aenter__", mock_init)
        monkeypatch.setattr(WebSearcher, "__aexit__", mock_close)
        monkeypatch.setattr(WebSearcher, "search_duckduckgo", mock_ddg)
        monkeypatch.setattr(WebSearcher, "search_html_duckduckgo", mock_html_ddg)
        monkeypatch.setattr(WebSearcher, "search_google", AsyncMock(return_value=[]))
        monkeypatch.setattr(WebSearcher, "search_bing", AsyncMock(return_value=[]))

        result = await server.handle_call_tool(
            "web_search",
            {"query": "test", "search_engine": "duckduckgo", "max_results": 5},
        )
        assert len(result) == 1
        assert "未找到" in result[0].text

    @pytest.mark.asyncio
    async def test_get_webpage_content_success(self, monkeypatch):
        """get_webpage_content returns formatted content"""

        async def mock_get_page(self_inner, url):
            return "Page content here"

        async def mock_init(self_inner):
            return self_inner

        async def mock_close(self_inner, exc_type=None, exc_val=None, exc_tb=None):
            pass

        monkeypatch.setattr(WebSearcher, "__aenter__", mock_init)
        monkeypatch.setattr(WebSearcher, "__aexit__", mock_close)
        monkeypatch.setattr(WebSearcher, "get_page_content", mock_get_page)

        result = await server.handle_call_tool(
            "get_webpage_content", {"url": "https://example.com"}
        )
        assert len(result) == 1
        assert "Page content here" in result[0].text
        assert "https://example.com" in result[0].text

    @pytest.mark.asyncio
    async def test_get_webpage_content_empty_url(self):
        """get_webpage_content with empty URL returns error"""
        result = await server.handle_call_tool("get_webpage_content", {"url": ""})
        assert len(result) == 1
        assert "不能为空" in result[0].text

    @pytest.mark.asyncio
    async def test_get_webpage_content_empty_content(self, monkeypatch):
        """get_webpage_content returns error when content is empty"""

        async def mock_get_page(self_inner, url):
            return ""

        async def mock_init(self_inner):
            return self_inner

        async def mock_close(self_inner, exc_type=None, exc_val=None, exc_tb=None):
            pass

        monkeypatch.setattr(WebSearcher, "__aenter__", mock_init)
        monkeypatch.setattr(WebSearcher, "__aexit__", mock_close)
        monkeypatch.setattr(WebSearcher, "get_page_content", mock_get_page)

        result = await server.handle_call_tool(
            "get_webpage_content", {"url": "https://example.com"}
        )
        assert len(result) == 1
        assert "无法获取" in result[0].text or "为空" in result[0].text

    @pytest.mark.asyncio
    async def test_unknown_tool_name(self):
        """Unknown tool name returns error"""
        result = await server.handle_call_tool("nonexistent_tool", {})
        assert len(result) == 1
        assert "未知工具" in result[0].text
        assert "nonexistent_tool" in result[0].text

    @pytest.mark.asyncio
    async def test_web_search_url_dedup(self, monkeypatch):
        """Duplicate URLs across engines are deduplicated"""
        same_url_results_a = [
            {
                "title": "A1",
                "url": "https://shared.com/page",
                "snippet": "A snippet",
                "type": "duckduckgo_result",
            },
        ]
        same_url_results_b = [
            {
                "title": "B1",
                "url": "https://shared.com/page",
                "snippet": "B snippet",
                "type": "bing_result",
            },
        ]

        async def mock_ddg(self_inner, query, max_results=10):
            return same_url_results_a

        async def mock_html_ddg(self_inner, query, max_results=10):
            return []

        async def mock_bing(self_inner, query, max_results=10):
            return same_url_results_b

        async def mock_init(self_inner):
            return self_inner

        async def mock_close(self_inner, exc_type=None, exc_val=None, exc_tb=None):
            pass

        monkeypatch.setattr(WebSearcher, "__aenter__", mock_init)
        monkeypatch.setattr(WebSearcher, "__aexit__", mock_close)
        monkeypatch.setattr(WebSearcher, "search_duckduckgo", mock_ddg)
        monkeypatch.setattr(WebSearcher, "search_html_duckduckgo", mock_html_ddg)
        monkeypatch.setattr(WebSearcher, "search_google", AsyncMock(return_value=[]))
        monkeypatch.setattr(WebSearcher, "search_bing", mock_bing)

        result = await server.handle_call_tool(
            "web_search", {"query": "test", "search_engine": "both", "max_results": 10}
        )
        assert len(result) == 1
        # Count occurrences of the shared URL
        count = result[0].text.count("https://shared.com/page")
        assert count == 1, f"URL should appear once after dedup, found {count} times"

    @pytest.mark.asyncio
    async def test_max_results_clamped_above上限(self, monkeypatch):
        """max_results > 20 is clamped to 20"""
        received_max = []

        async def mock_ddg(self_inner, query, max_results=10):
            received_max.append(max_results)
            return []

        async def mock_init(self_inner):
            return self_inner

        async def mock_close(self_inner, exc_type=None, exc_val=None, exc_tb=None):
            pass

        monkeypatch.setattr(WebSearcher, "__aenter__", mock_init)
        monkeypatch.setattr(WebSearcher, "__aexit__", mock_close)
        monkeypatch.setattr(WebSearcher, "search_duckduckgo", mock_ddg)
        monkeypatch.setattr(WebSearcher, "search_html_duckduckgo", AsyncMock(return_value=[]))
        monkeypatch.setattr(WebSearcher, "search_google", AsyncMock(return_value=[]))
        monkeypatch.setattr(WebSearcher, "search_bing", AsyncMock(return_value=[]))

        await server.handle_call_tool(
            "web_search", {"query": "test", "search_engine": "duckduckgo", "max_results": 1000}
        )
        assert received_max[-1] == 20, f"max_results should be clamped to 20, got {received_max[-1]}"

    @pytest.mark.asyncio
    async def test_max_results_clamped_below_minimum(self, monkeypatch):
        """max_results < 1 is clamped to 1"""
        received_max = []

        async def mock_ddg(self_inner, query, max_results=10):
            received_max.append(max_results)
            return []

        async def mock_init(self_inner):
            return self_inner

        async def mock_close(self_inner, exc_type=None, exc_val=None, exc_tb=None):
            pass

        monkeypatch.setattr(WebSearcher, "__aenter__", mock_init)
        monkeypatch.setattr(WebSearcher, "__aexit__", mock_close)
        monkeypatch.setattr(WebSearcher, "search_duckduckgo", mock_ddg)
        monkeypatch.setattr(WebSearcher, "search_html_duckduckgo", AsyncMock(return_value=[]))
        monkeypatch.setattr(WebSearcher, "search_google", AsyncMock(return_value=[]))
        monkeypatch.setattr(WebSearcher, "search_bing", AsyncMock(return_value=[]))

        await server.handle_call_tool(
            "web_search", {"query": "test", "search_engine": "duckduckgo", "max_results": -5}
        )
        assert received_max[-1] == 1, f"max_results should be clamped to 1, got {received_max[-1]}"

    @pytest.mark.asyncio
    async def test_max_results_non_integer_handled(self, monkeypatch):
        """Non-integer max_results is coerced to int and clamped"""
        received_max = []

        async def mock_ddg(self_inner, query, max_results=10):
            received_max.append(max_results)
            return []

        async def mock_init(self_inner):
            return self_inner

        async def mock_close(self_inner, exc_type=None, exc_val=None, exc_tb=None):
            pass

        monkeypatch.setattr(WebSearcher, "__aenter__", mock_init)
        monkeypatch.setattr(WebSearcher, "__aexit__", mock_close)
        monkeypatch.setattr(WebSearcher, "search_duckduckgo", mock_ddg)
        monkeypatch.setattr(WebSearcher, "search_html_duckduckgo", AsyncMock(return_value=[]))
        monkeypatch.setattr(WebSearcher, "search_google", AsyncMock(return_value=[]))
        monkeypatch.setattr(WebSearcher, "search_bing", AsyncMock(return_value=[]))

        # String that looks like a number
        await server.handle_call_tool(
            "web_search", {"query": "test", "search_engine": "duckduckgo", "max_results": "15"}
        )
        assert received_max[-1] == 15, f"String '15' should be coerced to int 15, got {received_max[-1]}"
