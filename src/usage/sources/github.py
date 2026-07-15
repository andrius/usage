"""GitHub Actions minutes source.

Uses the current billing API (`/settings/billing/usage/summary`); the older
`/settings/billing/actions` endpoint was deprecated (HTTP 410). The summary
exposes usage per product/SKU; we sum Actions compute-minute SKUs. The new API
does not publish an "included minutes" quota, so the metric carries no limit.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from ..models import FetchContext, Metric, SourceReport

API = "https://api.github.com"


def parse_usage_summary(data: dict, scope: str) -> list[Metric]:
    """Sum Actions compute minutes from a billing usage/summary response.

    Only Actions SKUs measured in minutes count (storage and other products are
    gigabyte-hours). Returns [] when there is no Actions minute usage.
    """
    minutes = Decimal("0")
    for item in data.get("usageItems", []):
        if item.get("product") == "Actions" and item.get("unitType") == "minutes":
            minutes += Decimal(str(item.get("grossQuantity", 0)))
    if minutes <= 0:
        return []
    return [Metric(
        source="github", scope=scope, label="Actions minutes",
        dimension="quota",
        used=minutes.quantize(Decimal("1"), rounding=ROUND_HALF_UP),
        limit=None, unit="minutes",
    )]


class GithubSource:
    name = "github"
    env_prefix = "GITHUB"

    async def fetch(self, ctx: FetchContext) -> SourceReport:
        token = ctx.creds.get("GITHUB_TOKEN")
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        metrics: list[Metric] = []
        warnings: list[str] = []

        include = (ctx.config or {}).get("include") or []
        if include:
            orgs = include
        else:
            r = await ctx.http.get(f"{API}/user/orgs", headers=headers)
            r.raise_for_status()
            orgs = [o["login"] for o in r.json()]

        me = await ctx.http.get(f"{API}/user", headers=headers)
        if me.is_success:
            login = me.json().get("login")
            r = await ctx.http.get(
                f"{API}/users/{login}/settings/billing/usage/summary", headers=headers)
            if r.is_success:
                metrics.extend(parse_usage_summary(r.json(), f"user:{login}"))
            else:
                warnings.append(f"user billing: HTTP {r.status_code}")
        else:
            warnings.append(f"/user: HTTP {me.status_code}")

        for org in orgs:
            r = await ctx.http.get(
                f"{API}/organizations/{org}/settings/billing/usage/summary", headers=headers)
            if r.is_success:
                metrics.extend(parse_usage_summary(r.json(), f"org:{org}"))
            else:
                warnings.append(f"org {org} billing: HTTP {r.status_code}")

        return SourceReport(source=self.name, metrics=metrics, warnings=warnings)


source = GithubSource()
