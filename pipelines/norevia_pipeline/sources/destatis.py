import httpx
from norevia_pipeline.contracts import CandidateObservation, RawArtifact
from norevia_pipeline.sources.base import HttpSourceAdapter


class DestatisAdapter(HttpSourceAdapter):
    source_code = "destatis"
    base_url = "https://www-genesis.destatis.de/genesisWS/rest/2020"

    def __init__(self, raw_root, username: str = "GAST", password: str = "GAST") -> None:
        super().__init__(raw_root)
        self.credentials = {"username": username, "password": password}

    async def check_availability(self) -> bool:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{self.base_url}/helloworld/logincheck", params=self.credentials
            )
            return response.status_code == 200

    async def download(self, dataset_code: str) -> RawArtifact:
        return await self._preserve(
            dataset_code=dataset_code,
            url=f"{self.base_url}/data/tablefile",
            params={
                **self.credentials,
                "name": dataset_code,
                "area": "all",
                "format": "csv",
                "language": "en",
            },
        )

    def transform(self, artifact: RawArtifact) -> list[CandidateObservation]:
        # GENESIS tables vary by table code. A registered mapping must provide column,
        # unit and geographic semantics before CandidateObservation objects are emitted.
        return []
