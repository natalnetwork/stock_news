"""
news.py

NewsAPI client with:
- query generation from terms (joined by OR)
- optional searchIn restriction (title,description)
- post-filtering to keep results strongly related to the company/stock
"""

from __future__ import annotations

import requests


class NewsClient:
    """
    Minimal wrapper around NewsAPI /v2/everything.

    Strategy:
    - Build an OR query from `terms` (e.g. "tesla OR tsla").
    - Fetch more than needed (pageSize=20) then post-filter.
    """

    def __init__(self, endpoint: str, api_key: str):
        """
        Initialize the news client.

        Args:
            endpoint: NewsAPI /v2/everything endpoint.
            api_key: NewsAPI key.
        """
        if not api_key:
            raise RuntimeError("Missing NewsAPI key (NEWSAPI_KEY).")
        self.endpoint = endpoint
        self.api_key = api_key

    @staticmethod
    def build_query(terms: list[str]) -> str:
        """
        Build an OR query for NewsAPI.
        Terms with spaces get quoted.

        Args:
            terms: Search terms used to build the NewsAPI query.

        Returns:
            str: Query string joined with OR.

        Raises:
            ValueError: If no usable search terms are provided.
        """
        parts = []
        for t in terms:
            t = t.strip()
            if not t:
                continue
            parts.append(f'"{t}"' if " " in t else t)

        if not parts:
            raise ValueError("No NEWS_TERMS provided.")
        return " OR ".join(parts)

    def top(self, terms: list[str], *, language: str = "en", limit: int = 3) -> list[dict]:
        """
        Return up to `limit` articles matching `terms`.

        - Uses `searchIn=title,description` to reduce noise.
        - Post-filters by checking any term appears in title/description.

        Args:
            terms: Terms used for NewsAPI query and local relevance filter.
            language: Language code for NewsAPI search.
            limit: Maximum number of articles returned.

        Returns:
            list[dict]: NewsAPI article dicts

        Raises:
            requests.HTTPError: On network/HTTP problems.
        """
        query = self.build_query(terms)

        params = {
            "q": query,
            "searchIn": "title,description",
            "sortBy": "publishedAt",
            "language": language,
            "pageSize": 20,  # fetch more, then filter
            "apiKey": self.api_key,
        }

        r = requests.get(self.endpoint, params=params, timeout=20)
        r.raise_for_status()
        payload = r.json()

        articles = payload.get("articles", [])

        terms_l = [t.lower() for t in terms if t.strip()]
        filtered: list[dict] = []

        for a in articles:
            title = (a.get("title") or "").lower()
            desc = (a.get("description") or "").lower()

            if any(t in title or t in desc for t in terms_l):
                filtered.append(a)

            if len(filtered) >= limit:
                break

        return filtered