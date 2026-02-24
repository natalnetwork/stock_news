"""
report_formatter.py

Formatting utilities for terminal/email reports and compact SMS texts.
"""

from __future__ import annotations

from datetime import datetime, timezone


class ReportFormatter:
    """Create human-readable alert content for different output channels."""

    @staticmethod
    def arrow(pct: float) -> str:
        """Return up/down arrow icon for a percentage move."""
        return "🔺" if pct > 0 else "🔻"

    @staticmethod
    def truncate(text: str | None, n: int = 140) -> str:
        """Normalize whitespace and cut long strings for compact output."""
        if not text:
            return "-"
        text = " ".join(text.split())
        return text if len(text) <= n else text[: n - 1] + "…"

    @staticmethod
    def fmt_iso_z(dt_str: str | None) -> str:
        """Convert ISO UTC timestamps to a stable `YYYY-MM-DD HH:MM UTC` format."""
        if not dt_str:
            return "-"
        try:
            dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        except Exception:
            return dt_str

    def render_report(self, signal, company_name: str, articles: list[dict], threshold_pct) -> str:
        """Render a full multi-line report for terminal/email output."""
        pct = float(signal.change_pct)
        line = "=" * 70
        lines = [
            "",
            line,
            f"STOCK NEWS ALERT  |  {signal.symbol} ({company_name})",
            "-" * 70,
            f"Period : {signal.day_old} → {signal.day_new}",
            f"Move   : {self.arrow(pct)} {signal.change_pct:.2f}%   (threshold: {threshold_pct:.2f}%)",
            line,
        ]

        if not articles:
            lines.append("No related news found.")
            lines.append(line)
            return "\n".join(lines)

        lines.extend(["Top related news", "-" * 70])
        for i, article in enumerate(articles, start=1):
            src = (article.get("source") or {}).get("name") or "-"
            title = self.truncate(article.get("title"), 110)
            desc = self.truncate(article.get("description"), 160)
            url = article.get("url") or "-"
            when = self.fmt_iso_z(article.get("publishedAt"))
            lines.append(f"{i}. {title}")
            lines.append(f"   {desc}")
            lines.append(f"   Source: {src} | Published: {when}")
            lines.append(f"   {url}")
            lines.append("")

        lines.append(line)
        return "\n".join(lines)

    def build_sms_messages(self, signal, company_name: str, articles: list[dict]) -> list[str]:
        """Create one concise SMS body per article (or one fallback message)."""
        header = f"{signal.symbol} ({company_name}): {self.arrow(float(signal.change_pct))} {signal.change_pct:.2f}%"

        if not articles:
            return [f"{header}\nNo related news found."]

        messages: list[str] = []
        for article in articles:
            title = self.truncate(article.get("title"), 80)
            url = article.get("url") or "-"
            messages.append(f"{header}\nHeadline: {title}\n{url}")
        return messages
