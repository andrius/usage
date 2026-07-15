import asyncio
from datetime import date
from decimal import Decimal
from pathlib import Path

import httpx

from usage.models import DateRange, FetchContext
from usage.sources.github import GithubSource, parse_usage_summary

FIX = Path(__file__).parent.parent / "fixtures" / "github_usage_summary.json"


def _ctx(handler) -> FetchContext:
    return FetchContext(
        creds={"GITHUB_TOKEN": "t"}, config={},
        window=DateRange(since=date(2026, 1, 1), until=date(2026, 1, 31)),
        http=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )


def test_parse_usage_summary_sums_actions_minutes():
    data = json_load()
    metrics = parse_usage_summary(data, "user:octocat")
    assert len(metrics) == 1
    m = metrics[0]
    assert m.label == "Actions minutes"
    assert m.dimension == "quota"
    assert m.used == Decimal("4031")          # 3176 + 855; storage + Git LFS excluded
    assert m.limit is None                    # new API exposes no included-minutes quota
    assert m.unit == "minutes"
    assert m.scope == "user:octocat"


def test_parse_usage_summary_no_actions_returns_empty():
    metrics = parse_usage_summary({"usageItems": [{"product": "Git LFS", "grossQuantity": 5, "unitType": "gigabyte-hours"}]}, "user:x")
    assert metrics == []


def test_fetch_user_and_org():
    data = FIX.read_text()

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/user":
            return httpx.Response(200, json={"login": "octocat"})
        if path == "/user/orgs":
            return httpx.Response(200, json=[{"login": "acme"}])
        return httpx.Response(200, content=data)  # usage/summary for user + org

    rep = asyncio.run(GithubSource().fetch(_ctx(handler)))
    by_scope = {m.scope: m for m in rep.metrics}
    assert "user:octocat" in by_scope
    assert "org:acme" in by_scope
    assert by_scope["user:octocat"].used == Decimal("4031")


def test_fetch_org_404_reports_warning():
    data = FIX.read_text()

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/user":
            return httpx.Response(200, json={"login": "octocat"})
        if path == "/user/orgs":
            return httpx.Response(200, json=[{"login": "acme"}, {"login": "dead"}])
        if "/organizations/dead/" in path:
            return httpx.Response(404, json={"message": "Not Found"})
        return httpx.Response(200, content=data)

    rep = asyncio.run(GithubSource().fetch(_ctx(handler)))
    scopes = {m.scope for m in rep.metrics}
    assert "org:acme" in scopes
    assert "org:dead" not in scopes
    assert any("dead billing: HTTP 404" in w for w in rep.warnings)


def json_load():
    import json
    return json.loads(FIX.read_text())
