"""JSON renderer."""
from __future__ import annotations

import dataclasses
import json
from datetime import date, datetime
from decimal import Decimal

from ..models import SourceReport


def _default(o: object) -> object:
    if isinstance(o, (date, datetime)):
        return o.isoformat()
    if isinstance(o, Decimal):
        return str(o)
    raise TypeError(f"not serializable: {type(o)}")


def render(reports: list[SourceReport]) -> str:
    return json.dumps([dataclasses.asdict(r) for r in reports], indent=2, default=_default)
