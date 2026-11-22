"""MCP prompt templates for common Trustpilot review workflows."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP


def register_prompts(mcp: FastMCP) -> None:
    """Register prompt templates on the MCP server."""

    @mcp.prompt()
    async def analyze_company_reviews(domain: str, language: str | None = None) -> str:
        """Profile a company and summarize what its unhappy customers complain about.

        Args:
            domain: Company domain, e.g. 'zalando.it'
            language: ISO 639-1 code to restrict reviews to (optional)
        """
        lang = f', language="{language}"' if language else ""
        return (
            f"Analyze the Trustpilot reputation of `{domain}`.\n\n"
            f"Steps:\n"
            f"1. Call `get_company` for `{domain}` (2 credits) to get the TrustScore, review "
            f"counts, star distribution and reply behaviour.\n"
            f"2. Call `get_reviews` for `{domain}` with stars=[1, 2]{lang}, sort=\"recent\", "
            f"limit=50 (10 credits) to read the latest negative reviews.\n"
            f"3. Report:\n"
            f"   - **Overview**: TrustScore, total reviews, share of 1-2 star reviews, reply rate\n"
            f"   - **Top complaints**: 3-6 recurring themes, each with how often it appears and "
            f"one short quote\n"
            f"   - **Company response**: whether and how the company replies to complaints\n"
            f"   - **Trend**: whether complaints look recent or old, based on the dates\n"
        )

    @mcp.prompt()
    async def compare_companies(domains: str) -> str:
        """Compare the Trustpilot reputation of several companies.

        Args:
            domains: Comma-separated domains, e.g. 'monzo.com,revolut.com'
        """
        items = [d.strip() for d in domains.split(",") if d.strip()]
        listed = ", ".join(f"`{d}`" for d in items)
        return (
            f"Compare these companies on Trustpilot: {listed}.\n\n"
            f"Steps:\n"
            f"1. For each company, call `get_company` (2 credits each).\n"
            f"2. For each company, call `get_reviews` with limit=20 (4 credits each) to sample "
            f"recent reviews.\n"
            f"3. Present a comparison table (TrustScore, reviews, % 5-star, % 1-star, reply "
            f"rate, average days to reply), then the main strengths and weaknesses of each, "
            f"and which one customers seem happiest with.\n"
        )

    @mcp.prompt()
    async def find_best_companies(category: str, country: str) -> str:
        """Find the best-rated companies of a category in a country.

        Args:
            category: Category name or id, e.g. 'bank' or 'Electronics Store'
            country: ISO 3166-1 alpha-2 country code, e.g. 'IT'
        """
        return (
            f"Find the best-rated `{category}` companies in `{country}` on Trustpilot.\n\n"
            f"Steps:\n"
            f"1. If `{category}` is not a category id, call `list_categories` (1 credit) and "
            f"pick the closest id.\n"
            f"2. Call `get_category_companies` with country=\"{country}\", "
            f"min_trust_score=\"4.0\", limit=20 (2 credits).\n"
            f"3. List the top companies with TrustScore, number of reviews and city, and point "
            f"out which have few reviews (less reliable scores).\n"
        )
