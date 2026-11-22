"""Integration tests — verify the MCP server registers all components."""

from __future__ import annotations

import importlib
import os
from unittest.mock import patch

import pytest
from mcp.server.fastmcp import FastMCP


@pytest.fixture
def server():
    """Import server module with a fake API key set."""
    with patch.dict(os.environ, {"SCRAPEREVIEWS_API_KEY": "test_integration"}):
        import scrapereviews_mcp.server as srv_mod

        importlib.reload(srv_mod)
        yield srv_mod.mcp


def test_server_has_tools(server: FastMCP):
    assert set(server._tool_manager._tools) == {
        "search_companies",
        "get_company",
        "get_reviews",
        "list_categories",
        "get_category_companies",
    }


def test_server_has_resources(server: FastMCP):
    actual_uris = {str(k) for k in server._resource_manager._resources}
    assert actual_uris == {
        "scrapereviews://docs/api-reference",
        "scrapereviews://docs/quickstart",
        "scrapereviews://docs/pricing",
        "scrapereviews://docs/examples",
    }


def test_server_has_prompts(server: FastMCP):
    assert set(server._prompt_manager._prompts) == {
        "analyze_company_reviews",
        "compare_companies",
        "find_best_companies",
    }


@pytest.mark.asyncio
async def test_analyze_prompt_mentions_tools(server: FastMCP):
    prompt = server._prompt_manager._prompts["analyze_company_reviews"]
    text = await prompt.fn(domain="zalando.it", language="it")
    assert "get_company" in text and "get_reviews" in text
    assert 'language="it"' in text
