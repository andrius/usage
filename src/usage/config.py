"""Minimal config loading.

Loads .env (credentials, gitignored) into a dict. Per-source credential and
config slicing is wired in once the real sources land; for the spike the runner
passes empty slices so the demo source runs with no setup.
"""
from __future__ import annotations

from pathlib import Path


def load_env(path: Path | str = ".env") -> dict[str, str]:
    """Parse a .env file into a dict. Missing file -> empty dict."""
    p = Path(path)
    if not p.exists():
        return {}
    env: dict[str, str] = {}
    for raw in p.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


from datetime import date, timedelta
from .models import DateRange

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

DEFAULT_WINDOW_DAYS = 30


def load_config(path: "str | Path") -> dict:
    p = Path(path)
    if not p.exists() or yaml is None:
        return {}
    return yaml.safe_load(p.read_text()) or {}


def window_from_config(config: dict) -> DateRange:
    days_cfg = ((config or {}).get("window") or {}).get("default_days")
    days = int(days_cfg) if days_cfg else DEFAULT_WINDOW_DAYS
    until = date.today()
    return DateRange(since=until - timedelta(days=days), until=until)


def slice_creds(env: dict, prefix: "str | None") -> dict:
    if not prefix:
        return {}
    mark = prefix + "_"
    return {k: v for k, v in env.items() if k.startswith(mark)}
