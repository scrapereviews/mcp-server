"""Async HTTP client for the ScrapeReviews REST API."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote, urlparse

import httpx

from . import __version__
from .errors import raise_for_status

DEFAULT_BASE_URL = "https://api.scrapereviews.com"
DEFAULT_TIMEOUT = 60.0


class ScrapeReviewsClient:
    """Async wrapper around the ScrapeReviews REST API. Methods return the raw JSON body."""

    def __init__(self, api_key: str, base_url: str = DEFAULT_BASE_URL):
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            headers={
                "X-API-Key": api_key,
                "Accept": "application/json",
                "User-Agent": f"ScrapeReviews-MCP/{__version__}",
            },
            timeout=DEFAULT_TIMEOUT,
        )

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        clean = {
            k: ("true" if v is True else v)
            for k, v in (params or {}).items()
            if v is not None and v is not False
        }
        response = await self._client.get(path, params=clean)
        raise_for_status(response)
        return response.json()

    # -- Companies --

    async def search_companies(
        self, query: str, limit: int = 10, cursor: str | None = None
    ) -> dict[str, Any]:
        return await self._get(
            "/v1/companies/search", {"query": query, "limit": limit, "cursor": cursor}
        )

    async def get_company(self, domain: str, include_similar: bool = False) -> dict[str, Any]:
        return await self._get(
            f"/v1/companies/{_domain_path(domain)}", {"include_similar": include_similar}
        )

    async def get_reviews(
        self,
        domain: str,
        stars: list[int] | None = None,
        language: str = "all",
        since: str | None = None,
        until: str | None = None,
        verified: bool = False,
        with_reply: bool = False,
        search: str | None = None,
        sort: str = "recent",
        limit: int = 20,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        params = {
            "stars": ",".join(str(s) for s in sorted(stars)) if stars else None,
            "language": None if language == "all" else language,
            "since": since,
            "until": until,
            "verified": verified,
            "with_reply": with_reply,
            "search": search,
            "sort": sort,
            "limit": limit,
            "cursor": cursor,
        }
        return await self._get(f"/v1/companies/{_domain_path(domain)}/reviews", params)

    # -- Categories --

    async def list_categories(self) -> dict[str, Any]:
        return await self._get("/v1/categories")

    async def get_category_companies(
        self,
        category_id: str,
        country: str,
        sort: str = "relevant",
        min_trust_score: str | None = None,
        location: str | None = None,
        limit: int = 20,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        params = {
            "country": country,
            "sort": sort,
            "min_trust_score": min_trust_score,
            "location": location,
            "limit": limit,
            "cursor": cursor,
        }
        category = quote(category_id.strip(), safe="")
        return await self._get(f"/v1/categories/{category}/companies", params)

    async def close(self) -> None:
        await self._client.aclose()


def _domain_path(domain: str) -> str:
    """Reduce a website or Trustpilot URL to its domain (a slash cannot travel in a path)."""
    value = domain.strip()
    if "://" in value:
        parsed = urlparse(value)
        host = parsed.hostname or ""
        if host.endswith("trustpilot.com") and parsed.path.startswith("/review/"):
            value = parsed.path.split("/review/", 1)[1]
        else:
            value = host
    return quote(value.split("/")[0].split("?")[0].split("#")[0], safe="")
