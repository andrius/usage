from decimal import Decimal
import pytest
from usage.models import DateRange, Metric, SourceReport


@pytest.fixture
def sample_metric():
    return Metric(
        source="demo", scope="account:personal", label="Actions minutes",
        dimension="quota", used=Decimal("1240"), limit=Decimal("3000"), unit="minutes",
    )


@pytest.fixture
def sample_report(sample_metric):
    return SourceReport(source="demo", metrics=[sample_metric], warnings=[])
