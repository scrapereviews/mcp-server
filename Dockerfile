# Runs the ScrapeReviews MCP server over stdio (for registries' automated checks and container use).
# Usage: docker run -i --rm -e SCRAPEREVIEWS_API_KEY=... scrapereviews-mcp
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir .
ENTRYPOINT ["scrapereviews-mcp"]
