"""Source template - copy this file, rename, implement fetch.

To bake a new source:
  1. Copy this file to <your_source>.py (e.g. hetzner.py).
  2. Set `name`.
  3. Read credentials from ctx.creds and preferences from ctx.config.
  4. In fetch(), call your provider's API via ctx.http and return a SourceReport
     of Metric rows (dimension "cost" or "quota").
  5. Export a module-level `source = YourSource()` instance.

Discovery is automatic - no registration anywhere. Run it alone with:
  usage --sources <your_source>
"""
from __future__ import annotations

from ..models import FetchContext, SourceReport


class TemplateSource:
    name = "template"

    async def fetch(self, ctx: FetchContext) -> SourceReport:
        # token = ctx.creds.get("token")
        # include = ctx.config.get("include", [])
        return SourceReport(source=self.name)
