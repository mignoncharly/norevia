from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.entities import Location, LocationType
from app.schemas.api import LocationRead

router = APIRouter(tags=["locations"])


@router.get("/locations", response_model=list[LocationRead])
async def list_locations(
    type: LocationType | None = None,
    country: str = "DE",
    session: AsyncSession = Depends(get_session),
) -> list[Location]:
    query = select(Location).where(
        Location.iso_country_code == country.upper(), Location.valid_to.is_(None)
    )
    if type:
        query = query.where(Location.location_type == type)
    return list((await session.scalars(query.order_by(Location.name))).all())


@router.get("/locations/{slug}", response_model=LocationRead)
async def get_location(slug: str, session: AsyncSession = Depends(get_session)) -> Location:
    location = await session.scalar(select(Location).where(Location.slug == slug))
    if location is None:
        raise HTTPException(
            404, detail={"code": "not_found", "messageKey": "errors.locationNotFound"}
        )
    return location
