from pathlib import Path

from app.db.session import SessionLocal
from app.destinations.seed import seed_destinations


def main() -> None:
    catalog_path = Path(__file__).parents[2] / "data" / "destinations.v1.json"
    with SessionLocal() as session:
        result = seed_destinations(session, catalog_path)
    print(f"Destination catalog seeded: created={result.created}, updated={result.updated}")


if __name__ == "__main__":
    main()
