from fastapi import FastAPI

from app.ai.router import router as ai_profile_router
from app.auth.router import router as auth_router
from app.destinations.router import router as destinations_router
from app.guides.router import router as guides_router
from app.map.router import router as map_router
from app.footprints.router import router as footprints_router
from app.recommendations.router import router as recommendations_router
from app.weather.router import router as weather_router
from app.visits.router import router as visits_router


def create_app() -> FastAPI:
    app = FastAPI(title="Travel Recommendation API")
    app.include_router(auth_router)
    app.include_router(destinations_router)
    app.include_router(ai_profile_router)
    app.include_router(recommendations_router)
    app.include_router(weather_router)
    app.include_router(guides_router)
    app.include_router(visits_router)
    app.include_router(footprints_router)
    app.include_router(map_router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
