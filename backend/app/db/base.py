from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def import_models() -> None:
    from app.ai import models as ai_models  # noqa: F401
    from app.destinations import models as destination_models  # noqa: F401
    from app.users import models as user_models  # noqa: F401
