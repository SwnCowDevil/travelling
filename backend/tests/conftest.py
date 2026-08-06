from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base, import_models
from app.db.session import create_engine_for_url


@pytest.fixture
def db_session(tmp_path: Path) -> Iterator[Session]:
    import_models()
    engine = create_engine_for_url(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as session:
        yield session
    engine.dispose()
