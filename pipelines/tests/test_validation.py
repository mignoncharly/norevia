from datetime import UTC, date, datetime
from decimal import Decimal

from norevia_pipeline.contracts import CandidateObservation
from norevia_pipeline.validation.rules import IndicatorRule, publishable, validate


def observation(
    value: str = "5", unit: str = "percent", end: date = date(2025, 12, 31)
) -> CandidateObservation:
    return CandidateObservation(
        "unemployment_rate",
        "11000000",
        "city",
        date(end.year, 1, 1),
        end,
        Decimal(value),
        unit,
        "destatis",
        "table",
        "https://example.test",
        datetime.now(UTC),
        None,
        "v1",
    )


def test_rejects_unit_change_and_impossible_value() -> None:
    issues = validate(
        [observation("150", "fraction")],
        {"unemployment_rate": IndicatorRule("percent", Decimal(0), Decimal(100))},
    )
    assert {item.code for item in issues} == {"changed_unit", "impossible_value"}
    assert not publishable(issues)


def test_rejects_older_replacement() -> None:
    issues = validate(
        [observation(end=date(2023, 12, 31))],
        {"unemployment_rate": IndicatorRule("percent")},
        [observation(end=date(2024, 12, 31))],
    )
    assert any(item.code == "older_replaces_newer" for item in issues)
