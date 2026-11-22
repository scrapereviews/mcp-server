"""Tests for the async HTTP client."""

from __future__ import annotations

import pytest
import respx

from scrapereviews_mcp.client import ScrapeReviewsClient
from scrapereviews_mcp.errors import (
    AuthenticationError,
    InsufficientCreditsError,
    InvalidCursorError,
    InvalidParameterError,
    NotFoundError,
    RateLimitError,
    ScrapeReviewsError,
    UpstreamError,
)

from .payloads import company_summary, list_meta, reviews_page


@pytest.mark.asyncio
async def test_search_companies(mock_api: respx.MockRouter, client: ScrapeReviewsClient):
    route = mock_api.get(
        "/v1/companies/search", params={"query": "zalando", "limit": "5", "cursor": "c1"}
    ).respond(200, json={"data": [company_summary()], "meta": list_meta(1)})
    data = await client.search_companies("zalando", limit=5, cursor="c1")
    assert route.called
    assert data["data"][0]["domain"] == "zalando.it"


@pytest.mark.asyncio
async def test_get_company_sends_key_and_flag(
    mock_api: respx.MockRouter, client: ScrapeReviewsClient
):
    route = mock_api.get("/v1/companies/zalando.it", params={"include_similar": "true"}).respond(
        200, json={"data": company_summary(), "meta": {"credits_used": 2}}
    )
    await client.get_company("https://www.trustpilot.com/review/zalando.it", include_similar=True)
    assert route.calls.last.request.headers["X-API-Key"] == "test_key"


@pytest.mark.asyncio
async def test_get_reviews_params(mock_api: respx.MockRouter, client: ScrapeReviewsClient):
    route = mock_api.get("/v1/companies/zalando.it/reviews").respond(
        200, json=reviews_page(["r1"])
    )
    await client.get_reviews(
        "zalando.it",
        stars=[2, 1],
        language="en",
        since="2026-01-01",
        with_reply=True,
        search="refund",
        limit=10,
        cursor="abc",
    )
    assert dict(route.calls.last.request.url.params) == {
        "stars": "1,2",
        "language": "en",
        "since": "2026-01-01",
        "with_reply": "true",
        "search": "refund",
        "sort": "recent",
        "limit": "10",
        "cursor": "abc",
    }


@pytest.mark.asyncio
async def test_category_endpoints(mock_api: respx.MockRouter, client: ScrapeReviewsClient):
    mock_api.get("/v1/categories").respond(
        200, json={"data": [{"id": "bank", "name": "Bank"}], "meta": {"credits_used": 1}}
    )
    route = mock_api.get(
        "/v1/categories/bank/companies",
        params={"country": "IT", "sort": "relevant", "min_trust_score": "4.0", "limit": "20"},
    ).respond(
        200,
        json={
            "category": {"id": "bank", "name": "Bank", "country": "IT"},
            "data": [],
            "meta": list_meta(0),
        },
    )
    assert (await client.list_categories())["data"][0]["id"] == "bank"
    await client.get_category_companies("bank", "IT", min_trust_score="4.0")
    assert route.called


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "code", "exc_class"),
    [
        (400, "invalid_parameter", InvalidParameterError),
        (401, "invalid_api_key", AuthenticationError),
        (402, "insufficient_credits", InsufficientCreditsError),
        (404, "company_not_found", NotFoundError),
        (422, "invalid_cursor", InvalidCursorError),
        (429, "rate_limit_exceeded", RateLimitError),
        (503, "upstream_blocked", UpstreamError),
        (500, "internal_error", ScrapeReviewsError),
    ],
)
async def test_error_mapping(
    mock_api: respx.MockRouter, client: ScrapeReviewsClient, status, code, exc_class
):
    mock_api.get("/v1/companies/x.com").respond(
        status, json={"detail": {"error": code, "message": "Nope"}}, headers={"Retry-After": "9"}
    )
    with pytest.raises(exc_class, match="Nope") as exc_info:
        await client.get_company("x.com")
    assert type(exc_info.value) is exc_class
    assert exc_info.value.code == code
    assert exc_info.value.retry_after == 9.0
