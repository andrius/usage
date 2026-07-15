"""Rich table renderer (--cli). Placeholder default render for the spike."""
from __future__ import annotations

from rich.console import Console
from rich.table import Table

from ..models import SourceReport


def render(reports: list[SourceReport], errors: list[str] | None = None) -> None:
    console = Console()
    table = Table(title="usage")
    table.add_column("source")
    table.add_column("scope")
    table.add_column("metric")
    table.add_column("used", justify="right")
    table.add_column("limit", justify="right")
    table.add_column("unit")
    table.add_column("kind")

    for r in reports:
        for m in r.metrics:
            table.add_row(
                m.source,
                m.scope,
                m.label,
                f"{m.used}",
                f"{m.limit}" if m.limit is not None else "-",
                m.unit,
                m.dimension,
            )

    console.print(table)
    for err in errors or []:
        console.print(f"[red]error:[/red] {err}")
