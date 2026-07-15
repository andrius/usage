"""Discover sources, run them in isolation, aggregate reports."""
from __future__ import annotations

import asyncio
from datetime import date, timedelta

import httpx

from .models import DateRange, FetchContext, SourceReport
from .sources import discover


def default_window() -> DateRange:
    until = date.today()
    return DateRange(since=until - timedelta(days=30), until=until)


async def run_sources(
    selected: list[str], window: DateRange
) -> tuple[list[SourceReport], list[str]]:
    """Run the selected sources (or all if none given). Returns reports + errors.

    Each source runs in isolation: a hard failure becomes an error string, never
    crashing the whole run. Unknown source names are reported, not raised.
    """
    registry = discover()
    names = [n for n in (selected or list(registry)) if n in registry]
    errors: list[str] = [
        f"unknown source: {name}" for name in set(selected or []) - set(names)
    ]

    async with httpx.AsyncClient(timeout=30.0) as http:

        async def go(name: str) -> tuple[SourceReport | None, str | None]:
            ctx = FetchContext(creds={}, config={}, window=window, http=http)
            try:
                return await registry[name].fetch(ctx), None
            except Exception as exc:  # noqa: BLE001 - isolate per-source failures
                return None, f"{name}: {exc.__class__.__name__}: {exc}"

        results = await asyncio.gather(*(go(n) for n in names))

    reports = [rep for rep, _ in results if rep is not None]
    errors.extend(err for _, err in results if err)
    return reports, errors
