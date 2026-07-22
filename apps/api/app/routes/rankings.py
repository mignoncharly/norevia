import uuid

from fastapi import APIRouter, Depends, HTTPException
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache import get_cache
from app.database import get_session
from app.models.entities import Ranking, Source
from app.schemas.api import RankingRequest, RankingResponse
from app.services.ranking import calculate_ranking

router = APIRouter(tags=["rankings"])
CACHE_TTL_SECONDS = 86_400


async def cache_result(cache: Redis, result: RankingResponse) -> None:
    try:
        await cache.set(
            f"ranking:{result.id}", result.model_dump_json(by_alias=True), ex=CACHE_TTL_SECONDS
        )
    except RedisError:
        pass


@router.post("/rankings", response_model=RankingResponse)
@router.post("/comparisons", response_model=RankingResponse)
async def create_ranking(
    request: RankingRequest,
    session: AsyncSession = Depends(get_session),
    cache: Redis = Depends(get_cache),
) -> RankingResponse:
    result = await calculate_ranking(session, request)
    session.add(
        Ranking(
            id=result.id,
            user_id=None,
            request_payload=request.model_dump(mode="json", by_alias=True),
            result_payload=result.model_dump(mode="json", by_alias=True),
            methodology_version=result.methodology_version,
            created_at=result.created_at,
        )
    )
    await session.commit()
    await cache_result(cache, result)
    return result


@router.get("/rankings/{ranking_id}", response_model=RankingResponse)
async def get_ranking(
    ranking_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    cache: Redis = Depends(get_cache),
) -> RankingResponse:
    try:
        cached = await cache.get(f"ranking:{ranking_id}")
    except RedisError:
        cached = None
    if cached:
        return RankingResponse.model_validate_json(cached)
    ranking = await session.get(Ranking, ranking_id)
    if ranking is None:
        raise HTTPException(
            404, detail={"code": "not_found", "messageKey": "errors.rankingNotFound"}
        )
    result = RankingResponse.model_validate(ranking.result_payload)
    await cache_result(cache, result)
    return result


@router.get("/sources/{source_id}")
async def get_source(
    source_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> dict[str, object]:
    source = await session.get(Source, source_id)
    if source is None:
        raise HTTPException(
            404, detail={"code": "not_found", "messageKey": "errors.sourceNotFound"}
        )
    return {
        "id": source.id,
        "organization": source.organization,
        "datasetName": source.dataset_name,
        "officialStatus": source.official_status,
        "evidenceType": source.evidence_type.value,
        "license": source.license,
        "apiEndpoint": source.api_endpoint,
        "updateFrequency": source.update_frequency,
        "lastCheckedAt": source.last_checked_at,
        "nextExpectedUpdate": source.next_expected_update,
    }
