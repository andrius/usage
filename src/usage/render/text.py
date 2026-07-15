"""Plain-text renderer, grouped by source."""
from __future__ import annotations

from ..models import SourceReport


def render(reports: list[SourceReport]) -> str:
    lines: list[str] = []
    for r in reports:
        lines.append(f"[{r.source}]")
        for w in r.warnings:
            lines.append(f"  ! {w}")
        for m in r.metrics:
            row = f"  {m.scope}  {m.label}: {m.used}"
            if m.limit is not None:
                row += f" / {m.limit}"
            row += f" {m.unit} ({m.dimension})"
            lines.append(row)
        lines.append("")
    return "\n".join(lines).rstrip()
