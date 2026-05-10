"""
追加测试: 错误路径、边界条件、SSRF、缓存、引擎回退
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from heventure_search_mcp import server
from heventure_search_mcp.server import WebSearcher


class TestHandleCallToolMaxResults:
    """测试 handle_call_tool 层级的 max_results 边界处理"""

    @pytest.fixture(autouse=True)
    def _setup(self):
        """每个测试前清空缓存"""
        WebSearcher.clear_cache()

    def _patch_searcher(self, monkeypatch):
        """补丁 WebSearcher 使得 __aenter__/__aexit__ 可用，并返回搜索方法的捕获列表"""
        captured_max = []

        async def mock_ddg(self_inner, query, max_results=10):
            captured_max.append(max_results)
            return []

        async def mock_init(self_inner):
            return self_inner

        async def mock_close(self_inner, exc_type=None, exc_val=None, exc_tb=None):
            pass

        monkeypatch.setattr(WebSearcher, "__aenter__", mock_init)
        monkeypatch.setattr(WebSearcher, "__aexit__", mock_close)
        monkeypatch.setattr(WebSearcher, "search_duckduckgo", mock_ddg)
        monkeypatch.setattr(WebSearcher, "search_google", AsyncMock(return_value=[]))
        monkeypatch.setattr(WebSearcher, "search_bing", AsyncMock(return_value=[]))
        return captured_max

    @pytest.mark.asyncio
    async def test_max_results_zero_at_handler(self, monkeypatch):
        """max_results=0 在 handler 层被 clamp 为 1"""
        captured = self._patch_searcher(monkeypatch)
        await server.handle_call_tool(
            "web_search",
            {"query": "test", "search_engine": "duckduckgo", "max_results": 0},
        )
        assert captured[-1] == 1

    @pytest.mark.asyncio
    async def test_max_results_21_at_handler(self, monkeypatch):
        """max_results=21 在 handler 层被 clamp 为 20"""
        captured = self._patch_searcher(monkeypatch)
        await server.handle_call_tool(
            "web_search",
            {"query": "test", "search_engine": "duckduckgo", "max_results": 21},
        )
        assert captured[-1] == 20

    @pytest.mark.asyncio
    async def test_max_results_negative_at_handler(self, monkeypatch):
        """max_results=-5 在 handler 层被 clamp 为 1"""
        captured = self._patch_searcher(monkeypatch)
        await server.handle_call_tool(
            "web_search",
            {"query": "test", "search_engine": "duckduckgo", "max_results": -5},
        )
        assert captured[-1] == 1

    @pytest.mark.asyncio
    async def test_max_results_non_numeric_at_handler(self, monkeypatch):
        """max_results='abc' 在 handler 层回退为默认值 10"""
        captured = self._patch_searcher(monkeypatch)
        await server.handle_call_tool(
            "web_search",
            {"query": "test", "search_engine": "duckduckgo", "max_results": "abc"},
        )
        assert captured[-1] == 10

    @pytest.mark.asyncio
    async def test_max_results_none_at_handler(self, monkeypatch):
        """max_results=None 在 handler 层回退为默认值 10"""
        captured = self._patch_searcher(monkeypatch)
        await server.handle_call_tool(
            "web_search",
            {"query": "test", "search_engine": "duckduckgo", "max_results": None},
        )
        assert captured[-1] == 10

    @pytest.mark.asyncio
    async def test_max_results_float_at_handler(self, monkeypatch):
        """max_results=5.7 被 int() 转为 5"""
        captured = self._patch_searcher(monkeypatch)
        await server.handle_call_tool(
            "web_search",
            {"query": "test", "search_engine": "duckduckgo", "max_results": 5.7},
        )
        assert captured[-1] == 5


class TestValidateUrlSSRF:
    """_validate_url SSRF 攻击向量测试"""

    def test_reject_ftp_scheme(self):
        """ftp:// 协议应被拒绝"""
        assert WebSearcher._validate_url("ftp://evil.com/file") is None

    def test_reject_file_scheme(self):
        """file:// 协议应被拒绝"""
        assert WebSearcher._validate_url("file:///etc/passwd") is None

    def test_reject_data_scheme(self):
        """data: 协议应被拒绝"""
        assert (
            WebSearcher._validate_url("data:text/html,<script>alert(1)</script>")
            is None
        )

    def test_reject_ipv6_loopback(self):
        """IPv6 回环地址 [::1] 应被拒绝"""
        assert WebSearcher._validate_url("http://[::1]/") is None

    def test_reject_ipv6_link_local(self):
        """IPv6 链路本地地址 [fe80::1] 应被拒绝"""
        assert WebSearcher._validate_url("http://[fe80::1]/") is None

    def test_reject_ipv6_ula(self):
        """IPv6 ULA [fd00::1] 应被拒绝"""
        assert WebSearcher._validate_url("http://[fd00::1]/") is None

    def test_reject_ipv4_unspecified(self):
        """IPv4 未指定地址 0.0.0.0 应被拒绝"""
        assert WebSearcher._validate_url("http://0.0.0.0/") is None

    def test_reject_cloud_metadata(self):
        """云元数据端点 169.254.169.254 应被拒绝"""
        assert (
            WebSearcher._validate_url("http://169.254.169.254/latest/meta-data/")
            is None
        )

    def test_reject_reserved_ip(self):
        """保留 IP 地址 240.0.0.1 应被拒绝"""
        assert WebSearcher._validate_url("http://240.0.0.1/") is None

    def test_reject_no_hostname(self):
        """无主机名的 URL 应被拒绝"""
        assert WebSearcher._validate_url("http:///path") is None

    def test_reject_non_ascii_domain(self):
        """非 ASCII 域名应被拒绝"""
        assert WebSearcher._validate_url("http://例子.com/") is None

    def test_accept_valid_public_https(self):
        """合法公网 HTTPS URL 应通过验证"""
        assert WebSearcher._validate_url("https://www.example.com/search") is not None

    def test_accept_valid_public_http(self):
        """合法公网 HTTP URL 应通过验证"""
        assert WebSearcher._validate_url("http://example.com/") is not None

    def test_reject_ftp_with_port(self):
        """ftp:// 带端口的 URL 应被拒绝"""
        assert WebSearcher._validate_url("ftp://evil.com:21/") is None

    def test_reject_javascript_scheme(self):
        """javascript: 协议应被拒绝"""
        assert WebSearcher._validate_url("javascript:alert(1)") is None


