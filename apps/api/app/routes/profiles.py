import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.entities import Indicator, Profile, ProfileWeight
from app.schemas.api import ApiModel
from app.security import current_user_id

router = APIRouter(tags=["profiles"])


class ProfileWeightInput(ApiModel):
    indicator_code: str
    weight: float = Field(ge=0, le=100)
    mandatory: bool = False
    minimum_acceptable_score: float | None = Field(default=None, ge=0, le=100)


class ProfileInput(ApiModel):
    name: str = Field(min_length=1, max_length=120)
    household_type: str = Field(min_length=1, max_length=60)
    household_size: int = Field(ge=1, le=24)
    children_ages: list[int] = Field(default_factory=list)
    disposable_income: Decimal | None = Field(default=None, ge=0)
    preferred_languages: list[str] = Field(default_factory=list)
    attributes: dict[str, object] = Field(default_factory=dict)
    weights: list[ProfileWeightInput] = Field(default_factory=list)


class ProfileRead(ProfileInput):
    id: uuid.UUID


async def serialize_profile(session: AsyncSession, profile: Profile) -> ProfileRead:
    rows = (
        await session.execute(
            select(ProfileWeight, Indicator.code)
            .join(Indicator)
            .where(ProfileWeight.profile_id == profile.id)
        )
    ).all()
    return ProfileRead(
        id=profile.id,
        name=profile.name,
        household_type=profile.household_type,
        household_size=profile.household_size,
        children_ages=profile.children_ages,
        disposable_income=profile.disposable_income,
        preferred_languages=profile.preferred_languages,
        attributes=profile.attributes,
        weights=[
            ProfileWeightInput(
                indicator_code=code,
                weight=float(item.weight),
                mandatory=item.mandatory,
                minimum_acceptable_score=float(item.minimum_acceptable_score)
                if item.minimum_acceptable_score is not None
                else None,
            )
            for item, code in rows
        ],
    )


async def replace_weights(
    session: AsyncSession, profile_id: uuid.UUID, weights: list[ProfileWeightInput]
) -> None:
    codes = {item.indicator_code for item in weights}
    indicators = list(
        (await session.scalars(select(Indicator).where(Indicator.code.in_(codes)))).all()
    )
    by_code = {item.code: item for item in indicators}
    missing = sorted(codes - set(by_code))
    if missing:
        raise HTTPException(
            422,
            detail={
                "code": "unknown_indicators",
                "messageKey": "errors.unknownIndicators",
                "context": {"codes": missing},
            },
        )
    await session.execute(delete(ProfileWeight).where(ProfileWeight.profile_id == profile_id))
    for item in weights:
        session.add(
            ProfileWeight(
                profile_id=profile_id,
                indicator_id=by_code[item.indicator_code].id,
                weight=item.weight,
                mandatory=item.mandatory,
                minimum_acceptable_score=item.minimum_acceptable_score,
            )
        )


@router.get("/profiles", response_model=list[ProfileRead])
async def list_profiles(
    user_id: str = Depends(current_user_id), session: AsyncSession = Depends(get_session)
) -> list[ProfileRead]:
    profiles = list(
        (
            await session.scalars(
                select(Profile).where(Profile.user_id == user_id).order_by(Profile.name)
            )
        ).all()
    )
    return [await serialize_profile(session, profile) for profile in profiles]


@router.post("/profiles", response_model=ProfileRead, status_code=201)
async def create_profile(
    payload: ProfileInput,
    user_id: str = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> ProfileRead:
    profile = Profile(
        id=uuid.uuid4(),
        user_id=user_id,
        name=payload.name,
        household_type=payload.household_type,
        household_size=payload.household_size,
        children_ages=payload.children_ages,
        disposable_income=payload.disposable_income,
        preferred_languages=payload.preferred_languages,
        attributes=payload.attributes,
    )
    session.add(profile)
    await session.flush()
    await replace_weights(session, profile.id, payload.weights)
    await session.commit()
    return await serialize_profile(session, profile)


@router.put("/profiles/{profile_id}", response_model=ProfileRead)
async def update_profile(
    profile_id: uuid.UUID,
    payload: ProfileInput,
    user_id: str = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> ProfileRead:
    profile = await session.scalar(
        select(Profile).where(Profile.id == profile_id, Profile.user_id == user_id)
    )
    if profile is None:
        raise HTTPException(
            404, detail={"code": "not_found", "messageKey": "errors.profileNotFound"}
        )
    profile.name = payload.name
    profile.household_type = payload.household_type
    profile.household_size = payload.household_size
    profile.children_ages = payload.children_ages
    profile.disposable_income = payload.disposable_income
    profile.preferred_languages = payload.preferred_languages
    profile.attributes = payload.attributes
    await replace_weights(session, profile.id, payload.weights)
    await session.commit()
    return await serialize_profile(session, profile)
