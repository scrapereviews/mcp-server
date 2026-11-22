"""ScrapeReviews MCP Server entry point."""

from __future__ import annotations

import os
import sys

from mcp.server.fastmcp import FastMCP

from .client import DEFAULT_BASE_URL, ScrapeReviewsClient
from .prompts import register_prompts
from .resources import register_resources
from .tools import register_tools

mcp = FastMCP(
    "ScrapeReviews",
    instructions=(
        "Trustpilot data via the ScrapeReviews API: find companies (search_companies), read "
        "their profile (get_company) and reviews (get_reviews, filterable by stars, language, "
        "dates, text), and browse category rankings (list_categories, "
        "get_category_companies). Every call costs credits, stated in each tool; results "
        "include credits_used. Lists return next_cursor only when more results exist."
    ),
)

# Lazy-init client so import doesn't fail without env var (tests, --help, etc.)
_client: ScrapeReviewsClient | None = None


def _get_client() -> ScrapeReviewsClient:
    global _client
    if _client is None:
        api_key = os.environ.get("SCRAPEREVIEWS_API_KEY", "")
        if not api_key:
            print(
                "Error: SCRAPEREVIEWS_API_KEY environment variable is required.\n"
                "Get your API key at https://scrapereviews.com",
                file=sys.stderr,
            )
            sys.exit(1)
        base_url = os.environ.get("SCRAPEREVIEWS_BASE_URL", DEFAULT_BASE_URL)
        _client = ScrapeReviewsClient(api_key=api_key, base_url=base_url)
    return _client


# Register components — tools get a lazy client reference
register_tools(mcp, _get_client)
register_resources(mcp)
register_prompts(mcp)


def main() -> None:
    """Run the MCP server (stdio transport)."""
    # Force client init to fail fast if key is missing
    _get_client()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
