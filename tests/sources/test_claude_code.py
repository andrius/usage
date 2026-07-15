from pathlib import Path
from decimal import Decimal
from usage.sources.claude_code import _no_metric_warnings, parse_usage

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


_API_MODE = "API-key/gateway mode"


def test_no_metric_api_key_mode_via_takes_precedence():
    # stderr carries the auth-override notice; stdout has no subscription lines
    stderr = ("claude.ai connectors are disabled because ANTHROPIC_API_KEY or "
              "another auth source is set and takes precedence over your claude.ai login")
    warns = _no_metric_warnings(stdout="", stderr=stderr)
    assert len(warns) == 1
    assert _API_MODE in warns[0]


def test_no_metric_api_key_mode_via_total_cost():
    # headless session cost summary with no subscription report
    stdout = ("Total cost:            $0.0000\n"
              "Total duration (API):  0s\n"
              "Usage:                 0 input, 0 output, 0 cache read, 0 cache write\n")
    warns = _no_metric_warnings(stdout=stdout, stderr="")
    assert len(warns) == 1
    assert _API_MODE in warns[0]


def test_no_metric_generic_parse_failure_dumps_raw():
    # unrecognised output, no API-mode markers -> generic fallback with raw dump
    warns = _no_metric_warnings(stdout="something totally unexpected", stderr="")
    assert len(warns) == 1
    assert "could not parse /usage" in warns[0]
    assert "something totally unexpected" in warns[0]
