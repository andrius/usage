"""Hetzner Cloud estimated monthly cost source (servers only in v1)."""
from __future__ import annotations

from decimal import Decimal

from ..models import FetchContext, Metric, SourceReport

API = "https://api.hetzner.com/v1"
DISCLAIMER = ("Estimated run-rate from servers only; volumes, load balancers, "
              "IPs, and traffic are not counted.")


def estimate_cost(servers: list[dict], pricing: dict) -> Decimal:
    """Sum monthly gross price over servers, joined by (server_type, location)."""
    price_by_key: dict[tuple[str, str], Decimal] = {}
    for st in pricing.get("server_type", []):
        for p in st.get("prices", []):
            price_by_key[(st["name"], p["location"])] = Decimal(p["price_monthly"]["gross"])
    total = Decimal("0")
    for s in servers:
        key = (s["server_type"]["name"], s["location"]["name"])
        total += price_by_key.get(key, Decimal("0"))
    return total


class HetznerSource:
    name = "hetzner"
    env_prefix = "HETZNER"

    async def fetch(self, ctx: FetchContext) -> SourceReport:
        headers = {"Authorization": f"Bearer {ctx.creds.get('HETZNER_API_TOKEN')}"}
        srv = await ctx.http.get(f"{API}/servers", headers=headers)
        srv.raise_for_status()
        pri = await ctx.http.get(f"{API}/pricing", headers=headers)
        pri.raise_for_status()
        servers = srv.json().get("servers", [])
        cost = estimate_cost(servers, pri.json().get("pricing", {}))
        return SourceReport(
            source=self.name,
            metrics=[Metric(source="hetzner", scope="account",
                            label="Estimated monthly cost", dimension="cost",
                            used=cost, unit="EUR")],
            warnings=[DISCLAIMER],
        )


source = HetznerSource()
