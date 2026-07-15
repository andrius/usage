"""Textual TUI renderer (default output)."""
from __future__ import annotations

from decimal import Decimal

from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Footer, Header, Static

from ..models import SourceReport


def gauge(used: Decimal, limit: Decimal | None, width: int = 20) -> str:
    if not limit:
        return ""
    frac = max(0.0, min(1.0, float(used) / float(limit)))
    filled = int(round(frac * width))
    return "#" * filled + "-" * (width - filled)


def format_report(report: SourceReport) -> str:
    lines = [f"[{report.source}]"]
    for m in report.metrics:
        row = f"  {m.scope}  {m.label}: {m.used}"
        if m.limit is not None:
            row += f" / {m.limit}"
        row += f" {m.unit}"
        if m.dimension == "quota":
            row += "  " + gauge(m.used, m.limit)
        lines.append(row)
    for w in report.warnings:
        lines.append(f"  ! {w}")
    return "\n".join(lines)


class UsageApp(App):
    def __init__(self, reports: list[SourceReport], errors: list[str] | None = None):
        super().__init__()
        self.reports = reports
        self.errors = errors or []

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll():
            for r in self.reports:
                yield Static(format_report(r))
            for e in self.errors:
                yield Static(f"error: {e}")
        yield Footer()


def render(reports: list[SourceReport], errors: list[str] | None = None) -> None:
    UsageApp(reports, errors).run()
