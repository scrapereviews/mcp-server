"""Error mapping from HTTP responses to domain-specific exceptions."""

from __future__ import annotations

import httpx


class ScrapeReviewsError(Exception):
    """Base error for the ScrapeReviews API."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        code: str | None = None,
        retry_after: float | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.code = code
        self.retry_after = retry_after
        super().__init__(message)


class InvalidParameterError(ScrapeReviewsError):
    """A parameter was rejected (bad domain, stars, language, date...)."""


class AuthenticationError(ScrapeReviewsError):
    """Missing or invalid API key."""


class InsufficientCreditsError(ScrapeReviewsError):
    """The credit balance is empty."""


class NotFoundError(ScrapeReviewsError):
    """Company or category not found."""


class InvalidCursorError(ScrapeReviewsError):
    """The cursor is malformed or was made for other filters."""


class RateLimitError(ScrapeReviewsError):
    """Too many requests."""


class UpstreamError(ScrapeReviewsError):
    """Trustpilot is unreachable, blocking, slow, or changed its pages."""


_ERROR_MAP: dict[str, type[ScrapeReviewsError]] = {
    "invalid_parameter": InvalidParameterError,
    "missing_api_key": AuthenticationError,
    "invalid_api_key": AuthenticationError,
    "insufficient_credits": InsufficientCreditsError,
    "insufficient_credits_retry_later": InsufficientCreditsError,
    "company_not_found": NotFoundError,
    "category_not_found": NotFoundError,
    "invalid_cursor": InvalidCursorError,
    "rate_limit_exceeded": RateLimitError,
    "upstream_changed": UpstreamError,
    "upstream_blocked": UpstreamError,
    "upstream_error": UpstreamError,
    "upstream_timeout": UpstreamError,
}

_STATUS_MAP: dict[int, type[ScrapeReviewsError]] = {
    400: InvalidParameterError,
    401: AuthenticationError,
    402: InsufficientCreditsError,
    404: NotFoundError,
    422: InvalidCursorError,
    429: RateLimitError,
    502: UpstreamError,
    503: UpstreamError,
    504: UpstreamError,
}


def raise_for_status(response: httpx.Response) -> None:
    """Raise a domain-specific exception if the response indicates an error."""
    if response.is_success:
        return

    message = f"HTTP {response.status_code}"
    code: str | None = None
    try:
        body = response.json()
    except ValueError:
        body = None
        message = response.text or message
    # FastAPI error format: {"detail": {"error": "<code>", "message": "..."}}
    detail = body.get("detail") if isinstance(body, dict) else None
    if isinstance(detail, dict):
        code = detail.get("error")
        message = detail.get("message", message)
    elif isinstance(detail, str):
        message = detail

    retry_after: float | None = None
    header = response.headers.get("retry-after")
    if header and header.isdigit():
        retry_after = float(header)

    exc_class = _ERROR_MAP.get(code or "") or _STATUS_MAP.get(response.status_code)
    raise (exc_class or ScrapeReviewsError)(
        message, status_code=response.status_code, code=code, retry_after=retry_after
    )
