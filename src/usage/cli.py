"""CLI entry point: parse flags, run sources, dispatch to a renderer.

Default render is a rich table for the spike; the real default becomes the
textual TUI once that layer lands. --json / --text / --cli select the others.
"""
from __future__ import annotations

import argparse
import asyncio
from datetime import date

from .config import load_config, window_from_config
from .core import run_sources
from .render import json as r_json
from .render import table as r_table
from .render import text as r_text
from .render import tui as r_tui


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="usage",
        description="Fetch usage, quota, and billing from cloud and AI sources.",
    )
    out = p.add_mutually_exclusive_group()
    out.add_argument("--json", action="store_true", help="machine-readable JSON")
    out.add_argument("--text", action="store_true", help="plain text")
    out.add_argument("--cli", action="store_true", help="formatted table")
    p.add_argument("--sources", default="", help="comma-separated source names (default: all)")
    p.add_argument("--since", help="start date YYYY-MM-DD (default: 30 days ago)")
    p.add_argument("--until", help="end date YYYY-MM-DD (default: today)")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_config("config.yml")
    if args.since or args.until:
        base = window_from_config(config)
        window = type(base)(
            since=date.fromisoformat(args.since) if args.since else base.since,
            until=date.fromisoformat(args.until) if args.until else base.until,
        )
    else:
        window = window_from_config(config)

    selected = [s.strip() for s in args.sources.split(",") if s.strip()]
    reports, errors = asyncio.run(run_sources(selected, window, config=config))

    if args.json:
        print(r_json.render(reports))
    elif args.text:
        print(r_text.render(reports))
    elif args.cli:
        r_table.render(reports, errors)
    else:
        r_tui.render(reports, errors)   # default: textual TUI

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
