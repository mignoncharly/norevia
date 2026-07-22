import hashlib
import re
from datetime import UTC, datetime
from pathlib import Path

import httpx
from norevia_pipeline.contracts import RawArtifact

SAFE_DATASET_CODE = re.compile(r"[A-Za-z0-9_.-]{1,128}\Z")


class HttpSourceAdapter:
    source_code: str

    def __init__(self, raw_root: Path, timeout_seconds: float = 60) -> None:
        self.raw_root = raw_root
        self.timeout = httpx.Timeout(timeout_seconds, connect=15)

    async def _preserve(
        self, *, dataset_code: str, url: str, params: dict[str, str] | None = None
    ) -> RawArtifact:
        if not SAFE_DATASET_CODE.fullmatch(dataset_code):
            raise ValueError("Dataset code contains unsupported path characters")
        retrieved_at = datetime.now(UTC)
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            response = await client.get(
                url, params=params, headers={"User-Agent": "Norevia/0.1 data-pipeline"}
            )
            response.raise_for_status()
        payload = response.content
        digest = hashlib.sha256(payload).hexdigest()
        destination = (
            self.raw_root / self.source_code / dataset_code / retrieved_at.strftime("%Y/%m/%d")
        )
        destination.mkdir(parents=True, exist_ok=True)
        path = destination / f"{digest}.raw"
        if not path.exists():
            path.write_bytes(payload)
        return RawArtifact(
            self.source_code,
            dataset_code,
            path,
            digest,
            retrieved_at,
            str(response.url),
            response.headers.get("content-type", "application/octet-stream"),
        )
