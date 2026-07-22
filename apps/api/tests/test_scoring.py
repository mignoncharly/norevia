from datetime import date

import pytest
from app.scoring.engine import ScoreInput, aggregate_score, confidence_coefficient, normalize_value


def test_winsorized_direction_and_outliers() -> None:
    peers = list(range(1, 101))
    assert normalize_value(999, peers, "HIGHER_IS_BETTER") == pytest.approx(100)
    assert normalize_value(-999, peers, "LOWER_IS_BETTER") == pytest.approx(100)


def test_coverage_is_not_confidence_or_score() -> None:
    summary = aggregate_score([ScoreInput(80, 60, 1)], total_requested_weight=100)
    assert summary.destination_score == 80
    assert summary.data_coverage == 60
    assert summary.confidence_coefficient == 1


def test_national_data_for_city_is_explicitly_discounted() -> None:
    coefficient = confidence_coefficient(
        is_official=True,
        preferred_geo_level="city",
        actual_geo_level="country",
        period_end=date(2025, 12, 31),
        quality_status="VALIDATED",
        today=date(2026, 7, 1),
    )
    assert coefficient == 0.7


def test_subjective_data_never_enters_official_score() -> None:
    assert (
        confidence_coefficient(
            is_official=False,
            preferred_geo_level="city",
            actual_geo_level="city",
            period_end=date(2026, 1, 1),
            quality_status="VALIDATED",
        )
        == 0
    )
