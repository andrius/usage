import json
from usage.render.json import render


def test_json_is_parseable_and_serializes_decimal(sample_report):
    data = json.loads(render([sample_report]))
    assert data["reports"][0]["source"] == "demo"
    m = data["reports"][0]["metrics"][0]
    assert m["used"] == "1240"          # Decimal -> str
    assert m["limit"] == "3000"
    assert m["dimension"] == "quota"
    assert "T" in m["fetched_at"]       # ISO datetime
    assert data["errors"] == []


def test_json_includes_errors(sample_report):
    data = json.loads(render([sample_report], ["github: HTTP 503", "unknown source: nope"]))
    assert data["errors"] == ["github: HTTP 503", "unknown source: nope"]
    assert data["reports"]              # reports still present alongside errors
