"""
app_types.py

Shared lightweight types for CLI parsing and workflow coordination.
"""

from __future__ import annotations

from dataclasses import dataclass


SymbolTarget = tuple[str, str]
SymbolTargets = list[SymbolTarget]


@dataclass
class OutputTargets:
    """Normalized output routing targets from CLI options."""

    terminal_enabled: bool
    sms_targets: list[str]
    email_targets: list[str]
