from pathlib import Path

from app.db.session import create_engine_for_url


def test_sqlite_engine_enables_wal_and_foreign_keys(tmp_path: Path) -> None:
    database_path = tmp_path / "travel-test.db"
    engine = create_engine_for_url(f"sqlite:///{database_path}")

    with engine.connect() as connection:
        journal_mode = connection.exec_driver_sql("PRAGMA journal_mode").scalar_one()
        foreign_keys = connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one()

    assert journal_mode.lower() == "wal"
    assert foreign_keys == 1
