"""Shared fixtures for MCP server tests."""

from __future__ import annotations

import pytest
import respx

from scrapereviews_mcp.client import ScrapeReviewsClient

BASE_URL = "https://api.test.scrapereviews.com"


@pytest.fixture
def mock_api():
    """respx mock router scoped to the test base URL."""
    with respx.mock(base_url=BASE_URL) as router:
        yield router


@pytest.fixture
def client():
    """ScrapeReviewsClient pointed at the mocked base URL."""
    return ScrapeReviewsClient(api_key="test_key", base_url=BASE_URL)
