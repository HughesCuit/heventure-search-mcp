"""
测试用例 for heventure-search-mcp
"""

import json
import os
import sys
from unittest.mock import AsyncMock, MagicMock

import aiohttp
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

    def test_cache_key_query_normalization(self):
        """测试缓存键的查询归一化：语义相同的查询产生相同缓存键"""
        # 大小写归一化
        key1 = WebSearcher._get_cache_key("Python Tutorial", "google", 10)
        key2 = WebSearcher._get_cache_key("python tutorial", "google", 10)
        assert key1 == key2, "大小写不同应产生相同缓存键"

        # 多空格归一化
        key3 = WebSearcher._get_cache_key("Python  tutorial", "google", 10)
        key4 = WebSearcher._get_cache_key("Python   tutorial", "google", 10)
        assert key3 == key4, "多空格应合并为单空格"

        # 首尾空格归一化
        key5 = WebSearcher._get_cache_key("  Python tutorial  ", "google", 10)
        key6 = WebSearcher._get_cache_key("Python tutorial", "google", 10)
        assert key5 == key6, "首尾空格应被去除"

        # 组合场景
        key7 = WebSearcher._get_cache_key("  Python  tutorial  ", "google", 10)
        assert key7 == key6, "组合归一化应产生相同缓存键"

    def test_normalize_query(self):
        """测试 _normalize_query 方法"""
        assert WebSearcher._normalize_query("Hello World") == "hello world"
        assert WebSearcher._normalize_query("  spaces  ") == "spaces"
        assert WebSearcher._normalize_query("multiple   spaces") == "multiple spaces"
        assert WebSearcher._normalize_query("Mixed CASE  With   Spaces") == "mixed case with spaces"

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
    async def test_duckduckgo_within_engine_url_dedup(self, monkeypatch):
        """DuckDuckGo API 返回 Answer+Abstract 共享同一 URL 时，within-engine 去重应消除重复

        模拟 DuckDuckGo Instant Answer API 返回的 JSON 数据中
        AnswerURL 和 AbstractURL 相同，验证 search_duckduckgo 不会返回重复结果。
        """
        shared_url = "https://example.com/shared"
        ddg_api_response = json.dumps(
            {
                "Answer": "This is the answer",
                "AnswerURL": shared_url,
                "Abstract": "This is the abstract",
                "AbstractURL": shared_url,
                "Heading": "Test Heading",
                "RelatedTopics": [
                    {
                        "Text": "Related topic - example.com",
                        "FirstURL": "https://example.com/related",
                    }
                ],
            }
        )

        class MockResp:
            status = 200

            async def text(self):
                return ddg_api_response

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

        def mock_get(self_inner, url, timeout=None):
            return MockResp()

        monkeypatch.setattr("aiohttp.ClientSession.get", mock_get)

        async with WebSearcher() as searcher:
            results = await searcher.search_duckduckgo("test query", max_results=10)

        urls = [r["url"] for r in results]
        assert urls.count(shared_url) == 1, (
            f"URL {shared_url} should appear once, got {urls.count(shared_url)}"
        )
        assert len(results) == 2  # 1 answer/abstract + 1 related topic

    @pytest.mark.asyncio
    async def test_duckduckgo_within_engine_empty_url_dedup(self, monkeypatch):
        """DuckDuckGo API 返回多个空 URL 结果时，最多保留一个"""
        ddg_api_response = json.dumps(
            {
                "Answer": "Answer without URL",
                "AnswerURL": "",
                "Abstract": "Abstract without URL",
                "AbstractURL": "",
            }
        )

        class MockResp:
            status = 200

            async def text(self):
                return ddg_api_response

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

        def mock_get(self_inner, url, timeout=None):
            return MockResp()

        monkeypatch.setattr("aiohttp.ClientSession.get", mock_get)

        async with WebSearcher() as searcher:
            results = await searcher.search_duckduckgo("empty url test", max_results=10)
        assert len(results) == 1, f"Expected 1 result (empty URL dedup), got {len(results)}"
        assert results[0]["url"] == ""

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

    @pytest.mark.asyncio
    async def test_max_results_non_numeric_string_defaults(self, monkeypatch):
        """Non-numeric max_results string like 'abc' should default to 10."""
        received_max = []

        async def mock_search(self, query, max_results=10):
            received_max.append(max_results)
            return []

        monkeypatch.setattr(WebSearcher, "search_duckduckgo", mock_search)
        monkeypatch.setattr(WebSearcher, "search_html_duckduckgo", AsyncMock(return_value=[]))
        monkeypatch.setattr(WebSearcher, "search_google", AsyncMock(return_value=[]))
        monkeypatch.setattr(WebSearcher, "search_bing", AsyncMock(return_value=[]))

        await server.handle_call_tool(
            "web_search", {"query": "test", "search_engine": "duckduckgo", "max_results": "abc"}
        )
        assert received_max[-1] == 10, f"Non-numeric 'abc' should default to 10, got {received_max[-1]}"


