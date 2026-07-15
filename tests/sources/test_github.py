import json
from decimal import Decimal
from pathlib import Path
import httpx
from usage.sources.github import GithubSource, parse_billing

FIX = Path(__file__).parent.parent / "fixtures" / "github_billing.json"


def test_parse_billing_maps_fields():
    data = json.loads(FIX.read_text())
    m = parse_billing(data, "org:acme")
    assert m.dimension == "quota"
    assert m.used == Decimal("305")
    assert m.limit == Decimal("3000")
    assert m.unit == "minutes"
    assert m.scope == "org:acme"


def test_fetch_uses_mock_transport():
    data = FIX.read_text()
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/user":
            return httpx.Response(200, json={"login": "alice"})
        if request.url.path == "/user/orgs":
            return httpx.Response(200, json=[{"login": "acme"}])
        return httpx.Response(200, content=data)

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    from usage.models import FetchContext, DateRange
    from datetime import date
    ctx = FetchContext(creds={"GITHUB_TOKEN": "t"}, config={},
                       window=DateRange(since=date(2026,1,1), until=date(2026,1,31)), http=client)
    import asyncio
    rep = asyncio.run(GithubSource().fetch(ctx))
    scopes = {m.scope for m in rep.metrics}
    assert "org:acme" in scopes
    assert any(s.startswith("user:") for s in scopes)
