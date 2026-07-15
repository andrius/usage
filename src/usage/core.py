"""Discover sources, run them in isolation, aggregate reports."""
from __future__ import annotations

import asyncio
from datetime import date, timedelta

import httpx

from .config import load_config, load_env, slice_creds, DEFAULT_WINDOW_DAYS
from .models import DateRange, FetchContext, SourceReport
from .sources import discover


def default_window() -> DateRange:
    until = date.today()
    return DateRange(since=until - timedelta(days=DEFAULT_WINDOW_DAYS), until=until)


async def run_sources(
    selected: list[str],
    window: DateRange,
    *,
    env: dict | None = None,
    config: dict | None = None,
) -> tuple[list[SourceReport], list[str]]:
    registry = discover()
    names = [n for n in (selected or list(registry)) if n in registry]
    errors: list[str] = [
        f"unknown source: {name}" for name in set(selected or []) - set(names)
    ]

    env = load_env() if env is None else env
    config = load_config("config.yml") if config is None else config
    source_cfg = (config or {}).get("sources") or {}

    async with httpx.AsyncClient(timeout=30.0) as http:

        async def go(name: str) -> tuple[SourceReport | None, str | None]:
            src = registry[name]
            creds = slice_creds(env, getattr(src, "env_prefix", None))
            ctx = FetchContext(creds=creds, config=source_cfg.get(name, {}),
                               window=window, http=http)
            try:
                return await src.fetch(ctx), None
            except Exception as exc:  # noqa: BLE001 - isolate per-source failures
                return None, f"{name}: {exc.__class__.__name__}: {exc}"

        results = await asyncio.gather(*(go(n) for n in names))

    reports = [rep for rep, _ in results if rep is not None]
    errors.extend(err for _, err in results if err)
    return reports, errors