class TestSSRFValidation:
    """SSRF URL 验证测试"""

    def test_validate_url_allows_https(self):
        """正常 HTTPS URL 应通过验证"""
        assert WebSearcher._validate_url("https://example.com") is not None

    def test_validate_url_allows_http(self):
        """正常 HTTP URL 应通过验证"""
        assert WebSearcher._validate_url("http://example.com") is not None

    def test_validate_url_allows_https_with_path(self):
        """带路径的 HTTPS URL 应通过"""
        assert WebSearcher._validate_url("https://example.com/path?q=1") is not None

    def test_validate_url_rejects_file_scheme(self):
        """file:// 协议应被拒绝"""
        assert WebSearcher._validate_url("file:///etc/passwd") is None

    def test_validate_url_rejects_ftp_scheme(self):
        """ftp:// 协议应被拒绝"""
        assert WebSearcher._validate_url("ftp://example.com/file") is None

    def test_validate_url_rejects_data_scheme(self):
        """data: 协议应被拒绝"""
        assert WebSearcher._validate_url("data:text/html,<script>alert(1)</script>") is None

    def test_validate_url_rejects_javascript_scheme(self):
        """javascript: 协议应被拒绝"""
        assert WebSearcher._validate_url("javascript:alert(1)") is None

    def test_validate_url_rejects_loopback_ipv4(self):
        """127.x.x.x 回环地址应被拒绝"""
        assert WebSearcher._validate_url("http://127.0.0.1") is None
        assert WebSearcher._validate_url("http://127.0.0.1:8080/path") is None
        assert WebSearcher._validate_url("http://127.255.255.255") is None

    def test_validate_url_rejects_loopback_ipv6(self):
        """IPv6 回环地址应被拒绝"""
        assert WebSearcher._validate_url("http://[::1]") is None
        assert WebSearcher._validate_url("http://[::1]:8080") is None

    def test_validate_url_rejects_rfc1918_10(self):
        """10.x.x.x 私有地址应被拒绝"""
        assert WebSearcher._validate_url("http://10.0.0.1") is None
        assert WebSearcher._validate_url("http://10.255.255.255") is None
        assert WebSearcher._validate_url("http://10.0.0.1:3000/api") is None

    def test_validate_url_rejects_rfc1918_172(self):
        """172.16-31.x.x 私有地址应被拒绝"""
        assert WebSearcher._validate_url("http://172.16.0.1") is None
        assert WebSearcher._validate_url("http://172.31.255.255") is None
        assert WebSearcher._validate_url("http://172.20.0.1:8080") is None

    def test_validate_url_rejects_rfc1918_192(self):
        """192.168.x.x 私有地址应被拒绝"""
        assert WebSearcher._validate_url("http://192.168.1.1") is None
        assert WebSearcher._validate_url("http://192.168.0.0") is None

    def test_validate_url_rejects_link_local(self):
        """169.254.x.x 链路本地地址应被拒绝"""
        assert WebSearcher._validate_url("http://169.254.169.254") is None
        assert WebSearcher._validate_url("http://169.254.0.1") is None

    def test_validate_url_rejects_cloud_metadata(self):
        """AWS/GCP/Azure 元数据端点应被拒绝"""
        assert WebSearcher._validate_url("http://169.254.169.254/latest/meta-data/") is None
        assert WebSearcher._validate_url("http://169.254.169.254/latest/user-data") is None

    def test_validate_url_rejects_unspecified(self):
        """0.0.0.0 未指定地址应被拒绝"""
        assert WebSearcher._validate_url("http://0.0.0.0") is None

    def test_validate_url_rejects_ipv6_ula(self):
        """IPv6 ULA (fc00::/7) 地址应被拒绝"""
        assert WebSearcher._validate_url("http://[fc00::1]") is None
        assert WebSearcher._validate_url("http://[fd00::1]") is None

    def test_validate_url_rejects_ipv6_link_local(self):
        """IPv6 链路本地地址应被拒绝"""
        assert WebSearcher._validate_url("http://[fe80::1]") is None

    def test_validate_url_rejects_empty(self):
        """空 URL 应被拒绝"""
        assert WebSearcher._validate_url("") is None

    def test_validate_url_rejects_no_scheme(self):
        """无协议的 URL 应被拒绝"""
        assert WebSearcher._validate_url("example.com") is None

    def test_validate_url_rejects_no_hostname(self):
        """无主机名的 URL 应被拒绝"""
        assert WebSearcher._validate_url("http://") is None

    def test_validate_url_allows_public_ip(self):
        """公网 IP 应通过验证"""
        assert WebSearcher._validate_url("http://8.8.8.8") is not None
        assert WebSearcher._validate_url("https://1.1.1.1") is not None

    def test_validate_url_allows_ipv6_public(self):
        """公网 IPv6 应通过验证"""
        assert WebSearcher._validate_url("http://[2606:4700::1]") is not None  # Cloudflare IPv6

    @pytest.mark.asyncio
    async def test_get_webpage_content_rejects_ssrf(self, monkeypatch):
        """get_webpage_content 工具拒绝 SSRF URL"""
        result = await server.handle_call_tool(
            "get_webpage_content", {"url": "http://169.254.169.254/latest/meta-data/"}
        )
        assert len(result) == 1
        assert "不安全" in result[0].text

    @pytest.mark.asyncio
    async def test_get_webpage_content_rejects_file_scheme(self, monkeypatch):
        """get_webpage_content 工具拒绝 file:// 协议"""
        result = await server.handle_call_tool(
            "get_webpage_content", {"url": "file:///etc/passwd"}
        )
        assert len(result) == 1
        assert "不安全" in result[0].text

    @pytest.mark.asyncio
    async def test_get_webpage_content_rejects_private_ip(self, monkeypatch):
        """get_webpage_content 工具拒绝私有 IP"""
        result = await server.handle_call_tool(
            "get_webpage_content", {"url": "http://192.168.1.1/admin"}
        )
        assert len(result) == 1
        assert "不安全" in result[0].text

    @pytest.mark.asyncio
    async def test_get_page_content_rejects_ssrf(self):
        """get_page_content 方法拒绝 SSRF URL"""
        async with WebSearcher() as searcher:
            result = await searcher.get_page_content("http://127.0.0.1:8080")
            assert result == ""

    @pytest.mark.asyncio
    async def test_get_page_content_rejects_loopback(self):
        """get_page_content 方法拒绝回环地址"""
        async with WebSearcher() as searcher:
            result = await searcher.get_page_content("http://[::1]:3000/api")
            assert result == ""


