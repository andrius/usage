from pathlib import Path
from decimal import Decimal
from usage.sources.claude_code import parse_usage

FIX = Path(__file__).parent.parent / "fixtures" / "claude_usage.txt"


def test_parse_session_and_weekly():
    metrics = parse_usage(FIX.read_text())
    labels = {m.label: m for m in metrics}
    assert "Session usage" in labels
    assert labels["Session usage"].used == Decimal("24")
    assert labels["Weekly usage (all models)"].used == Decimal("71")
    assert labels["Weekly usage (Fable)"].used == Decimal("98")
    for m in metrics:
        assert m.limit == Decimal("100")
        assert m.unit == "%"


def test_parse_garbage_returns_empty():
    assert parse_usage("nothing useful here") == []
