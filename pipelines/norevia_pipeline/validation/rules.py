from collections import Counter, defaultdict
from dataclasses import dataclass
from decimal import Decimal

from norevia_pipeline.contracts import CandidateObservation


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    severity: str
    indicator_code: str
    geo_code: str
    detail: str


@dataclass(frozen=True)
class IndicatorRule:
    unit: str
    minimum: Decimal | None = None
    maximum: Decimal | None = None
    maximum_annual_change_ratio: Decimal = Decimal("5")


def validate(
    observations: list[CandidateObservation],
    rules: dict[str, IndicatorRule],
    previous: list[CandidateObservation] | None = None,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    identities = [
        (
            item.indicator_code,
            item.official_geo_code,
            item.period_start,
            item.period_end,
            item.source_code,
            item.methodology_version,
        )
        for item in observations
    ]
    duplicates = {key for key, count in Counter(identities).items() if count > 1}
    previous_latest: dict[tuple[str, str], CandidateObservation] = {}
    for item in previous or []:
        key = (item.indicator_code, item.official_geo_code)
        if key not in previous_latest or item.period_end > previous_latest[key].period_end:
            previous_latest[key] = item
    series: dict[tuple[str, str], list[CandidateObservation]] = defaultdict(list)
    for item, identity in zip(observations, identities, strict=True):
        key = (item.indicator_code, item.official_geo_code)
        series[key].append(item)
        rule = rules.get(item.indicator_code)
        if identity in duplicates:
            issues.append(ValidationIssue("duplicate", "error", *key, "Duplicate natural key"))
        if not item.source_url or not item.methodology_version or not item.source_dataset:
            issues.append(
                ValidationIssue(
                    "missing_metadata", "error", *key, "Required provenance field is empty"
                )
            )
        if item.period_end < item.period_start:
            issues.append(
                ValidationIssue("invalid_period", "error", *key, "Period ends before it starts")
            )
        if item.series_break:
            issues.append(
                ValidationIssue(
                    "series_break", "warning", *key, "Source flags a definition or series break"
                )
            )
        if rule:
            if item.unit != rule.unit:
                issues.append(
                    ValidationIssue(
                        "changed_unit", "error", *key, f"Expected {rule.unit}, received {item.unit}"
                    )
                )
            if (
                rule.minimum is not None
                and item.value < rule.minimum
                or rule.maximum is not None
                and item.value > rule.maximum
            ):
                issues.append(
                    ValidationIssue(
                        "impossible_value",
                        "error",
                        *key,
                        f"Value {item.value} is outside accepted bounds",
                    )
                )
        old = previous_latest.get(key)
        if old and item.period_end < old.period_end:
            issues.append(
                ValidationIssue(
                    "older_replaces_newer",
                    "error",
                    *key,
                    f"Incoming {item.period_end} predates published {old.period_end}",
                )
            )
    for key, items in series.items():
        ordered = sorted(items, key=lambda item: item.period_end)
        rule = rules.get(key[0])
        if not rule:
            continue
        for before, after in zip(ordered, ordered[1:], strict=False):
            baseline = max(abs(before.value), Decimal("0.000001"))
            change = abs(after.value - before.value) / baseline
            if change > rule.maximum_annual_change_ratio:
                issues.append(
                    ValidationIssue(
                        "abnormal_annual_variation",
                        "warning",
                        *key,
                        f"Change ratio {change:.2f} exceeds {rule.maximum_annual_change_ratio}",
                    )
                )
    return issues


def publishable(issues: list[ValidationIssue]) -> bool:
    return not any(issue.severity == "error" for issue in issues)
