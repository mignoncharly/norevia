import uuid
from collections import defaultdict
from datetime import UTC, datetime

from app.models.entities import (
    Category,
    EvidenceType,
    Indicator,
    Location,
    LocationType,
    Observation,
    Source,
)
from app.schemas.api import (
    IndicatorContribution,
    LocationRead,
    ObservationRead,
    RankingItem,
    RankingRequest,
    RankingResponse,
)
from app.scoring.engine import ScoreInput, aggregate_score, confidence_coefficient, normalize_value
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

METHODOLOGY_VERSION = "norevia-winsorized-v1"


async def calculate_ranking(session: AsyncSession, request: RankingRequest) -> RankingResponse:
    peer_locations = list(
        (
            await session.scalars(
                select(Location)
                .where(
                    Location.location_type == LocationType(request.location_type),
                    Location.iso_country_code.in_(request.countries),
                    Location.valid_to.is_(None),
                )
                .order_by(Location.name)
            )
        ).all()
    )
    requested_slugs = set(request.location_slugs)
    locations = (
        [item for item in peer_locations if item.slug in requested_slugs]
        if requested_slugs
        else peer_locations
    )
    if not locations:
        return RankingResponse(
            id=uuid.uuid4(),
            methodology_version=METHODOLOGY_VERSION,
            created_at=datetime.now(UTC),
            results=[],
            warnings=["ranking.no_locations"],
        )

    subcategory = aliased(Category)
    top_category = aliased(Category)
    rows = (
        await session.execute(
            select(Observation, Indicator, top_category, Source)
            .join(Indicator, Observation.indicator_id == Indicator.id)
            .join(subcategory, Indicator.category_id == subcategory.id)
            .join(top_category, subcategory.parent_id == top_category.id)
            .join(Source, Observation.source_id == Source.id)
            .where(Observation.location_id.in_([item.id for item in peer_locations]))
            .order_by(Observation.period_end.desc(), Observation.published_at.desc().nullslast())
        )
    ).all()
    latest: dict[tuple[uuid.UUID, str], tuple[Observation, Indicator, Category, Source]] = {}
    peer_values: dict[tuple[str, int], list[float]] = defaultdict(list)
    for observation, indicator, category, source in rows:
        if request.reference_year and observation.period_end.year > request.reference_year:
            continue
        key = (observation.location_id, indicator.code)
        if key not in latest:
            latest[key] = (observation, indicator, category, source)
            peer_values[(indicator.code, observation.period_end.year)].append(
                float(observation.value)
            )

    weighted_categories = {key for key, value in request.weights.items() if value > 0}
    catalog_subcategory = aliased(Category)
    catalog_top = aliased(Category)
    catalog_rows = (
        await session.execute(
            select(Indicator, catalog_top)
            .join(catalog_subcategory, Indicator.category_id == catalog_subcategory.id)
            .join(catalog_top, catalog_subcategory.parent_id == catalog_top.id)
            .where(Indicator.active.is_(True), catalog_top.code.in_(weighted_categories))
        )
    ).all()
    codes_by_category: dict[str, set[str]] = defaultdict(set)
    for indicator, category in catalog_rows:
        if indicator.official_only and indicator.direction.value != "DESCRIPTIVE_ONLY":
            codes_by_category[category.code].add(indicator.code)
    expected_codes = set().union(*codes_by_category.values()) if codes_by_category else set()

    results: list[RankingItem] = []
    for location in locations:
        contributions: list[IndicatorContribution] = []
        score_inputs: list[ScoreInput] = []
        covered_codes: set[str] = set()
        failed_constraints: list[str] = []
        values_by_code: dict[str, float] = {}
        for (location_id, code), (observation, indicator, category, source) in latest.items():
            if location_id != location.id:
                continue
            values_by_code[code] = float(observation.value)
            eligible = (
                category.code in weighted_categories
                and indicator.official_only
                and source.official_status
                and source.evidence_type == EvidenceType.OFFICIAL
                and indicator.direction.value != "DESCRIPTIVE_ONLY"
            )
            if not eligible:
                continue
            count = len(codes_by_category.get(category.code, set()))
            weight = request.weights[category.code] / count if count else 0
            score = normalize_value(
                float(observation.value),
                peer_values[(code, observation.period_end.year)],
                indicator.direction.value,
                (float(indicator.target_min), float(indicator.target_max))
                if indicator.target_min is not None and indicator.target_max is not None
                else None,
            )
            coefficient = confidence_coefficient(
                is_official=True,
                preferred_geo_level=indicator.preferred_geo_level.value,
                actual_geo_level=observation.geographic_level.value,
                period_end=observation.period_end,
                quality_status=observation.quality_status.value,
            )
            if score is not None:
                covered_codes.add(code)
            score_inputs.append(ScoreInput(score, weight, coefficient))
            evidence = ObservationRead(
                id=observation.id,
                indicator_code=code,
                location_slug=location.slug,
                period_start=observation.period_start,
                period_end=observation.period_end,
                value=float(observation.value),
                unit=observation.unit,
                organization=source.organization,
                source_dataset=observation.source_dataset,
                source_url=observation.source_url,
                retrieved_at=observation.retrieved_at,
                published_at=observation.published_at,
                geographic_level=observation.geographic_level.value,
                quality_status=observation.quality_status.value,
                methodology_version=observation.methodology_version,
                evidence_type=source.evidence_type.value,
                transformations=observation.transformations,
            )
            contributions.append(
                IndicatorContribution(
                    indicator_code=code,
                    category_code=category.code,
                    raw_value=float(observation.value),
                    unit=observation.unit,
                    score=score,
                    weight=weight,
                    quality_coefficient=coefficient,
                    evidence_type=source.evidence_type.value,
                    observation=evidence,
                )
            )
        for constraint in request.constraints:
            actual = values_by_code.get(constraint.indicator_code)
            passed = actual is not None and (
                (constraint.operator == "lte" and actual <= constraint.value)
                or (constraint.operator == "gte" and actual >= constraint.value)
                or (constraint.operator == "eq" and actual == constraint.value)
            )
            if constraint.required and not passed:
                failed_constraints.append(constraint.indicator_code)
        summary = aggregate_score(
            score_inputs, total_requested_weight=sum(request.weights.values())
        )
        results.append(
            RankingItem(
                location=LocationRead.model_validate(location),
                destination_score=summary.destination_score,
                data_coverage=summary.data_coverage,
                methodological_confidence=summary.methodological_confidence,
                confidence_coefficient=summary.confidence_coefficient,
                constraints_met=not failed_constraints,
                failed_constraints=failed_constraints,
                indicators=contributions,
                missing_indicator_codes=sorted(expected_codes - covered_codes),
            )
        )
    results.sort(
        key=lambda item: (
            item.constraints_met,
            item.destination_score is not None,
            item.destination_score or -1,
        ),
        reverse=True,
    )
    return RankingResponse(
        id=uuid.uuid4(),
        methodology_version=METHODOLOGY_VERSION,
        created_at=datetime.now(UTC),
        results=results,
        warnings=["methodology.official_score_only", "methodology.recorded_complaints_warning"],
    )
