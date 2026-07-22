import json

import httpx
from norevia_pipeline.contracts import CandidateObservation, RawArtifact
from norevia_pipeline.sources.base import HttpSourceAdapter


class EurostatAdapter(HttpSourceAdapter):
    source_code = "eurostat"
    base_url = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"

    async def check_availability(self) -> bool:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.head("https://ec.europa.eu/eurostat/api/dissemination")
            return response.status_code < 500

    async def download(self, dataset_code: str, **dimensions: str) -> RawArtifact:
        return await self._preserve(
            dataset_code=dataset_code,
            url=f"{self.base_url}/{dataset_code}",
            params={"lang": "en", **dimensions},
        )

    def transform(self, artifact: RawArtifact) -> list[CandidateObservation]:
        payload = json.loads(artifact.path.read_text(encoding="utf-8"))
        if not {"id", "size", "dimension", "value"}.issubset(payload):
            raise ValueError("Eurostat response is not JSON-stat 2.0 compatible")
        # Dataset-specific dimension-to-indicator mappings are required at registration time.
        # Returning no observations prevents accidental semantic guesses.
        return []
