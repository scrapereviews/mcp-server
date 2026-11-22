"""MCP tool definitions for ScrapeReviews.

Tools return compact JSON (no nulls, no logos, short keys where obvious) so that pages of
reviews fit comfortably in an agent's context.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any, Literal

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from .client import ScrapeReviewsClient
from .errors import ScrapeReviewsError


def register_tools(mcp: FastMCP, get_client: Callable[[], ScrapeReviewsClient]) -> None:
    """Register all tools on the MCP server instance.

    API errors are raised as ToolError, so the client sees a failed call (isError) with the
    API's message, not a successful result.
    """

    @mcp.tool()
    async def search_companies(query: str, limit: int = 10, cursor: str | None = None) -> str:
        """Find Trustpilot companies by name or domain; returns their domains for the other tools.

        An exact domain returns that company. Cost: 1 credit per 10 results (min 1).

        Args:
            query: Company name or domain, e.g. 'zalando' or 'zalando.it'.
            limit: Results to return, 1-50 (default 10).
            cursor: `next_cursor` from a previous call to get more results.
        """
        data = await _call(get_client().search_companies(query, limit=limit, cursor=cursor))
        return _dump(
            {
                "companies": [_summary(c) for c in data["data"]],
                **_page_meta(data["meta"]),
            }
        )

    @mcp.tool()
    async def get_company(domain: str, include_similar: bool = False) -> str:
        """Get a company's Trustpilot profile: TrustScore, review counts, star distribution,
        languages, categories, contact details, claimed status, reply rate and reply time.

        Cost: 2 credits.

        Args:
            domain: Company domain ('monzo.com'), website URL, or Trustpilot review URL.
            include_similar: Also list similar companies (default false).
        """
        data = await _call(get_client().get_company(domain, include_similar=include_similar))
        company = dict(data["data"])
        company.pop("logo_url", None)
        company["similar"] = [_summary(s) for s in company.get("similar") or []]
        return _dump({"company": company, "credits_used": data["meta"].get("credits_used")})

    @mcp.tool()
    async def get_reviews(
        domain: str,
        stars: list[int] | None = None,
        language: str = "all",
        since: str | None = None,
        until: str | None = None,
        verified: bool = False,
        with_reply: bool = False,
        search: str | None = None,
        sort: Literal["recent", "relevant"] = "recent",
        limit: int = 20,
        cursor: str | None = None,
    ) -> str:
        """Get a company's Trustpilot reviews, filtered and paginated.

        Cost: 1 credit per 5 reviews returned (min 1); 20 reviews = 4 credits. Request only
        what you need and page with `cursor`. Authors are anonymous (pseudonymous id only).

        Args:
            domain: Company domain, e.g. 'zalando.it'.
            stars: Ratings to keep, e.g. [1, 2] for negative reviews. All if omitted.
            language: 'all' (default) or an ISO 639-1 code like 'en', 'it'.
            since: Published on/after, 'YYYY-MM-DD'.
            until: Published on/before, 'YYYY-MM-DD'.
            verified: Only verified reviews.
            with_reply: Only reviews the company replied to.
            search: Full-text filter, max 100 characters.
            sort: 'recent' (default) or 'relevant'.
            limit: Reviews to return, 1-100 (default 20).
            cursor: `next_cursor` from a previous call (same filters) for the next page.
        """
        data = await _call(
            get_client().get_reviews(
                domain,
                stars=stars,
                language=language,
                since=since,
                until=until,
                verified=verified,
                with_reply=with_reply,
                search=search,
                sort=sort,
                limit=limit,
                cursor=cursor,
            )
        )
        meta = data["meta"]
        company = data["company"]
        return _dump(
            {
                "company": {
                    "domain": company["domain"],
                    "name": company["name"],
                    "trust_score": company.get("trust_score"),
                    "review_count": company.get("review_count"),
                },
                "reviews": [_review(r) for r in data["data"]],
                **_page_meta(meta),
                # False: Trustpilot's 200-per-filter cap hid some matching reviews.
                "complete": meta.get("complete"),
            }
        )

    @mcp.tool()
    async def list_categories() -> str:
        """List all Trustpilot categories (ids and names, nested) for get_category_companies.

        Cost: 1 credit. The tree is large: call it once and reuse the ids.
        """
        data = await _call(get_client().list_categories())
        return _dump({"categories": [_category(c) for c in data["data"]]})

    @mcp.tool()
    async def get_category_companies(
        category_id: str,
        country: str,
        sort: Literal["relevant", "reviews_count"] = "relevant",
        min_trust_score: Literal["3.0", "4.0", "4.5"] | None = None,
        location: str | None = None,
        limit: int = 20,
        cursor: str | None = None,
    ) -> str:
        """Rank the companies of a Trustpilot category in a country, as Trustpilot shows them.

        Cost: 1 credit per 10 companies (min 1).

        Args:
            category_id: Category id from list_categories, e.g. 'bank', 'electronics_store'.
            country: ISO 3166-1 alpha-2 country code, e.g. 'IT', 'GB', 'US'.
            sort: 'relevant' (default) or 'reviews_count'.
            min_trust_score: Only companies with at least '3.0', '4.0' or '4.5'.
            location: City, e.g. 'Milano'.
            limit: Companies to return, 1-100 (default 20).
            cursor: `next_cursor` from a previous call for the next page.
        """
        data = await _call(
            get_client().get_category_companies(
                category_id,
                country,
                sort=sort,
                min_trust_score=min_trust_score,
                location=location,
                limit=limit,
                cursor=cursor,
            )
        )
        return _dump(
            {
                "category": data["category"],
                "companies": [_summary(c) for c in data["data"]],
                **_page_meta(data["meta"]),
            }
        )


async def _call(coro: Any) -> dict[str, Any]:
    try:
        return await coro
    except ScrapeReviewsError as e:
        message = f"{e.message} ({e.code})" if e.code else e.message
        if e.retry_after:
            message += f" Retry after {int(e.retry_after)}s."
        raise ToolError(message) from e


def _summary(c: dict[str, Any]) -> dict[str, Any]:
    contact = c.get("contact") or {}
    return {
        "domain": c["domain"],
        "name": c["name"],
        "trust_score": c.get("trust_score"),
        "review_count": c.get("review_count"),
        "categories": [cat["name"] for cat in c.get("categories") or []],
        "city": contact.get("city"),
        "country": contact.get("country"),
    }


def _review(r: dict[str, Any]) -> dict[str, Any]:
    reply = r.get("reply")
    return {
        "id": r["id"],
        "rating": r["rating"],
        "title": r.get("title"),
        "text": r.get("text"),
        "language": r.get("language"),
        "published_at": r.get("published_at"),
        "verified": r.get("is_verified") or None,
        "author_id": (r.get("author") or {}).get("id"),
        "author_country": (r.get("author") or {}).get("country"),
        "likes": r.get("likes") or None,
        "reply": {"text": reply["text"], "published_at": reply.get("published_at")}
        if reply
        else None,
    }


def _category(c: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": c["id"],
        "name": c["name"],
        "subcategories": [_category(s) for s in c.get("subcategories") or []],
    }


def _page_meta(meta: dict[str, Any]) -> dict[str, Any]:
    return {
        "total": meta.get("total"),
        "next_cursor": meta.get("next_cursor"),
        "credits_used": meta.get("credits_used"),
    }


def _prune(value: Any) -> Any:
    """Drop nulls, empty strings and empty containers, recursively."""
    if isinstance(value, dict):
        pruned = {k: _prune(v) for k, v in value.items()}
        return {k: v for k, v in pruned.items() if v not in (None, "", [], {})}
    if isinstance(value, list):
        return [_prune(v) for v in value]
    return value


def _dump(value: Any) -> str:
    return json.dumps(_prune(value), ensure_ascii=False, separators=(",", ":"))
