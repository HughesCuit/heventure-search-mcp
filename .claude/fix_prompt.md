Fix the TestSafeGetRedirectLoop class in tests/test_server.py. The problem: 3 tests use 'async def mock_get(url, **kwargs)' for mock_session.get, but _safe_get uses 'async with self.session.get(url) as response:' which expects an async context manager, not a coroutine.

Fix these 3 test methods:
1. test_redirect_loop_trailing_slash
2. test_redirect_loop_query_param_order  
3. test_redirect_chain_exceeds_max_redirects

Replace the 'async def mock_get' pattern with a factory function that returns a MagicMock with __aenter__ and __aexit__ (following the pattern used in test_search_duckduckgo_non_200_fallback on line 309).

The correct pattern is:
def mock_session_get(url, **kwargs):
    cm = MagicMock()
    if condition:
        cm.__aenter__ = AsyncMock(return_value=response1)
    else:
        cm.__aenter__ = AsyncMock(return_value=response2)
    cm.__aexit__ = AsyncMock(return_value=None)
    return cm

mock_session = MagicMock()
mock_session.get = MagicMock(side_effect=mock_session_get)

Keep all existing assertions and test logic intact. Just fix the mock pattern.
