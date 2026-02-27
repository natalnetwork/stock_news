"""
alert_service.py

Service layer for the stock-news alert workflow.

This module encapsulates per-symbol processing:
- stock move analysis
- optional news fetch
- report rendering
- SMS/email dispatch
"""

from __future__ import annotations

from app_types import OutputTargets, SymbolTargets
from constants import (
    STOCK_ENDPOINT,
    NEWS_ENDPOINT,
    PRICE_CHANGE_THRESHOLD_PCT,
    NEWS_TERMS,
    NEWS_LANGUAGE,
    NEWS_LIMIT,
)
from stock import StockClient
from news import NewsClient
from notifiers import SmsNotifier, EmailNotifier
from report_formatter import ReportFormatter


class AlertService:
    """Run stock alert processing and deliver results to configured outputs."""

    def __init__(
        self,
        *,
        av_key: str,
        news_key: str,
        outputs: OutputTargets,
        ignore_threshold: bool,
    ):
        self.av_key = av_key
        self.news_key = news_key
        self.terminal_enabled = outputs.terminal_enabled
        self.sms_targets = outputs.sms_targets
        self.email_targets = outputs.email_targets
        self.ignore_threshold = ignore_threshold
        self.formatter = ReportFormatter()

        self.sms_notifier: SmsNotifier | None = None
        if self.sms_targets:
            try:
                self.sms_notifier = SmsNotifier.from_env()
            except Exception as exc:
                self.sms_targets = []
                if self.terminal_enabled:
                    print(f"SMS deaktiviert ({exc})")

        self.email_notifier: EmailNotifier | None = None
        if self.email_targets:
            try:
                self.email_notifier = EmailNotifier.from_env()
            except Exception as exc:
                self.email_targets = []
                if self.terminal_enabled:
                    print(f"E-Mail deaktiviert ({exc})")

    def run(self, symbol_targets: SymbolTargets) -> None:
        """Process all symbols and dispatch alerts to terminal/SMS/email outputs."""
        for symbol in symbol_targets:
            self._process_symbol(symbol)

    def _process_symbol(self, symbol: str) -> None:
        """Run stock + news flow for one symbol and send configured outputs."""
        try:
            stock = StockClient(
                endpoint=STOCK_ENDPOINT,
                api_key=self.av_key,
                symbol=symbol,
                threshold_pct=PRICE_CHANGE_THRESHOLD_PCT,
            )
            signal = stock.analyze()
        except Exception as exc:
            if self.terminal_enabled:
                print(f"{symbol}: could not analyze stock data ({exc})")
            return

        if not signal.triggered and not self.ignore_threshold:
            if self.terminal_enabled:
                print(
                    f"{signal.symbol} {signal.day_old}->{signal.day_new}: {signal.change_pct:.2f}% (no alert)"
                )
            return

        try:
            news = NewsClient(endpoint=NEWS_ENDPOINT, api_key=self.news_key)
            articles = news.top(
                NEWS_TERMS + [symbol],
                language=NEWS_LANGUAGE,
                limit=NEWS_LIMIT,
            )
        except Exception as exc:
            if self.terminal_enabled:
                print(f"{symbol}: could not fetch news ({exc})")
            articles = []

        report = self.formatter.render_report(
            signal, articles, PRICE_CHANGE_THRESHOLD_PCT
        )
        if self.terminal_enabled:
            print(report)

        if self.sms_notifier and self.sms_targets:
            sms_messages = self.formatter.build_sms_messages(signal, articles)
            try:
                self.sms_notifier.send_messages(sms_messages, self.sms_targets)
            except Exception as exc:
                if self.terminal_enabled:
                    print(f"{symbol}: SMS Versand fehlgeschlagen ({exc})")

        if self.email_notifier and self.email_targets:
            email_subject = (
                f"Stock Alert: {signal.symbol} {self.formatter.arrow(float(signal.change_pct))} "
                f"{signal.change_pct:.2f}%"
            )
            try:
                self.email_notifier.send(email_subject, report, self.email_targets)
            except Exception as exc:
                if self.terminal_enabled:
                    print(f"{symbol}: E-Mail Versand fehlgeschlagen ({exc})")
