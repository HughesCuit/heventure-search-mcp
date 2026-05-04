# heventure-search-mcp

MCP server providing web search capabilities via multiple engines.

## Architecture
- `server.py` — Main MCP server with `WebSearcher` class
- Search engines: DuckDuckGo, Bing, Google, SerpAPI, Tavily
- Caching: LRU cache with 300s TTL, max 100 entries
- Tests: `tests/test_server.py` (pytest)

## Key Commands
- `python3 -m pytest tests/ -x -q` — run tests
- `ruff check .` — lint
- `ruff format .` — format

## Code Standards
- Python 3.12+, async/await throughout
- Type hints on all public functions
- Google-style docstrings
- Minimize external dependencies (prefer stdlib)
- All search methods must use the cache mechanism

## Cache Pattern
```python
cache_key = self._get_cache_key(query, engine_name, max_results)
cached = self._get_from_cache(cache_key)
if cached:
    return cached
# ... perform search ...
self._set_to_cache(cache_key, results)
```
