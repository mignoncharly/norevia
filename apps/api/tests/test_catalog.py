import json
from pathlib import Path


def test_germany_v1_catalog_has_exactly_fifty_unique_indicators() -> None:
    path = Path(__file__).parents[3] / "packages" / "indicator-catalog" / "catalog.json"
    catalog = json.loads(path.read_text(encoding="utf-8"))
    codes = [item["code"] for item in catalog]
    assert len(codes) == 50
    assert len(set(codes)) == 50
    assert {item["category"] for item in catalog} >= {
        "education",
        "inclusion",
        "employment",
        "housing",
        "health",
        "safety",
        "cost_of_living",
        "climate",
    }
