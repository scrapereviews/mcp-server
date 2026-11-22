"""Tests for MCP tool handlers."""

from __future__ import annotations

import json

import pytest
import respx
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from scrapereviews_mcp.client import ScrapeReviewsClient
from scrapereviews_mcp.tools import register_tools

from .conftest import BASE_URL
from .payloads import company_summary, list_meta, reviews_page


@pytest.fixture
def tools():
    """Tool functions of a FastMCP instance with tools registered."""
    client = ScrapeReviewsClient(api_key="test", base_url=BASE_URL)
    server = FastMCP("test")
    register_tools(server, lambda: client)
    return {name: tool.fn for name, tool in server._tool_manager._tools.items()}


def test_descriptions_state_cost():
    server = FastMCP("test")
    register_tools(server, lambda: ScrapeReviewsClient(api_key="k", base_url=BASE_URL))
    for tool in server._tool_manager._tools.values():
        assert "Cost:" in tool.description, tool.name


@pytest.mark.asyncio
async def test_search_companies(tools, mock_api: respx.MockRouter):
    mock_api.get("/v1/companies/search", params={"query": "zalando"}).respond(
        200, json={"data": [company_summary()], "meta": list_meta(1, "next1")}
    )
    result = json.loads(await tools["search_companies"](query="zalando"))
    assert result["companies"][0] == {
        "domain": "zalando.it",
        "name": "Zalando",
        "trust_score": 1.9,
        "review_count": 13683,
        "categories": ["Shoe Store"],
        "city": "Berlin",
        "country": "Germany",
    }
    assert result["next_cursor"] == "next1"
    assert result["credits_used"] == 1


@pytest.mark.asyncio
async def test_get_company_compact(tools, mock_api: respx.MockRouter):
    profile = {
        **company_summary("monzo.com"),
        "description": None,
        "similar": [company_summary("revolut.com")],
        "is_closed": False,
    }
    mock_api.get("/v1/companies/monzo.com", params={"include_similar": "true"}).respond(
        200, json={"data": profile, "meta": {"credits_used": 2, "cache_hit": False}}
    )
    result = json.loads(await tools["get_company"](domain="monzo.com", include_similar=True))
    company = result["company"]
    assert "logo_url" not in company
    assert "description" not in company
    assert company["is_closed"] is False
    assert company["similar"][0]["domain"] == "revolut.com"
    assert result["credits_used"] == 2


@pytest.mark.asyncio
async def test_get_reviews(tools, mock_api: respx.MockRouter):
    route = mock_api.get("/v1/companies/zalando.it/reviews").respond(
        200, json=reviews_page(["r1", "r2"], next_cursor="c2")
    )
    raw = await tools["get_reviews"](domain="zalando.it", stars=[1, 2], limit=2)
    result = json.loads(raw)
    assert route.calls.last.request.url.params["stars"] == "1,2"
    assert result["company"]["name"] == "Zalando"
    first, second = result["reviews"]
    assert first["reply"]["text"] == "Sorry!"
    assert "reply" not in second
    assert first["verified"] is True
    assert "likes" not in first and "url" not in first
    assert result["next_cursor"] == "c2"
    assert result["complete"] is True
    assert result["credits_used"] == 1
    assert raw == json.dumps(result, ensure_ascii=False, separators=(",", ":"))


@pytest.mark.asyncio
async def test_get_reviews_last_page_has_no_cursor(tools, mock_api: respx.MockRouter):
    mock_api.get("/v1/companies/zalando.it/reviews").respond(200, json=reviews_page(["r1"]))
    result = json.loads(await tools["get_reviews"](domain="zalando.it"))
    assert "next_cursor" not in result


@pytest.mark.asyncio
async def test_list_categories(tools, mock_api: respx.MockRouter):
    mock_api.get("/v1/categories").respond(
        200,
        json={
            "data": [
                {
                    "id": "money_insurance",
                    "name": "Money & Insurance",
                    "subcategories": [{"id": "bank", "name": "Bank", "subcategories": []}],
                }
            ],
            "meta": {"credits_used": 1},
        },
    )
    result = json.loads(await tools["list_categories"]())
    assert result["categories"][0]["subcategories"] == [{"id": "bank", "name": "Bank"}]


@pytest.mark.asyncio
async def test_get_category_companies(tools, mock_api: respx.MockRouter):
    mock_api.get("/v1/categories/bank/companies", params={"country": "IT"}).respond(
        200,
        json={
            "category": {"id": "bank", "name": "Bank", "country": "IT"},
            "data": [company_summary("bank.it")],
            "meta": list_meta(1),
        },
    )
    result = json.loads(await tools["get_category_companies"](category_id="bank", country="IT"))
    assert result["category"] == {"id": "bank", "name": "Bank", "country": "IT"}
    assert result["companies"][0]["domain"] == "bank.it"


@pytest.mark.asyncio
async def test_error_becomes_tool_error(tools, mock_api: respx.MockRouter):
    mock_api.get("/v1/companies/nope.invalid").respond(
        404,
        json={"detail": {"error": "company_not_found", "message": "No Trustpilot profile"}},
    )
    with pytest.raises(ToolError, match=r"No Trustpilot profile \(company_not_found\)"):
        await tools["get_company"](domain="nope.invalid")


@pytest.mark.asyncio
async def test_rate_limit_message_has_retry(tools, mock_api: respx.MockRouter):
    mock_api.get("/v1/categories").respond(
        429,
        json={"detail": {"error": "rate_limit_exceeded", "message": "Slow down."}},
        headers={"Retry-After": "30"},
    )
    with pytest.raises(ToolError, match="Retry after 30s"):
        await tools["list_categories"]()
