"""Sample API payloads shared by the tests."""

from __future__ import annotations

from typing import Any


def company_summary(domain: str = "zalando.it") -> dict[str, Any]:
    return {
        "id": "4e80",
        "domain": domain,
        "name": "Zalando",
        "trust_score": 1.9,
        "stars": 2.0,
        "review_count": 13683,
        "logo_url": "https://example.com/logo.png",
        "categories": [{"id": "shoe_store", "name": "Shoe Store", "is_primary": False}],
        "contact": {"website": "https://zalando.it", "city": "Berlin", "country": "Germany"},
        "trustpilot_url": f"https://www.trustpilot.com/review/{domain}",
    }


def review(review_id: str, rating: int = 1, reply: bool = False) -> dict[str, Any]:
    return {
        "id": review_id,
        "rating": rating,
        "title": "Never arrived",
        "text": "Waited three weeks, no refund.",
        "language": "en",
        "experienced_at": None,
        "published_at": "2026-11-20T01:05:15.000Z",
        "updated_at": None,
        "is_verified": True,
        "verification_source": "invitation",
        "source": "Organic",
        "likes": 0,
        "author": {"id": "u_1", "country": "GB", "review_count": 2, "is_verified": False},
        "reply": {"text": "Sorry!", "published_at": "2026-11-21T00:00:00Z", "updated_at": None}
        if reply
        else None,
        "url": f"https://www.trustpilot.com/reviews/{review_id}",
    }


def reviews_page(ids: list[str], next_cursor: str | None = None) -> dict[str, Any]:
    return {
        "company": {
            "id": "4e80",
            "domain": "zalando.it",
            "name": "Zalando",
            "trust_score": 1.9,
            "review_count": 13683,
            "trustpilot_url": "https://www.trustpilot.com/review/zalando.it",
        },
        "data": [review(i, reply=(n == 0)) for n, i in enumerate(ids)],
        "meta": {
            "credits_used": 1,
            "cache_hit": False,
            "count": len(ids),
            "total": 500,
            "has_more": next_cursor is not None,
            "next_cursor": next_cursor,
            "complete": True,
        },
    }


def list_meta(count: int, next_cursor: str | None = None) -> dict[str, Any]:
    return {
        "credits_used": 1,
        "cache_hit": False,
        "count": count,
        "total": count,
        "has_more": next_cursor is not None,
        "next_cursor": next_cursor,
    }
