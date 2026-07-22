import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.database import get_session
from app.models.entities import Category, Indicator, Observation, Source
from app.schemas.api import ApiModel, ObservationRead

router = APIRouter(tags=["catalog"])


class IndicatorCatalogRead(ApiModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    code: str
    category_code: str
    subcategory_code: str
    name_key: str
    description_key: str
    unit: str
    direction: str
    preferred_geo_level: str
    normalization_method: str
    official_only: bool


@router.get("/indicators", response_model=list[IndicatorCatalogRead])
async def indicators(
    category: str | None = None, session: AsyncSession = Depends(get_session)
) -> list[IndicatorCatalogRead]:
    subcategory = aliased(Category)
    top_category = aliased(Category)
    query = (
        select(Indicator, top_category.code, subcategory.code)
        .join(subcategory, Indicator.category_id == subcategory.id)
        .join(top_category, subcategory.parent_id == top_category.id)
    )
    if category:
        query = query.where(top_category.code == category)
    rows = (await session.execute(query.order_by(top_category.sort_order, Indicator.code))).all()
    return [
        IndicatorCatalogRead(
            id=item.id,
            code=item.code,
            category_code=category_code,
            subcategory_code=subcategory_code.split(".", 1)[-1],
            name_key=item.name_key,
            description_key=item.description_key,
            unit=item.unit,
            direction=item.direction.value,
            preferred_geo_level=item.preferred_geo_level.value,
            normalization_method=item.normalization_method,
            official_only=item.official_only,
        )
        for item, category_code, subcategory_code in rows
    ]


@router.get("/observations", response_model=list[ObservationRead])
async def observations(
    location: str,
    indicator: str,
    limit: int = Query(20, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
) -> list[ObservationRead]:
    rows = (
        await session.execute(
            select(Observation, Indicator.code, Source)
            .join(Indicator)
            .join(Source)
            .where(Observation.location.has(slug=location), Indicator.code == indicator)
            .order_by(Observation.period_end.desc())
            .limit(limit)
        )
    ).all()
    return [
        ObservationRead(
            id=item.id,
            indicator_code=code,
            location_slug=location,
            period_start=item.period_start,
            period_end=item.period_end,
            value=float(item.value),
            unit=item.unit,
            organization=source.organization,
            source_dataset=item.source_dataset,
            source_url=item.source_url,
            retrieved_at=item.retrieved_at,
            published_at=item.published_at,
            geographic_level=item.geographic_level.value,
            quality_status=item.quality_status.value,
            methodology_version=item.methodology_version,
            evidence_type=source.evidence_type.value,
            transformations=item.transformations,
        )
        for item, code, source in rows
    ]
