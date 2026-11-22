"""Contract the remote MCP server relies on (docs/tech/remote-mcp.md).

The backend copies client.py, errors.py, tools.py, prompts.py and resources.py and replaces only
the HTTP client: a ScrapeReviewsClient subclass whose __init__ sets `self._client` to an
httpx.AsyncClient on an in-memory transport (ASGITransport in production). These tests keep that
seam working: if they fail, the remote server's InProcessClient must change too.
"""

from __future__ import annotations

import json

import httpx
import pytest
from mcp.server.fastmcp import FastMCP

from scrapereviews_mcp.client import ScrapeReviewsClient
from scrapereviews_mcp.tools import register_tools

from .payloads import company_summary, list_meta


class InMemoryClient(ScrapeReviewsClient):
    def __init__(self, handler):  # noqa: D107 - skips the parent's network client on purpose
        self._client = httpx.AsyncClient(
            transport=httpx.MockTransport(handler),
            base_url="http://mcp.internal",
            headers={"X-SR-MCP-Internal": "nonce"},
        )


@pytest.mark.asyncio
async def test_tools_run_on_a_replaced_http_client():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"data": [company_summary()], "meta": list_meta(1, None)})

    client = InMemoryClient(handler)
    server = FastMCP("test")
    register_tools(server, lambda: client)
    tool = server._tool_manager._tools["search_companies"].fn

    result = json.loads(await tool(query="zalando"))

    assert seen[0].url.path == "/v1/companies/search"
    assert seen[0].headers["X-SR-MCP-Internal"] == "nonce"
    assert "X-API-Key" not in seen[0].headers
    assert result["credits_used"] == 1


def test_tool_names_are_stable():
    """The remote server's TOOL_TITLES map is keyed by these names."""
    server = FastMCP("test")
    register_tools(server, lambda: ScrapeReviewsClient(api_key="k"))
    assert sorted(server._tool_manager._tools) == [
        "get_category_companies",
        "get_company",
        "get_reviews",
        "list_categories",
        "search_companies",
    ]
