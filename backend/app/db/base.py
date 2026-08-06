from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def import_models() -> None:
    from app.ai import models as ai_models  # noqa: F401
    from app.destinations import models as destination_models  # noqa: F401
    from app.footprints import models as footprint_models  # noqa: F401
    from app.guides import models as guide_models  # noqa: F401
    from app.recommendations import models as recommendation_models  # noqa: F401
    from app.users import models as user_models  # noqa: F401
    from app.visits import models as visit_models  # noqa: F401