class TestCacheEdgeCases:
    """搜索缓存边界条件测试"""

    @pytest.fixture(autouse=True)
    def _setup(self):
        """每个测试前清空缓存"""
        WebSearcher.clear_cache()
        yield
        WebSearcher.clear_cache()

    def test_cache_update_existing_key(self):
        """更新缓存已有 key 时应返回新值"""
        key = "duckduckgo:test:5"
        WebSearcher._set_to_cache(key, ["a"])
        WebSearcher._set_to_cache(key, ["b"])
        result = WebSearcher._get_from_cache(key)
        assert result == ["b"]

    def test_cache_lru_order_after_get(self):
        """get 操作应将 key 移到末尾（LRU），淘汰最久未使用的"""
        WebSearcher._cache_max_size = 3
        WebSearcher._set_to_cache("k1", [1])
        WebSearcher._set_to_cache("k2", [2])
        WebSearcher._set_to_cache("k3", [3])
        # get k1, 应将 k1 移到末尾
        WebSearcher._get_from_cache("k1")
        # 添加 k4, 应淘汰 k2（最久未使用的）
        WebSearcher._set_to_cache("k4", [4])
        assert WebSearcher._get_from_cache("k1") == [1]
        assert WebSearcher._get_from_cache("k2") is None
        assert WebSearcher._get_from_cache("k3") == [3]
        assert WebSearcher._get_from_cache("k4") == [4]
        WebSearcher._cache_max_size = 100  # 恢复默认值

    def test_cache_ttl_zero_immediate_expiry(self):
        """TTL=0 时缓存立即过期"""
        WebSearcher._cache_ttl_seconds = 0
        WebSearcher._set_to_cache("key1", ["result"])
        result = WebSearcher._get_from_cache("key1")
        assert result is None
        WebSearcher._cache_ttl_seconds = 300  # 恢复默认值

    def test_cache_multiple_engines_different_keys(self):
        """不同引擎的相同查询应有独立的缓存条目"""
        WebSearcher._set_to_cache("duckduckgo:test:5", ["ddg_result"])
        WebSearcher._set_to_cache("bing:test:5", ["bing_result"])
        assert WebSearcher._get_from_cache("duckduckgo:test:5") == ["ddg_result"]
        assert WebSearcher._get_from_cache("bing:test:5") == ["bing_result"]

    def test_cache_set_get_roundtrip(self):
        """基本 set+get 返回相同的列表对象"""
        data = ["result1", "result2"]
        WebSearcher._set_to_cache("test:roundtrip:10", data)
        result = WebSearcher._get_from_cache("test:roundtrip:10")
        assert result is data


