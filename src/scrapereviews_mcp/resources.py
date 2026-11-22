"""MCP resource definitions — static documentation exposed to AI clients."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP


def register_resources(mcp: FastMCP) -> None:
    """Register documentation resources on the MCP server."""

    @mcp.resource("scrapereviews://docs/api-reference")
    async def api_reference() -> str:
        """ScrapeReviews REST API reference."""
        return API_REFERENCE

    @mcp.resource("scrapereviews://docs/quickstart")
    async def quickstart() -> str:
        """Getting started with the ScrapeReviews MCP server."""
        return QUICKSTART

    @mcp.resource("scrapereviews://docs/pricing")
    async def pricing() -> str:
        """ScrapeReviews pricing and credit costs."""
        return PRICING

    @mcp.resource("scrapereviews://docs/examples")
    async def examples() -> str:
        """Common workflow examples."""
        return EXAMPLES


# ---------------------------------------------------------------------------
# Static content
# ---------------------------------------------------------------------------

API_REFERENCE = """\
# ScrapeReviews API Reference

Base URL: `https://api.scrapereviews.com`

Authentication: `X-API-Key: <key>` header or `Authorization: Bearer <key>`.
Every successful response carries `X-Credits-Used`. Failed calls cost 0 credits.

Lists are paginated with cursors: pass `meta.next_cursor` as `cursor` (with the same filters)
to get the next page. `meta` also holds `credits_used`, `cache_hit`, `count`, `total`,
`has_more`.

---

## Companies

### GET /v1/companies/search
| Parameter | Default | Description |
|-----------|---------|-------------|
| query     | —       | Company name or domain (an exact domain returns that company) |
| limit     | 10      | 1–50 |
| cursor    | —       | Next page |

Response: `data` (CompanySummary[]), `meta`. Cost: 1 credit per 10 results (min 1).

### GET /v1/companies/{domain}
`domain` accepts `example.com`, `www.example.com`, a website URL or a Trustpilot URL.
Redirects to the canonical Trustpilot domain are followed.

| Parameter       | Default | Description |
|-----------------|---------|-------------|
| include_similar | false   | Add similar companies |

Response `data`: `domain`, `name`, `website`, `trust_score`, `stars`, `review_count`,
`review_count_last_12_months`, `star_distribution` (one…five), `languages`
(`{language, count}`), `categories`, `description`, `country`, `contact`, `is_claimed`,
`claimed_at`, `is_closed`, `is_temporarily_closed`, `reply_behavior` (`reply_rate`,
`average_days_to_reply`, …), `verified`, `consumer_alert`, `similar`, `trustpilot_url`.
Cost: 2 credits.

### GET /v1/companies/{domain}/reviews
| Parameter  | Default  | Description |
|------------|----------|-------------|
| stars      | all      | Comma-separated, e.g. `1,2` |
| language   | `all`    | `all` or ISO 639-1 |
| since      | —        | Published on/after (`YYYY-MM-DD` or ISO 8601) |
| until      | —        | Published on/before |
| verified   | false    | Only verified reviews |
| with_reply | false    | Only reviews with a company reply |
| search     | —        | Full-text filter (≤100 chars) |
| sort       | `recent` | `recent` or `relevant` |
| limit      | 20       | 1–100 (lowered if the balance cannot pay for it) |
| cursor     | —        | Next page |

Response: `company` (`domain`, `name`, `trust_score`, `review_count`), `data` (Review[]),
`meta` (+ `complete`). Review: `id`, `rating`, `title`, `text`, `language`, `experienced_at`,
`published_at`, `is_verified`, `source`, `likes`, `author` (`id` pseudonymous, `country`),
`reply` (`text`, `published_at`) or null, `url`.
Cost: 1 credit per 5 reviews returned (min 1).

Coverage: Trustpilot shows at most 200 reviews per filter combination. The API splits the
query by star rating and language to go further; `meta.complete` is false when a single
(star, language) slice still holds more than 200 reviews. Split results come grouped by star
rating (5 → 1) and language.

---

## Categories

### GET /v1/categories
Category tree: `data` (`{id, name, subcategories}`[]). Cost: 1 credit.

