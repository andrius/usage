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
