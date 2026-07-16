"""Hetzner Cloud estimated monthly cost source (servers only in v1)."""
from __future__ import annotations

from decimal import Decimal

from ..models import FetchContext, Metric, SourceReport

API = "https://api.hetzner.cloud/v1"
DISCLAIMER = ("Estimated run-rate from servers only; volumes, load balancers, "
              "IPs, and traffic are not counted.")


def estimate_cost(servers: list[dict], pricing: dict) -> Decimal:
    """Sum monthly gross price over servers, joined by (server_type, location)."""
    price_by_key: dict[tuple[str, str], Decimal] = {}
    for st in pricing.get("server_types", []):
        for p in st.get("prices", []):
            price_by_key[(st["name"], p["location"])] = Decimal(p["price_monthly"]["gross"])
    total = Decimal("0")
    for s in servers:
        key = (s["server_type"]["name"], s["location"]["name"])
        total += price_by_key.get(key, Decimal("0"))
    return total.quantize(Decimal("0.01"))  # Hetzner bills in EUR (2 decimals)


class HetznerSource:
    name = "hetzner"
    env_prefix = "HETZNER"

    async def fetch(self, ctx: FetchContext) -> SourceReport:
        headers = {"Authorization": f"Bearer {ctx.creds.get('HETZNER_API_TOKEN')}"}
        pri = await ctx.http.get(f"{API}/pricing", headers=headers)
        pri.raise_for_status()
        servers: list[dict] = []
        page = 1
        while True:
            r = await ctx.http.get(f"{API}/servers", params={"page": page, "per_page": 50}, headers=headers)
            r.raise_for_status()
            data = r.json()
            servers.extend(data.get("servers", []))
            nxt = (data.get("meta") or {}).get("pagination", {}).get("next_page")
            if not nxt:
                break
            page = nxt
        cost = estimate_cost(servers, pri.json().get("pricing", {}))
        scope = (ctx.config or {}).get("account") or "account"
        return SourceReport(
            source=self.name,
            metrics=[Metric(source="hetzner", scope=scope,
                            label="Estimated monthly cost", dimension="cost",
                            used=cost, unit="EUR")],
            warnings=[DISCLAIMER],
        )


source = HetznerSource()
