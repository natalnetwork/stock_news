"""
stock_news.py

CLI entrypoint for the stock news alert workflow.

Supports:
- normal run (stock move check + related news + output routing)
- direct connectivity tests for SMTP/Twilio without external market/news calls
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()  # MUST be before importing modules that read env vars

from constants import (
    STOCK_ENDPOINT,
    NEWS_ENDPOINT,
    SYMBOL,
    COMPANY_NAME,
    PRICE_CHANGE_THRESHOLD_PCT,
    NEWS_TERMS,
    NEWS_LANGUAGE,
    NEWS_LIMIT,
)
from stock import StockClient
from news import NewsClient
from notifiers import EnvReader, SmsNotifier, EmailNotifier
from report_formatter import ReportFormatter


def _parse_symbols(entries: list[str] | None) -> list[tuple[str, str]]:
    """
    Parse symbol arguments into `(symbol, display_name)` tuples.

    Accepted forms:
    - `IBM`
    - `TSLA="Tesla"`

    If `entries` is omitted, the default symbol/company from constants is used.
    """
    if not entries:
        return [(SYMBOL, COMPANY_NAME)]

    parsed: list[tuple[str, str]] = []
    for raw in entries:
        entry = raw.strip()
        if not entry:
            continue

        if "=" in entry:
            symbol, alias = entry.split("=", 1)
            symbol = symbol.strip().upper()
            alias = alias.strip().strip('"').strip("'")
            if not symbol:
                raise ValueError(f"Invalid symbol entry: {raw}")
            parsed.append((symbol, alias or symbol))
        else:
            symbol = entry.upper()
            parsed.append((symbol, symbol))

    if not parsed:
        raise ValueError("--symbols was provided but no valid symbols were found.")

    return parsed


def _parse_cli() -> argparse.Namespace:
    """Define and parse CLI arguments for runtime and test modes."""
    parser = argparse.ArgumentParser(description="Stock News Alert")
    parser.add_argument(
        "--output",
        action="append",
        default=[],
        help="Output target: terminal | sms:+49123... | email:user@example.com (repeatable)",
    )
    parser.add_argument(
        "--symbols",
        nargs="+",
        help='Symbols to check, optional alias via SYMBOL="Alias". Example: --symbols TSLA="Tesla" IBM',
    )
    parser.add_argument(
        "--ignore-threshold",
        action="store_true",
        help="Fetch and output news even when the price change does not reach the alert threshold.",
    )
    parser.add_argument(
        "--send-test-email",
        metavar="ADDRESS",
        help="Send a direct SMTP test email (without stock/news API calls).",
    )
    parser.add_argument(
        "--send-test-sms",
        metavar="NUMBER",
        help="Send a direct Twilio test SMS (without stock/news API calls).",
    )
    parser.add_argument(
        "--test-message",
        default="Stock News Alert SMS test successful.",
        help="Custom message text for --send-test-sms.",
    )
    return parser.parse_args()


def _parse_outputs(raw_outputs: list[str]) -> tuple[bool, list[str], list[str]]:
    """
    Parse `--output` entries into terminal, SMS and email target groups.

    Returns:
        tuple[bool, list[str], list[str]]:
            (terminal_enabled, sms_targets, email_targets)
    """
    if not raw_outputs:
        return True, [], []

    terminal_enabled = False
    sms_targets: list[str] = []
    email_targets: list[str] = []

    for item in raw_outputs:
        value = item.strip()
        if value == "terminal":
            terminal_enabled = True
        elif value.startswith("sms:"):
            target = value[len("sms:") :].strip()
            if not target:
                raise ValueError("Empty SMS target in --output sms:...")
            sms_targets.append(target)
        elif value.startswith("email:"):
            target = value[len("email:") :].strip()
            if not target:
                raise ValueError("Empty email target in --output email:...")
            email_targets.append(target)
        else:
            raise ValueError(f"Unsupported output target: {item}")

    return terminal_enabled, sms_targets, email_targets


def main() -> None:
    """Run the CLI workflow and dispatch outputs to selected channels."""
    args = _parse_cli()

    # Direct connectivity tests (no stock/news API calls)
    if args.send_test_sms or args.send_test_email:
        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        if args.send_test_sms:
            sms_notifier = SmsNotifier.from_env()
            sms_body = f"{args.test_message} Timestamp: {now_utc}"
            sms_notifier.send_messages([sms_body], [args.send_test_sms])
            print(f"Test-SMS gesendet an {args.send_test_sms}")

        if args.send_test_email:
            email_notifier = EmailNotifier.from_env()
            subject = "Stock News Alert - SMTP Test"
            body = f"SMTP test successful.\n\nTimestamp: {now_utc}\nProject: stock-news-extrahard-start"
            email_notifier.send(subject, body, [args.send_test_email])
            print(f"Test-E-Mail gesendet an {args.send_test_email}")

        return

    # Normal workflow uses both external data sources
    av_key = EnvReader.get("ALPHAVANTAGE_KEY")
    news_key = EnvReader.get("NEWSAPI_KEY")

    if not av_key:
        raise RuntimeError("Missing ALPHAVANTAGE_KEY in environment (.env).")
    if not news_key:
        raise RuntimeError("Missing NEWSAPI_KEY in environment (.env).")

    symbol_targets = _parse_symbols(args.symbols)
    terminal_enabled, sms_targets, email_targets = _parse_outputs(args.output)
    formatter = ReportFormatter()

    # Initialize optional notifiers only when corresponding targets are present
    sms_notifier: SmsNotifier | None = None
    if sms_targets:
        try:
            sms_notifier = SmsNotifier.from_env()
        except Exception as exc:
            sms_targets = []
            if terminal_enabled:
                print(f"SMS deaktiviert ({exc})")

    email_notifier: EmailNotifier | None = None
    if email_targets:
        try:
            email_notifier = EmailNotifier.from_env()
        except Exception as exc:
            email_targets = []
            if terminal_enabled:
                print(f"E-Mail deaktiviert ({exc})")

    for symbol, company_name in symbol_targets:
        # 1) Analyze stock movement for current symbol
        try:
            stock = StockClient(
                endpoint=STOCK_ENDPOINT,
                api_key=av_key,
                symbol=symbol,
                threshold_pct=PRICE_CHANGE_THRESHOLD_PCT,
            )
            signal = stock.analyze()
        except Exception as exc:
            if terminal_enabled:
                print(f"{symbol}: could not analyze stock data ({exc})")
            continue

        # 2) Respect threshold unless explicitly overridden
        if not signal.triggered and not args.ignore_threshold:
            if terminal_enabled:
                print(f"{signal.symbol} {signal.day_old}->{signal.day_new}: {signal.change_pct:.2f}% (no alert)")
            continue

        # 3) Fetch related news; continue with empty list on retrieval issues
        try:
            news = NewsClient(endpoint=NEWS_ENDPOINT, api_key=news_key)
            articles = news.top(NEWS_TERMS + [symbol, company_name], language=NEWS_LANGUAGE, limit=NEWS_LIMIT)
        except Exception as exc:
            if terminal_enabled:
                print(f"{symbol}: could not fetch news ({exc})")
            articles = []

        # 4) Render report and dispatch to selected output channels
        report = formatter.render_report(signal, company_name, articles, PRICE_CHANGE_THRESHOLD_PCT)
        if terminal_enabled:
            print(report)

        if sms_notifier and sms_targets:
            sms_messages = formatter.build_sms_messages(signal, company_name, articles)
            try:
                sms_notifier.send_messages(sms_messages, sms_targets)
            except Exception as exc:
                if terminal_enabled:
                    print(f"{symbol}: SMS Versand fehlgeschlagen ({exc})")

        if email_notifier and email_targets:
            email_subject = f"Stock Alert: {signal.symbol} {formatter.arrow(float(signal.change_pct))} {signal.change_pct:.2f}%"
            try:
                email_notifier.send(email_subject, report, email_targets)
            except Exception as exc:
                if terminal_enabled:
                    print(f"{symbol}: E-Mail Versand fehlgeschlagen ({exc})")


if __name__ == "__main__":
    main()