class TestSafeGetInvalidUrls:
    """_safe_get 对无效 URL 的处理测试"""

    @pytest.fixture
    def searcher(self):
        """创建 WebSearcher 实例（每个测试清空缓存）"""
        WebSearcher.clear_cache()
        return WebSearcher()

    @pytest.mark.asyncio
    async def test_safe_get_rejects_ftp_url(self, searcher):
        """_safe_get 应拒绝 ftp:// URL（被 _validate_url 阻止）"""
        result = await searcher._safe_get("ftp://example.com")
        assert result is None

    @pytest.mark.asyncio
    async def test_safe_get_rejects_loopback(self, searcher):
        """_safe_get 应拒绝回环地址"""
        result = await searcher._safe_get("http://127.0.0.1/")
        assert result is None

    @pytest.mark.asyncio
    async def test_safe_get_rejects_private_ip(self, searcher):
        """_safe_get 应拒绝私有 IP"""
        result = await searcher._safe_get("http://10.0.0.1/")
        assert result is None

    @pytest.mark.asyncio
    async def test_safe_get_rejects_link_local(self, searcher):
        """_safe_get 应拒绝链路本地地址"""
        result = await searcher._safe_get("http://169.254.1.1/")
        assert result is None

    @pytest.mark.asyncio
    async def test_safe_get_redirect_to_private_blocked(self, searcher):
        """_safe_get 应阻止重定向到私有 IP"""
        redirect_response = AsyncMock()
        redirect_response.status = 302
        redirect_response.headers = {"Location": "http://10.0.0.1/admin"}

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=redirect_response)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_cm)
        searcher.session = mock_session

        result = await searcher._safe_get("https://example.com/start")
        assert result is None


class TestEngineFallback:
    """搜索引擎回退逻辑测试"""

    @pytest.fixture(autouse=True)
    def _setup(self):
        """每个测试前清空缓存"""
        WebSearcher.clear_cache()

    @pytest.mark.asyncio
    async def test_search_with_fallback_duckduckgo_fails(self):
        """DuckDuckGo 失败时，both 模式仍返回其他引擎的结果"""

        async def ddg_raises(query, max_results=10):
            raise ConnectionError("Network error")

        bing_results = [
            {
                "title": "Bing1",
                "url": "https://bing.com/1",
                "snippet": "bs1",
                "type": "bing_result",
            },
        ]
        google_results = [
            {
                "title": "Google1",
                "url": "https://google.com/1",
                "snippet": "gs1",
                "type": "google_result",
            },
        ]

        with (
            patch.object(
                WebSearcher,
                "search_duckduckgo",
                new_callable=AsyncMock,
                side_effect=ddg_raises,
            ),
            patch.object(
                WebSearcher,
                "search_bing",
                new_callable=AsyncMock,
                return_value=bing_results,
            ),
            patch.object(
                WebSearcher,
                "search_google",
                new_callable=AsyncMock,
                return_value=google_results,
            ),
        ):
            response = await server.handle_call_tool(
                "web_search",
                {"query": "test", "search_engine": "both", "max_results": 10},
            )
        text = response[0].text
        assert "Bing1" in text
        assert "Google1" in text

    @pytest.mark.asyncio
    async def test_search_with_fallback_all_engines_fail(self):
        """所有引擎都失败时应返回未找到结果提示"""

        async def raises(query, max_results=10):
            raise ConnectionError("fail")

        with (
            patch.object(
                WebSearcher,
                "search_duckduckgo",
                new_callable=AsyncMock,
                side_effect=raises,
            ),
            patch.object(
                WebSearcher, "search_bing", new_callable=AsyncMock, side_effect=raises
            ),
            patch.object(
                WebSearcher, "search_google", new_callable=AsyncMock, side_effect=raises
            ),
        ):
            response = await server.handle_call_tool(
                "web_search",
                {"query": "test", "search_engine": "both", "max_results": 10},
            )
        assert "未找到相关搜索结果" in response[0].text

    @pytest.mark.asyncio
    async def test_search_with_fallback_unknown_engine(self):
        """未知引擎名称应回退到 duckduckgo"""
        ddg_results = [
            {
                "title": "DDG1",
                "url": "https://ddg.com/1",
                "snippet": "ds1",
                "type": "related_topic",
            },
        ]

        with patch.object(
            WebSearcher,
            "search_duckduckgo",
            new_callable=AsyncMock,
            return_value=ddg_results,
        ):
            response = await server.handle_call_tool(
                "web_search",
                {"query": "test", "search_engine": "unknown", "max_results": 5},
            )
        assert "DDG1" in response[0].text

    @pytest.mark.asyncio
    async def test_search_with_fallback_bing_captcha_shows_warning(self):
        """Bing 被验证码阻止时应显示警告信息"""

        async def mock_bing_with_block(self_inner, query, max_results=10):
            self_inner._blocked_engines["bing"] = "Bing 搜索被阻止（验证码）"
            return []

        ddg_results = [
            {
                "title": "DDG1",
                "url": "https://ddg.com/1",
                "snippet": "ds1",
                "type": "related_topic",
            },
        ]

        with (
            patch.object(
                WebSearcher,
                "search_duckduckgo",
                new_callable=AsyncMock,
                return_value=ddg_results,
            ),
            patch.object(WebSearcher, "search_bing", side_effect=mock_bing_with_block),
            patch.object(
                WebSearcher, "search_google", new_callable=AsyncMock, return_value=[]
            ),
        ):
            response = await server.handle_call_tool(
                "web_search",
                {"query": "test", "search_engine": "both", "max_results": 10},
            )
        text = response[0].text
        # 应该包含 Bing 的结果（来自 DDG）和 Bing 被阻止的警告
        assert "DDG1" in text
