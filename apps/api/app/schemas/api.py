import uuid
from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=lambda value: "".join(
            word if index == 0 else word.capitalize() for index, word in enumerate(value.split("_"))
        ),
        populate_by_name=True,
        from_attributes=True,
    )


class ErrorDetail(ApiModel):
    code: str
    message_key: str
    context: dict[str, object] = Field(default_factory=dict)


class LocationRead(ApiModel):
    id: uuid.UUID
    slug: str
    name: str
    location_type: str
    parent_location_id: uuid.UUID | None
    iso_country_code: str
    official_geo_code: str | None
    latitude: float | None
    longitude: float | None
    population: int | None


class IndicatorRead(ApiModel):
    id: uuid.UUID
    code: str
    category_code: str
    name_key: str
    description_key: str
    unit: str
    direction: str
    preferred_geo_level: str
    normalization_method: str
    official_only: bool


class ObservationRead(ApiModel):
    id: uuid.UUID
    indicator_code: str
    location_slug: str
    period_start: date
    period_end: date
    value: float
    unit: str
    organization: str
    source_dataset: str
    source_url: str
    retrieved_at: datetime
    published_at: datetime | None
    geographic_level: str
    quality_status: str
    methodology_version: str
    evidence_type: str
    transformations: list[str]
    inherited_from_location: str | None = None


class Household(ApiModel):
    adults: Annotated[int, Field(ge=1, le=12)] = 1
    children: Annotated[int, Field(ge=0, le=12)] = 0


class Constraint(ApiModel):
    indicator_code: str
    operator: Literal["lte", "gte", "eq"]
    value: float
    required: bool = True


class RankingRequest(ApiModel):
    location_type: Literal["country", "state", "district", "city"] = "city"
    countries: list[str] = Field(default_factory=lambda: ["DE"], min_length=1)
    location_slugs: list[str] = Field(default_factory=list, max_length=4)
    household: Household = Field(default_factory=Household)
    weights: dict[str, Annotated[float, Field(ge=0, le=100)]]
    constraints: list[Constraint] = Field(default_factory=list)
    reference_year: int | None = Field(default=None, ge=1990, le=2100)

    @model_validator(mode="after")
    def weights_must_total_one_hundred(self) -> "RankingRequest":
        total = sum(self.weights.values())
        if abs(total - 100) > 0.01:
            raise ValueError("validation.weights_total")
        return self


class IndicatorContribution(ApiModel):
    indicator_code: str
    category_code: str
    raw_value: float
    unit: str
    score: float | None
    weight: float
    quality_coefficient: float
    evidence_type: str
    observation: ObservationRead


class RankingItem(ApiModel):
    location: LocationRead
    destination_score: float | None
    data_coverage: float
    methodological_confidence: Literal["high", "medium", "low", "insufficient"]
    confidence_coefficient: float
    constraints_met: bool
    failed_constraints: list[str]
    indicators: list[IndicatorContribution]
    missing_indicator_codes: list[str]


class RankingResponse(ApiModel):
    id: uuid.UUID
    methodology_version: str
    created_at: datetime
    results: list[RankingItem]
    warnings: list[str]
