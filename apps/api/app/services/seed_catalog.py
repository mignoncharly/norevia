import asyncio
import json
import uuid
from pathlib import Path

from app.database import SessionFactory
from app.models.entities import (
    Category,
    Direction,
    EvidenceType,
    Indicator,
    Location,
    LocationType,
    Source,
)
from sqlalchemy import select

CATEGORIES = [
    "education",
    "employment",
    "inclusion",
    "housing",
    "health",
    "safety",
    "cost_of_living",
    "mobility",
    "environment",
    "climate",
    "digital",
    "entrepreneurship",
]
STATES = [
    ("baden-wuerttemberg", "Baden-Württemberg", "08"),
    ("bavaria", "Bavaria", "09"),
    ("berlin-state", "Berlin", "11"),
    ("brandenburg", "Brandenburg", "12"),
    ("bremen-state", "Bremen", "04"),
    ("hamburg-state", "Hamburg", "02"),
    ("hesse", "Hesse", "06"),
    ("lower-saxony", "Lower Saxony", "03"),
    ("mecklenburg-western-pomerania", "Mecklenburg-Western Pomerania", "13"),
    ("north-rhine-westphalia", "North Rhine-Westphalia", "05"),
    ("rhineland-palatinate", "Rhineland-Palatinate", "07"),
    ("saarland", "Saarland", "10"),
    ("saxony", "Saxony", "14"),
    ("saxony-anhalt", "Saxony-Anhalt", "15"),
    ("schleswig-holstein", "Schleswig-Holstein", "01"),
    ("thuringia", "Thuringia", "16"),
]
CITIES = [
    ("berlin", "Berlin", "11000000", 52.5200, 13.4050),
    ("hamburg", "Hamburg", "02000000", 53.5511, 9.9937),
    ("munich", "Munich", "09162000", 48.1351, 11.5820),
    ("cologne", "Cologne", "05315000", 50.9375, 6.9603),
    ("frankfurt", "Frankfurt am Main", "06412000", 50.1109, 8.6821),
    ("stuttgart", "Stuttgart", "08111000", 48.7758, 9.1829),
    ("duesseldorf", "Düsseldorf", "05111000", 51.2277, 6.7735),
    ("leipzig", "Leipzig", "14713000", 51.3397, 12.3731),
    ("dortmund", "Dortmund", "05913000", 51.5136, 7.4653),
    ("essen", "Essen", "05113000", 51.4556, 7.0116),
    ("bremen", "Bremen", "04011000", 53.0793, 8.8017),
    ("dresden", "Dresden", "14612000", 51.0504, 13.7373),
    ("hanover", "Hanover", "03241001", 52.3759, 9.7320),
    ("nuremberg", "Nuremberg", "09564000", 49.4521, 11.0767),
]


async def seed() -> None:
    catalog_path = Path(__file__).parents[4] / "packages" / "indicator-catalog" / "catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    async with SessionFactory() as session:
        top_categories: dict[str, Category] = {}
        for order, code in enumerate(CATEGORIES):
            item = await session.scalar(select(Category).where(Category.code == code))
            if item is None:
                item = Category(id=uuid.uuid4(), code=code, sort_order=order)
                session.add(item)
            top_categories[code] = item
        await session.flush()

        subcategories: dict[tuple[str, str], Category] = {}
        for entry in catalog:
            key = (entry["category"], entry["subcategory"])
            if key in subcategories:
                continue
            code = f"{key[0]}.{key[1]}"
            item = await session.scalar(select(Category).where(Category.code == code))
            if item is None:
                item = Category(
                    id=uuid.uuid4(),
                    code=code,
                    parent_id=top_categories[key[0]].id,
                    sort_order=len(subcategories),
                )
                session.add(item)
            subcategories[key] = item
        await session.flush()

        for entry in catalog:
            indicator = await session.scalar(
                select(Indicator).where(Indicator.code == entry["code"])
            )
            subcategory = subcategories[(entry["category"], entry["subcategory"])]
            if indicator is None:
                indicator = Indicator(
                    id=uuid.uuid4(),
                    code=entry["code"],
                    category_id=subcategory.id,
                    name_key=f"indicators.{entry['code']}.name",
                    description_key=f"indicators.{entry['code']}.description",
                    unit=entry["unit"],
                    direction=Direction(entry["direction"]),
                    preferred_geo_level=LocationType(entry["geoLevel"]),
                    official_only=entry.get("evidenceType") is None,
                )
                session.add(indicator)
            else:
                indicator.category_id = subcategory.id

        country = await session.scalar(select(Location).where(Location.slug == "germany"))
        if country is None:
            country = Location(
                id=uuid.uuid4(),
                slug="germany",
                name="Germany",
                location_type=LocationType.COUNTRY,
                iso_country_code="DE",
                official_geo_code="DE",
            )
            session.add(country)
            await session.flush()
        state_by_code: dict[str, Location] = {}
        for slug, name, code in STATES:
            state = await session.scalar(select(Location).where(Location.slug == slug))
            if state is None:
                state = Location(
                    id=uuid.uuid4(),
                    slug=slug,
                    name=name,
                    location_type=LocationType.STATE,
                    parent_location_id=country.id,
                    iso_country_code="DE",
                    official_geo_code=code,
                )
                session.add(state)
            state_by_code[code] = state
        await session.flush()
        for slug, name, code, lat, lon in CITIES:
            city = await session.scalar(select(Location).where(Location.slug == slug))
            if city is None:
                city = Location(
                    id=uuid.uuid4(),
                    slug=slug,
                    name=name,
                    location_type=LocationType.CITY,
                    parent_location_id=state_by_code[code[:2]].id,
                    iso_country_code="DE",
                    official_geo_code=code,
                    latitude=lat,
                    longitude=lon,
                )
                session.add(city)
            else:
                city.parent_location_id = state_by_code[code[:2]].id
        for organization, dataset, endpoint in [
            (
                "Statistisches Bundesamt (Destatis)",
                "GENESIS-Online",
                "https://www-genesis.destatis.de/genesisWS/rest/2020/",
            ),
            (
                "Eurostat",
                "Eurostat Data Browser",
                "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/",
            ),
        ]:
            if not await session.scalar(
                select(Source.id).where(
                    Source.organization == organization, Source.dataset_name == dataset
                )
            ):
                session.add(
                    Source(
                        id=uuid.uuid4(),
                        organization=organization,
                        dataset_name=dataset,
                        official_status=True,
                        evidence_type=EvidenceType.OFFICIAL,
                        api_endpoint=endpoint,
                        update_frequency="dataset-specific",
                    )
                )
        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed())
