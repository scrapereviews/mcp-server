# ScrapeReviews MCP Server

<!-- mcp-name: com.scrapereviews/scrapereviews -->

An [MCP](https://modelcontextprotocol.io) server that gives AI assistants (Claude Desktop, Cursor, etc.) access to Trustpilot company profiles, reviews and category rankings via the [ScrapeReviews](https://scrapereviews.com) API.

## Features

**5 Tools** — search companies, company profile, filtered reviews, category tree, category rankings

**4 Documentation Resources** — API reference, quickstart guide, pricing, workflow examples

**3 Prompt Templates** — analyze company reviews, compare companies, find best companies in a category

Tool results are compact JSON (nulls and logos dropped) and always include `credits_used`.

## Quick Start

### 1. Get an API Key

Sign up at [scrapereviews.com](https://scrapereviews.com) and create an API key from the dashboard (100 free credits every month).

### 2. Configure Claude Desktop

Add to your `claude_desktop_config.json`:

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

### 3. Use it

Ask Claude:
- "What do customers complain about on Trustpilot for zalando.it?"
- "Compare monzo.com and revolut.com on Trustpilot"
- "Which banks in Italy have a TrustScore above 4?"

## Configuration for Other Clients

### Cursor

Add to `.cursor/mcp.json`:

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

### Claude Code

```bash
claude mcp add scrapereviews -e SCRAPEREVIEWS_API_KEY=your_api_key -- uvx scrapereviews-mcp
```

## Installation Alternatives

### pip

```bash
pip install scrapereviews-mcp
SCRAPEREVIEWS_API_KEY=... scrapereviews-mcp
```

### npx

```bash
SCRAPEREVIEWS_API_KEY=... npx scrapereviews-mcp
```

### Docker

```bash
docker build -t scrapereviews-mcp . && docker run -i --rm -e SCRAPEREVIEWS_API_KEY=... scrapereviews-mcp
```

## Tools

| Tool | Description | Cost |
|------|-------------|------|
| `search_companies` | Find companies by name or domain | 1 credit / 10 results |
| `get_company` | Profile: TrustScore, star distribution, reply rate, contacts | 2 credits |
| `get_reviews` | Reviews filtered by stars, language, dates, verified, reply, text; cursor pagination | 1 credit / 5 reviews |
| `list_categories` | Trustpilot category tree | 1 credit |
| `get_category_companies` | Company ranking of a category in a country | 1 credit / 10 companies |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SCRAPEREVIEWS_API_KEY` | Yes | Your API key |
| `SCRAPEREVIEWS_BASE_URL` | No | Override API base URL (default: `https://api.scrapereviews.com`) |

## Development

```bash
uv venv -p 3.12 && uv pip install -e ".[dev]"
.venv/bin/pytest
```

Test with MCP Inspector:

```bash
SCRAPEREVIEWS_API_KEY=... mcp dev dev_server.py
```

## License

MIT
