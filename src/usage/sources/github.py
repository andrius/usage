"""GitHub Actions minutes source."""
from __future__ import annotations

from decimal import Decimal

from ..models import FetchContext, Metric, SourceReport

API = "https://api.github.com"


def parse_billing(data: dict, scope: str) -> Metric:
    included = data.get("included_minutes")
    return Metric(
        source="github", scope=scope, label="Actions minutes",
        dimension="quota",
        used=Decimal(str(data["total_minutes_used"])),
        limit=Decimal(str(included)) if included is not None else None,
        unit="minutes",
    )


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

        for org in orgs:
            r = await ctx.http.get(f"{API}/orgs/{org}/settings/billing/actions", headers=headers)
            if r.is_success:
                metrics.append(parse_billing(r.json(), f"org:{org}"))
            else:
                warnings.append(f"org {org} billing: HTTP {r.status_code}")

        me = await ctx.http.get(f"{API}/user", headers=headers)
        if me.is_success:
            login = me.json().get("login")
            r = await ctx.http.get(f"{API}/users/{login}/settings/billing/actions", headers=headers)
            if r.is_success:
                metrics.append(parse_billing(r.json(), f"user:{login}"))
            else:
                warnings.append(f"user billing: HTTP {r.status_code}")
        return SourceReport(source=self.name, metrics=metrics, warnings=warnings)


source = GithubSource()
