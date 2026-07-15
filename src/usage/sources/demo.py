"""Demo source - returns canned metrics, needs no credentials.

Lets the architecture run end-to-end with zero setup. Real sources
(github, hetzner, claude_code) have the exact same shape and drop in
alongside this one.
"""
from __future__ import annotations

from decimal import Decimal

from ..models import FetchContext, Metric, SourceReport


class DemoSource:
    name = "demo"
    env_prefix = None

    async def fetch(self, ctx: FetchContext) -> SourceReport:
        w = ctx.window
        return SourceReport(
            source=self.name,
            metrics=[
                Metric(
                    source="demo", scope="account:personal", label="Actions minutes",
                    dimension="quota", used=Decimal("1240"), limit=Decimal("3000"),
                    unit="minutes", window=w,
                ),
                Metric(
                    source="demo", scope="account:personal", label="Spend",
                    dimension="cost", used=Decimal("12.40"), unit="USD", window=w,
                ),
                Metric(
                    source="demo", scope="org:acme", label="API credits remaining",
                    dimension="quota", used=Decimal("8700"), limit=Decimal("10000"),
                    unit="credits", window=w,
                ),
            ],
        )


source = DemoSource()
