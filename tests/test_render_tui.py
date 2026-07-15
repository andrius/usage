from decimal import Decimal

from usage.models import Metric, SourceReport
from usage.render.tui import format_report, gauge


def test_gauge_scales_used_over_limit():
    assert gauge(Decimal("50"), Decimal("100"), width=10) == "#####-----"


def test_gauge_clamps_above_limit():
    assert gauge(Decimal("150"), Decimal("100"), width=4) == "####"


def test_format_report_includes_scope_label_and_warning():
    rep = SourceReport(
        source="github",
        metrics=[Metric(source="github", scope="org:acme", label="Actions minutes",
                        dimension="quota", used=Decimal("1240"), limit=Decimal("3000"),
                        unit="minutes")],
        warnings=["partial"],
    )
    out = format_report(rep)
    assert "[github]" in out
    assert "org:acme" in out
    assert "1240 / 3000 minutes" in out
    assert "! partial" in out
