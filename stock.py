"""
stock.py

Alpha Vantage stock client + analysis.

This module:
- fetches daily time series from Alpha Vantage
- picks the two newest available trading days (ISO date sorting)
- computes percent change with Decimal
- returns a StockSignal object (triggered/not triggered)
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import requests


@dataclass(frozen=True)
class StockSignal:
    """
    Result of a stock move analysis for the two newest available daily closes.
    """

    symbol: str
    day_new: str
    day_old: str
    close_new: Decimal
    close_old: Decimal
    change_pct: Decimal
    triggered: bool


class StockClient:
    """
    Alpha Vantage client for DAILY time series.
    Free API keys support daily data without intraday.

    Notes:
    - AlphaVantage returns strings for prices -> perfect for Decimal("...").
    - On rate limit or invalid request, the API often returns JSON with
      keys like "Note" or "Error Message".
    """

    def __init__(
        self, endpoint: str, api_key: str, symbol: str, threshold_pct: Decimal
    ):
        """
        Initialize the stock client.

        Args:
            endpoint: Alpha Vantage API base endpoint.
            api_key: Alpha Vantage API key.
            symbol: Stock ticker to analyze (e.g. TSLA).
            threshold_pct: Absolute move threshold in percent to trigger alerts.
        """
        if not api_key:
            raise RuntimeError("Missing AlphaVantage API key (ALPHAVANTAGE_KEY).")
        self.endpoint = endpoint
        self.api_key = api_key
        self.symbol = symbol
        self.threshold_pct = threshold_pct

    def fetch_daily(self) -> dict:
        """
        Fetch Alpha Vantage TIME_SERIES_DAILY JSON.

        Returns:
            dict: Raw Alpha Vantage JSON response.

        Raises:
            requests.HTTPError: Network / HTTP issues.
        """
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": self.symbol,
            "apikey": self.api_key,
        }
        r = requests.get(self.endpoint, params=params, timeout=20)
        r.raise_for_status()
        return r.json()

    @staticmethod
    def _latest_two_days(ts: dict) -> tuple[str, str]:
        """
        Return newest and previous trading day keys from a time series dict.

        Args:
            ts: "Time Series (Daily)" section from Alpha Vantage response.

        Returns:
            tuple[str, str]: (newest_day, previous_day)

        Raises:
            ValueError: If fewer than 2 daily data points exist.
        """
        days = sorted(ts.keys(), reverse=True)  # ISO dates sort correctly
        if len(days) < 2:
            raise ValueError("Not enough daily data points in Time Series (Daily).")
        return days[0], days[1]

    def analyze(self) -> StockSignal:
        """
        Compute percent change between the two newest daily closes.

        Returns:
            StockSignal: Analysis result for newest vs previous close.

        Raises:
            ValueError: If response does not contain daily series.
            ZeroDivisionError: If previous close is zero.
        """
        data = self.fetch_daily()

        if "Time Series (Daily)" not in data:
            msg = data.get("Note") or data.get("Error Message") or str(data)
            raise ValueError(f"AlphaVantage returned no daily series. Response: {msg}")

        ts = data["Time Series (Daily)"]
        d_new, d_old = self._latest_two_days(ts)

        c_new = Decimal(ts[d_new]["4. close"])
        c_old = Decimal(ts[d_old]["4. close"])
        if c_old == 0:
            raise ZeroDivisionError(
                "Previous close is 0; cannot compute percentage change."
            )

        change_pct = (c_new - c_old) / c_old * Decimal("100")
        triggered = abs(change_pct) >= self.threshold_pct

        return StockSignal(
            symbol=self.symbol,
            day_new=d_new,
            day_old=d_old,
            close_new=c_new,
            close_old=c_old,
            change_pct=change_pct,
            triggered=triggered,
        )
