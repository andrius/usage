"""Source auto-discovery.

Every module in this package that exports a module-level `source` instance
(implementing the Source protocol) is picked up automatically. Modules whose
name starts with `_` (like `_template`) are skipped. Drop a file in, get a
source - no registration.
"""
from __future__ import annotations

import importlib
import pkgutil

from ..models import Source


def discover() -> dict[str, Source]:
    found: dict[str, Source] = {}
    for mod_info in pkgutil.iter_modules(__path__):
        if mod_info.name.startswith("_"):
            continue
        module = importlib.import_module(f"{__name__}.{mod_info.name}")
        instance = getattr(module, "source", None)
        if instance is not None:
            found[instance.name] = instance
    return found
