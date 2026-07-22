from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class RawArtifact:
    source_code: str
    dataset_code: str
    path: Path
    sha256: str
    retrieved_at: datetime
    source_url: str
    content_type: str


@dataclass(frozen=True)
class CandidateObservation:
    indicator_code: str
    official_geo_code: str
    location_type: str
    period_start: date
    period_end: date
    value: Decimal
    unit: str
    source_code: str
    source_dataset: str
    source_url: str
    retrieved_at: datetime
    published_at: datetime | None
    methodology_version: str
    quality_status: str = "PROVISIONAL"
    transformations: tuple[str, ...] = field(default_factory=tuple)
    series_break: bool = False


class SourceAdapter(Protocol):
    source_code: str

    async def check_availability(self) -> bool: ...
    async def download(self, dataset_code: str) -> RawArtifact: ...
    def transform(self, artifact: RawArtifact) -> list[CandidateObservation]: ...
