from app.db.session import SessionLocal
from app.map.pack import MAP_PACK_PATH, build_map_pack


def main() -> None:
    with SessionLocal() as session:
        metadata = build_map_pack(session)
    print(f"version={metadata.version} bytes={metadata.byte_size} path={MAP_PACK_PATH}")


if __name__ == "__main__":
    main()
