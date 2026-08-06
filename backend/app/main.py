from fastapi import FastAPI

from app.ai.router import router as ai_profile_router
from app.auth.router import router as auth_router
from app.recommendations.router import router as recommendations_router
from app.weather.router import router as weather_router


def create_app() -> FastAPI:
    app = FastAPI(title="Travel Recommendation API")
    app.include_router(auth_router)
    app.include_router(ai_profile_router)
    app.include_router(recommendations_router)
    app.include_router(weather_router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
