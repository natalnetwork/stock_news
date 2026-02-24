"""
stock_news.py

CLI entrypoint for the stock news alert workflow.

Supports:
- normal run (stock move check + related news + output routing)
- direct connectivity tests for SMTP/Twilio without external market/news calls
"""

from __future__ import annotations

from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()  # MUST be before importing modules that read env vars

from notifiers import EnvReader, SmsNotifier, EmailNotifier
from cli_parser import parse_cli, parse_outputs, parse_symbols
from alert_service import AlertService


def main() -> None:
    """Run the CLI workflow and dispatch outputs to selected channels."""
    args = parse_cli()

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

    symbol_targets = parse_symbols(args.symbols)
    outputs = parse_outputs(args.output)

    service = AlertService(
        av_key=av_key,
        news_key=news_key,
        outputs=outputs,
        ignore_threshold=args.ignore_threshold,
    )
    service.run(symbol_targets)


if __name__ == "__main__":
    main()