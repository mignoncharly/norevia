import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from geoalchemy2 import Geometry
from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class LocationType(enum.StrEnum):
    COUNTRY = "country"
    STATE = "state"
    DISTRICT = "district"
    CITY = "city"
    NEIGHBORHOOD = "neighborhood"


class Direction(enum.StrEnum):
    HIGHER_IS_BETTER = "HIGHER_IS_BETTER"
    LOWER_IS_BETTER = "LOWER_IS_BETTER"
    TARGET_RANGE = "TARGET_RANGE"
    DESCRIPTIVE_ONLY = "DESCRIPTIVE_ONLY"


class EvidenceType(enum.StrEnum):
    OFFICIAL = "OFFICIAL"
    REPRESENTATIVE_SURVEY = "REPRESENTATIVE_SURVEY"
    RESIDENT_PERCEPTION = "RESIDENT_PERCEPTION"
    USER_REPORTED = "USER_REPORTED"


class QualityStatus(enum.StrEnum):
    VALIDATED = "VALIDATED"
    PROVISIONAL = "PROVISIONAL"
    ESTIMATED = "ESTIMATED"
    STALE = "STALE"
    REJECTED = "REJECTED"


class Category(Base):
    __tablename__ = "categories"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("categories.id"))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class Location(Base):
    __tablename__ = "locations"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    location_type: Mapped[LocationType] = mapped_column(
        Enum(LocationType, name="location_type"), index=True
    )
    parent_location_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("locations.id"), index=True
    )
    iso_country_code: Mapped[str] = mapped_column(String(2), index=True)
    official_geo_code: Mapped[str | None] = mapped_column(String(40), index=True)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    geometry: Mapped[object | None] = mapped_column(
        Geometry("GEOMETRY", srid=4326, spatial_index=True)
    )
    population: Mapped[int | None] = mapped_column(Integer)
    valid_from: Mapped[date | None] = mapped_column(Date)
    valid_to: Mapped[date | None] = mapped_column(Date)
    parent: Mapped["Location | None"] = relationship(remote_side=[id])


class Indicator(Base):
    __tablename__ = "indicators"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    category_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("categories.id"), index=True)
    description_key: Mapped[str] = mapped_column(String(180))
    name_key: Mapped[str] = mapped_column(String(180))
    unit: Mapped[str] = mapped_column(String(60))
    direction: Mapped[Direction] = mapped_column(Enum(Direction, name="indicator_direction"))
    value_type: Mapped[str] = mapped_column(String(30), default="number")
    preferred_geo_level: Mapped[LocationType] = mapped_column(
        Enum(LocationType, name="preferred_geo_level")
    )
    normalization_method: Mapped[str] = mapped_column(String(40), default="winsorized_minmax")
    official_only: Mapped[bool] = mapped_column(Boolean, default=True)
    target_min: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    target_max: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Source(Base):
    __tablename__ = "sources"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization: Mapped[str] = mapped_column(String(200))
    dataset_name: Mapped[str] = mapped_column(String(300))
    official_status: Mapped[bool] = mapped_column(Boolean)
    evidence_type: Mapped[EvidenceType] = mapped_column(Enum(EvidenceType, name="evidence_type"))
    license: Mapped[str | None] = mapped_column(String(200))
    api_endpoint: Mapped[str | None] = mapped_column(Text)
    update_frequency: Mapped[str | None] = mapped_column(String(80))
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_expected_update: Mapped[date | None] = mapped_column(Date)
    __table_args__ = (UniqueConstraint("organization", "dataset_name"),)


class Observation(Base):
    __tablename__ = "observations"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    indicator_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("indicators.id"), index=True)
    location_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("locations.id"), index=True)
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    value: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    unit: Mapped[str] = mapped_column(String(60))
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sources.id"), index=True)
    source_dataset: Mapped[str] = mapped_column(String(300))
    source_url: Mapped[str] = mapped_column(Text)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    geographic_level: Mapped[LocationType] = mapped_column(
        Enum(LocationType, name="observation_geo_level")
    )
    quality_status: Mapped[QualityStatus] = mapped_column(
        Enum(QualityStatus, name="quality_status")
    )
    methodology_version: Mapped[str] = mapped_column(String(120))
    transformations: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    import_batch_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("import_batches.id"))
    indicator: Mapped[Indicator] = relationship()
    location: Mapped[Location] = relationship()
    source: Mapped[Source] = relationship()
    __table_args__ = (
        UniqueConstraint(
            "indicator_id",
            "location_id",
            "period_start",
            "period_end",
            "source_id",
            "methodology_version",
        ),
        Index("ix_observations_latest", "indicator_id", "location_id", "period_end"),
    )


class ImportBatch(Base):
    __tablename__ = "import_batches"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sources.id"))
    raw_object_key: Mapped[str] = mapped_column(Text)
    raw_sha256: Mapped[str] = mapped_column(String(64))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(30))
    validation_report: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)


class Profile(Base):
    __tablename__ = "profiles"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String(200), index=True)
    name: Mapped[str] = mapped_column(String(120))
    household_type: Mapped[str] = mapped_column(String(60))
    household_size: Mapped[int] = mapped_column(Integer)
    children_ages: Mapped[list[int]] = mapped_column(ARRAY(Integer), default=list)
    disposable_income: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    preferred_languages: Mapped[list[str]] = mapped_column(ARRAY(String(8)), default=list)
    attributes: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)


class ProfileWeight(Base):
    __tablename__ = "profile_weights"
    profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True
    )
    indicator_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("indicators.id"), primary_key=True)
    weight: Mapped[Decimal] = mapped_column(Numeric(8, 4))
    mandatory: Mapped[bool] = mapped_column(Boolean, default=False)
    minimum_acceptable_score: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))


class Ranking(Base):
    __tablename__ = "rankings"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str | None] = mapped_column(String(200), index=True)
    request_payload: Mapped[dict[str, object]] = mapped_column(JSON)
    result_payload: Mapped[dict[str, object]] = mapped_column(JSON)
    methodology_version: Mapped[str] = mapped_column(String(60))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
