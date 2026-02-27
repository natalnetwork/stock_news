"""
constants.py

Project-wide constants (configuration knobs).
No secrets should be hardcoded here.

- Keep API keys in .env / environment variables.
- Keep only stable configuration values here.
"""

from decimal import Decimal

# External API endpoints
STOCK_ENDPOINT = "https://www.alphavantage.co/query"
NEWS_ENDPOINT = "https://newsapi.org/v2/everything"

# Stock settings
SYMBOL = "TSLA"

# Alert threshold: absolute percent move between two newest trading days
PRICE_CHANGE_THRESHOLD_PCT = Decimal("5")

# News settings
NEWS_LANGUAGE = "en"
NEWS_LIMIT = 3

# Single source of truth for news relevance:
# - used to build the NewsAPI query (" OR " join)
# - used for post-filtering in Python (case-insensitive)
NEWS_TERMS = ["tesla", "tsla"]
