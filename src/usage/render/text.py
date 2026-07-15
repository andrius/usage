"""Plain-text renderer, grouped by source."""
from __future__ import annotations

from ..models import SourceReport


def render(reports: list[SourceReport], errors: list[str] | None = None) -> str:
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
    for e in errors or []:
        lines.append(f"error: {e}")
    return "\n".join(lines).rstrip()
