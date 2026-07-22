from dataclasses import dataclass
from datetime import date
from math import isfinite
from statistics import quantiles


@dataclass(frozen=True)
class ScoreInput:
    score: float | None
    weight: float
    quality_coefficient: float


@dataclass(frozen=True)
class ScoreSummary:
    destination_score: float | None
    data_coverage: float
    confidence_coefficient: float
    methodological_confidence: str


def percentile_bounds(peer_values: list[float]) -> tuple[float, float] | None:
    values = sorted(value for value in peer_values if isfinite(value))
    if len(values) < 2:
        return None
    if len(values) < 20:
        return values[0], values[-1]
    cut_points = quantiles(values, n=100, method="inclusive")
    return cut_points[4], cut_points[94]


def normalize_value(
    value: float,
    peer_values: list[float],
    direction: str,
    target_range: tuple[float, float] | None = None,
) -> float | None:
    if direction == "DESCRIPTIVE_ONLY" or not isfinite(value):
        return None
    bounds = percentile_bounds(peer_values)
    if bounds is None or bounds[0] == bounds[1]:
        return None
    lower, upper = bounds
    capped = min(upper, max(lower, value))
    if direction == "TARGET_RANGE":
        if not target_range:
            return None
        target_min, target_max = target_range
        if target_min <= capped <= target_max:
            return 100.0
        distance = target_min - capped if capped < target_min else capped - target_max
        span = max(target_min - lower, upper - target_max, 1e-9)
        return max(0.0, 100.0 * (1.0 - distance / span))
    ascending = 100.0 * (capped - lower) / (upper - lower)
    return ascending if direction == "HIGHER_IS_BETTER" else 100.0 - ascending


def confidence_coefficient(
    *,
    is_official: bool,
    preferred_geo_level: str,
    actual_geo_level: str,
    period_end: date,
    quality_status: str,
    today: date | None = None,
) -> float:
    if not is_official or quality_status == "REJECTED":
        return 0.0
    today = today or date.today()
    age_years = max(0.0, (today - period_end).days / 365.25)
    freshness = 1.0 if age_years <= 2 else max(0.6, 1.0 - (age_years - 2) * 0.08)
    geography = (
        1.0
        if preferred_geo_level == actual_geo_level
        else {
            "city:district": 0.9,
            "city:state": 0.8,
            "city:country": 0.7,
            "district:state": 0.9,
            "state:country": 0.8,
        }.get(f"{preferred_geo_level}:{actual_geo_level}", 0.75)
    )
    quality = {"VALIDATED": 1.0, "PROVISIONAL": 0.9, "ESTIMATED": 0.55, "STALE": 0.7}.get(
        quality_status, 0.0
    )
    return round(min(freshness, geography, quality), 3)


def aggregate_score(inputs: list[ScoreInput], total_requested_weight: float) -> ScoreSummary:
    included = [
        item
        for item in inputs
        if item.score is not None and item.weight > 0 and item.quality_coefficient > 0
    ]
    covered_weight = sum(item.weight for item in included)
    adjusted_weight = sum(item.weight * item.quality_coefficient for item in included)
    destination_score = (
        sum((item.score or 0) * item.weight * item.quality_coefficient for item in included)
        / adjusted_weight
        if adjusted_weight
        else None
    )
    coverage = 100 * covered_weight / total_requested_weight if total_requested_weight else 0.0
    confidence = adjusted_weight / covered_weight if covered_weight else 0.0
    band = (
        "insufficient"
        if coverage < 50
        else "high"
        if confidence >= 0.9
        else "medium"
        if confidence >= 0.7
        else "low"
    )
    return ScoreSummary(destination_score, coverage, confidence, band)
