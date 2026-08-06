import json
from pathlib import Path

import pytest

from app.destinations.models import AdministrativeRegion, Destination
from app.destinations.seed import SeedValidationError, seed_destinations


def write_seed(path: Path, *, months: list[int] | None = None) -> None:
    path.write_text(
        json.dumps(
            {
                "version": "v1",
                "destinations": [
                    {
                        "code": "zj-hangzhou-west-lake",
                        "name": "杭州西湖",
                        "latitude": 30.25,
                        "longitude": 120.15,
                        "region_code": "330000",
                        "categories": ["城市", "人文", "景色"],
                        "suitable_months": months or [3, 4, 5, 9, 10, 11],
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def test_seed_is_idempotent(db_session, tmp_path: Path) -> None:
    db_session.add(AdministrativeRegion(code="330000", name="浙江省", level="province"))
    db_session.commit()
    seed_path = tmp_path / "seed.json"
    write_seed(seed_path)

    first = seed_destinations(db_session, seed_path)
    second = seed_destinations(db_session, seed_path)

    assert (first.created, first.updated) == (1, 0)
    assert (second.created, second.updated) == (0, 1)
    assert db_session.query(Destination).count() == 1


def test_seed_rejects_invalid_month(db_session, tmp_path: Path) -> None:
    db_session.add(AdministrativeRegion(code="330000", name="浙江省", level="province"))
    db_session.commit()
    seed_path = tmp_path / "seed.json"
    write_seed(seed_path, months=[13])

    with pytest.raises(SeedValidationError, match="month"):
        seed_destinations(db_session, seed_path)


def test_catalog_has_150_unique_destinations_covering_all_provinces(db_session) -> None:
    catalog_path = Path(__file__).parents[2] / "data" / "destinations.v1.json"

    result = seed_destinations(db_session, catalog_path)
    destinations = db_session.query(Destination).all()

    assert result.created == 150
    assert len(destinations) == 150
    assert len({item.code for item in destinations}) == 150
    assert len({item.region_code for item in destinations}) == 34
    verified = [item for item in destinations if item.coordinate_verified]
    unresolved = [item for item in destinations if not item.coordinate_verified]
    assert len(verified) == 146
    assert {item.region_code for item in unresolved} == {"710000"}
