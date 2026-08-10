import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.destinations.models import AdministrativeRegion
from app.map.models import RegionBoundary
from app.map.service import simplify_map_polygons

MAP_PACK_VERSION = "china-v1"
MAP_PACK_PATH = Path(__file__).resolve().parents[2] / "data" / "map-packs" / f"{MAP_PACK_VERSION}.json"


@dataclass(frozen=True)
class MapPackMetadata:
    version: str
    byte_size: int
    md5: str


def metadata_for(path: Path) -> MapPackMetadata:
    content = path.read_bytes()
    return MapPackMetadata(MAP_PACK_VERSION, len(content), hashlib.md5(content).hexdigest())


def build_map_pack(session: Session, destination: Path = MAP_PACK_PATH) -> MapPackMetadata:
    rows = session.execute(select(AdministrativeRegion, RegionBoundary).join(RegionBoundary)).all()
    regions = [
        {"region_code": region.code, "name": region.name, "level": region.level,
         "center": [boundary.center_longitude, boundary.center_latitude],
         "polygons": simplify_map_polygons(boundary.polygons)}
        for region, boundary in rows if region.level in {"province", "city"}
    ]
    content = json.dumps({"version": MAP_PACK_VERSION, "regions": regions}, ensure_ascii=False, separators=(",", ":")).encode()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)
    return metadata_for(destination)
