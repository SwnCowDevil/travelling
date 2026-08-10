import hashlib
import json

from app.destinations.models import AdministrativeRegion
from app.map.models import RegionBoundary
from app.map.pack import build_map_pack


def test_build_map_pack_writes_compact_geometry(db_session, tmp_path) -> None:
    db_session.add_all([
        AdministrativeRegion(code="330000", name="浙江", level="province"),
        RegionBoundary(region_code="330000", center_longitude=120, center_latitude=30,
                       polygons=[[[float(i), float(i % 7)] for i in range(900)]], source="amap"),
    ])
    db_session.commit()
    path = tmp_path / "china-v1.json"
    metadata = build_map_pack(db_session, path)
    payload = json.loads(path.read_text())
    assert metadata.byte_size == path.stat().st_size
    assert metadata.md5 == hashlib.md5(path.read_bytes()).hexdigest()
    assert sum(len(path) for path in payload["regions"][0]["polygons"]) <= 80