### GET /v1/categories/{category_id}/companies
| Parameter       | Default    | Description |
|-----------------|------------|-------------|
| country         | —          | ISO 3166-1 alpha-2, required |
| sort            | `relevant` | `relevant` or `reviews_count` |
| min_trust_score | —          | `3.0`, `4.0` or `4.5` |
| location        | —          | City, e.g. `Milano` |
| limit           | 20         | 1–100 |
| cursor          | —          | Next page |

Response: `category` (`id`, `name`, `country`), `data` (CompanySummary[]), `meta`.
Cost: 1 credit per 10 companies (min 1).

---

## Error Codes

Error body: `{"detail": {"error": "<code>", "message": "<text>"}}`.

| HTTP | Code | Meaning |
|------|------|---------|
| 400 | `invalid_parameter` | Bad domain, stars, language, date, missing query… |
| 401 | `missing_api_key` / `invalid_api_key` | |
| 402 | `insufficient_credits` | Balance is 0 |
| 404 | `company_not_found` / `category_not_found` | |
| 422 | `invalid_cursor` | Malformed, tampered, or made for other filters |
| 429 | `rate_limit_exceeded` / `insufficient_credits_retry_later` | `Retry-After` set |
| 502 | `upstream_changed` | Trustpilot changed its page format |
| 503 | `upstream_blocked` / `upstream_error` | Trustpilot unreachable or blocking |
| 504 | `upstream_timeout` | |
| 500 | `internal_error` | |
"""

QUICKSTART = """\
# ScrapeReviews MCP — Quick Start

## 1. Get an API Key

Sign up at https://scrapereviews.com and create an API key from the dashboard.
New accounts get 100 free credits every month.

## 2. Configure your MCP client

### Claude Desktop / Claude Code / Cursor

```json
{
  "mcpServers": {
    "scrapereviews": {
      "command": "uvx",
      "args": ["scrapereviews-mcp"],
      "env": {
        "SCRAPEREVIEWS_API_KEY": "your_api_key"
      }
    }
  }
}
```

## 3. Try it out

Ask your AI assistant:
- "What do customers complain about on Trustpilot for zalando.it?"
- "Compare monzo.com and revolut.com on Trustpilot"
- "Which banks in Italy have a TrustScore above 4?"

## Alternatives

```bash
npx scrapereviews-mcp
pip install scrapereviews-mcp && scrapereviews-mcp
```

Set `SCRAPEREVIEWS_API_KEY` as an environment variable.
"""

PRICING = """\
# ScrapeReviews Pricing

1 credit = $0.001. Only successful calls are billed; failed calls cost 0 credits.

## Free Tier
- **100 credits every month**, no credit card required

## Credit Packs (never expire)
- 10,000 credits — $9
- 100,000 credits — $80
- 1,000,000 credits — $700
- 10,000,000 credits — $5,000

## Cost per Call
| Call | Credits |
|------|---------|
| Reviews (`get_reviews`) | 1 per 5 reviews (min 1) — $0.20 per 1,000 reviews |
| Company profile (`get_company`) | 2 |
| Search (`search_companies`) | 1 per 10 results (min 1) |
| Category companies (`get_category_companies`) | 1 per 10 companies (min 1) |
| Category tree (`list_categories`) | 1 |

Every tool result includes `credits_used`.
"""

EXAMPLES = """\
# ScrapeReviews — Common Workflows

## Analyze complaints about a company
1. `get_company` for the profile, star distribution and reply rate
2. `get_reviews` with `stars=[1, 2]`, `sort="recent"`, `limit=50`
3. Group the reviews into recurring themes

## Track recent sentiment
1. `get_reviews` with `since="YYYY-MM-DD"` (e.g. the last 30 days) and `limit=100`
2. Page with `cursor` while `next_cursor` is present
3. Compare the rating mix with the all-time `star_distribution` from `get_company`

## Check how a company handles complaints
1. `get_company` → `reply_behavior` (reply rate, average days to reply)
2. `get_reviews` with `stars=[1]`, `with_reply=true` to read the replies

## Find a company when only the name is known
1. `search_companies` with the name
2. Use the returned `domain` with the other tools

## Find the best companies in a market
1. `list_categories` once to get category ids
2. `get_category_companies` with `country` and `min_trust_score="4.0"`

## Search reviews for a topic
1. `get_reviews` with `search="refund"` (or any keyword) and optional `language`
"""
