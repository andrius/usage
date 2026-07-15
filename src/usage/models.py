"""Core data contract shared by the runner and every source.

A source is a leaf: it takes a FetchContext (its own creds + config slice +
time window + a shared HTTP client) and returns a SourceReport of flat Metric
rows. The flat Metric shape is what makes cross-source aggregation and every
renderer trivial.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Literal, Mapping, Protocol, runtime_checkable

if TYPE_CHECKING:
    import httpx


@dataclass(frozen=True)
class DateRange:
    since: date
    until: date


@dataclass(frozen=True)
class Metric:
    source: str
    scope: str               # "org:acme", "account:personal", "project:web-prod"
    label: str               # "Actions minutes", "Spend", "API credits"
    dimension: Literal["cost", "quota"]
    used: Decimal
    limit: Decimal | None = None   # quota ceiling / budget; None when N/A
    unit: str = ""                 # "USD", "minutes", "credits", "tokens"
    window: DateRange | None = None
    fetched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class FetchContext:
    creds: Mapping[str, str]        # this source's env vars, already resolved
    config: Mapping[str, Any]       # this source's config.yml slice
    window: DateRange
    http: "httpx.AsyncClient"       # shared, reused across sources


@dataclass(frozen=True)
class SourceReport:
    source: str
    metrics: list[Metric] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@runtime_checkable
class Source(Protocol):
    name: str

    async def fetch(self, ctx: FetchContext) -> SourceReport: ...