class TestSSRFRedirectBypass:
    """SSRF 重定向绕过测试"""

    @pytest.fixture
    def searcher(self):
        WebSearcher.clear_cache()
        return WebSearcher()

    def test_is_ip_private_resolves_private_hostname(self, monkeypatch):
        """主机名解析到私有 IP 时应返回 True"""
        import socket as _socket

        def mock_getaddrinfo(host, port, *args, **kwargs):
            return [
                (_socket.AF_INET, _socket.SOCK_STREAM, 0, "", ("10.0.0.1", 0)),
            ]

        monkeypatch.setattr(_socket, "getaddrinfo", mock_getaddrinfo)
        assert WebSearcher._is_ip_private("metadata.google.internal") is True

    def test_is_ip_private_resolves_public_hostname(self, monkeypatch):
        """主机名解析到公网 IP 时应返回 False"""
        import socket as _socket

        def mock_getaddrinfo(host, port, *args, **kwargs):
            return [
                (_socket.AF_INET, _socket.SOCK_STREAM, 0, "", ("93.184.216.34", 0)),
            ]

        monkeypatch.setattr(_socket, "getaddrinfo", mock_getaddrinfo)
        assert WebSearcher._is_ip_private("example.com") is False

    def test_is_ip_private_dns_failure_treated_as_private(self, monkeypatch):
        """DNS 解析失败时应返回 True（安全默认值）"""
        import socket as _socket

        def mock_getaddrinfo(host, port, *args, **kwargs):
            raise _socket.gaierror("Name resolution failed")

        monkeypatch.setattr(_socket, "getaddrinfo", mock_getaddrinfo)
        assert WebSearcher._is_ip_private("nonexistent.invalid") is True

    def test_is_ip_private_raw_private_ip(self):
        """原始私有 IP 字符串应返回 True"""
        assert WebSearcher._is_ip_private("10.0.0.1") is True
        assert WebSearcher._is_ip_private("192.168.1.1") is True
        assert WebSearcher._is_ip_private("127.0.0.1") is True

    def test_is_ip_private_raw_public_ip(self):
        """原始公网 IP 字符串应返回 False"""
        assert WebSearcher._is_ip_private("8.8.8.8") is False
        assert WebSearcher._is_ip_private("1.1.1.1") is False

    @pytest.mark.asyncio
    async def test_safe_get_blocks_redirect_to_private_ip(self, searcher):
        """_safe_get 应阻止重定向到私有 IP（如 169.254.169.254）"""
        redirect_response = AsyncMock()
        redirect_response.status = 302
        redirect_response.headers = {"Location": "http://169.254.169.254/latest/meta-data/"}

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=redirect_response)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_cm)
        searcher.session = mock_session

        result = await searcher._safe_get("https://example.com/start")
        assert result is None
        # Should only make one request — blocked before following redirect
        assert mock_session.get.call_count == 1

    @pytest.mark.asyncio
    async def test_safe_get_blocks_redirect_to_private_10x(self, searcher):
        """_safe_get 应阻止重定向到 10.x.x.x"""
        redirect_response = AsyncMock()
        redirect_response.status = 302
        redirect_response.headers = {"Location": "http://10.0.0.1:8080/admin"}

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=redirect_response)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_cm)
        searcher.session = mock_session

        result = await searcher._safe_get("https://example.com/start")
        assert result is None

    @pytest.mark.asyncio
    async def test_safe_get_allows_redirect_to_public_ip(self, searcher):
        """_safe_get 应允许重定向到公网 IP"""
        redirect_response = AsyncMock()
        redirect_response.status = 302
        redirect_response.headers = {"Location": "https://93.184.216.34/final"}

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
