import json
from decimal import Decimal
from pathlib import Path
import httpx
from usage.sources.hetzner import HetznerSource, estimate_cost

FIXDIR = Path(__file__).parent.parent / "fixtures"


def test_estimate_cost_joins_server_type_and_location():
    servers = json.loads((FIXDIR / "hetzner_servers.json").read_text())["servers"]
    pricing = json.loads((FIXDIR / "hetzner_pricing.json").read_text())["pricing"]
    assert estimate_cost(servers, pricing) == Decimal("14.49")  # 2.96 + 11.53


def test_fetch_returns_cost_metric_with_warning():
    srv = (FIXDIR / "hetzner_servers.json").read_text()
    pri = (FIXDIR / "hetzner_pricing.json").read_text()

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/servers":
            return httpx.Response(200, content=srv)
        if request.url.path == "/v1/pricing":
            return httpx.Response(200, content=pri)
        return httpx.Response(404)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    from usage.models import FetchContext, DateRange
    from datetime import date
    ctx = FetchContext(creds={"HETZNER_API_TOKEN": "t"}, config={},
                       window=DateRange(since=date(2026, 1, 1), until=date(2026, 1, 31)), http=client)
    import asyncio
    rep = asyncio.run(HetznerSource().fetch(ctx))
    assert len(rep.metrics) == 1
    m = rep.metrics[0]
    assert m.dimension == "cost"
    assert m.used == Decimal("14.49")
    assert m.unit == "EUR"
    assert rep.warnings  # servers-only disclaimer
