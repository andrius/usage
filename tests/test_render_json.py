import json
from usage.render.json import render


def test_json_is_parseable_and_serializes_decimal(sample_report):
    data = json.loads(render([sample_report]))
    assert data[0]["source"] == "demo"
    m = data[0]["metrics"][0]
    assert m["used"] == "1240"          # Decimal -> str
    assert m["limit"] == "3000"
    assert m["dimension"] == "quota"
    assert "T" in m["fetched_at"]       # ISO datetime
