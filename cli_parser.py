"""
cli_parser.py

Central CLI parsing utilities for stock_news.
"""

from __future__ import annotations

import argparse

from app_types import OutputTargets, SymbolTargets
from constants import SYMBOL, COMPANY_NAME


def parse_symbols(entries: list[str] | None) -> SymbolTargets:
    """
    Parse symbol arguments into `(symbol, display_name)` tuples.

    Accepted forms:
    - `IBM`
    - `TSLA="Tesla"`

    If `entries` is omitted, the default symbol/company from constants is used.
    """
    if not entries:
        return [(SYMBOL, COMPANY_NAME)]

    parsed: SymbolTargets = []
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


def parse_cli() -> argparse.Namespace:
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


def parse_outputs(raw_outputs: list[str]) -> OutputTargets:
    """
    Parse `--output` entries into terminal, SMS and email target groups.

    Returns:
        OutputTargets: normalized output routing config.
    """
    if not raw_outputs:
        return OutputTargets(terminal_enabled=True, sms_targets=[], email_targets=[])

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

    return OutputTargets(
        terminal_enabled=terminal_enabled,
        sms_targets=sms_targets,
        email_targets=email_targets,
    )
