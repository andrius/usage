from dataclasses import FrozenInstanceError
from decimal import Decimal
import pytest
from usage.models import Metric, SourceReport


def test_metric_defaults_limit_and_unit(sample_metric):
    assert sample_metric.limit == Decimal("3000")
    assert sample_metric.unit == "minutes"
    assert sample_metric.fetched_at is not None


def test_metric_is_frozen(sample_metric):
    with pytest.raises(FrozenInstanceError):
        sample_metric.used = Decimal("1")


def test_two_reports_have_distinct_lists():
    a, b = SourceReport(source="x"), SourceReport(source="y")
    a.metrics.append(Metric(source="x", scope="s", label="l", dimension="cost", used=Decimal("1")))
    assert b.metrics == []
