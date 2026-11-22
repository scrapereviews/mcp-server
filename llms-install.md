# Installing the ScrapeReviews MCP server (for AI agents)

The server runs locally over stdio and is published on PyPI as `scrapereviews-mcp`.

## 1. Requirements

- `uv` (provides `uvx`): `curl -LsSf https://astral.sh/uv/install.sh | sh` (or `brew install uv`). Alternatively Python 3.10+ and `pip install scrapereviews-mcp`.
- A ScrapeReviews API key. Ask the user for it; they can create one for free (100 credits/month) at https://scrapereviews.com. Never invent a key.

## 2. MCP client configuration

Add this server to the client's MCP settings (for Cline: `cline_mcp_settings.json`), replacing the key:

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

Without uv, use `"command": "scrapereviews-mcp"` after `pip install scrapereviews-mcp`.

## 3. Check it works

After the client restarts the server it should list 5 tools: `search_companies`, `get_company`, `get_reviews`, `list_categories`, `get_category_companies`. Try `get_company` with `domain` `monzo.com` (2 credits).

An `invalid_api_key` error means the key is wrong or revoked; `insufficient_credits` means the credits are used up (top up at https://scrapereviews.com).
