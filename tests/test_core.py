import pytest
from usage.core import run_sources, default_window
from usage.models import SourceReport


def test_run_sources_aggregates_demo():
    reports, errors = await_run(["demo"], default_window())
    assert errors == []
    assert len(reports) == 1
    assert reports[0].source == "demo"
    assert len(reports[0].metrics) == 3


def test_unknown_source_becomes_error_not_exception():
    _reports, errors = await_run(["nope"], default_window())
    assert any("unknown source: nope" in e for e in errors)


def test_a_raising_source_is_isolated(monkeypatch):
    class Boom:
        name = "boom"
        env_prefix = None
        async def fetch(self, ctx):
            raise RuntimeError("boom")

    def fake_discover():
        from usage.sources import discover
        reg = discover()
        reg["boom"] = Boom()
        return reg

    monkeypatch.setattr("usage.core.discover", fake_discover)
    _reports, errors = await_run(["demo", "boom"], default_window())
    assert any("boom: RuntimeError: boom" in e for e in errors)


def await_run(selected, window):
    import asyncio
    return asyncio.run(run_sources(selected, window))
