from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import agent, datasets
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="AI-powered conversational analytics API.",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # production me specific domain use karna
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes
    app.include_router(
        datasets.router,
        prefix="/datasets",
        tags=["datasets"]
    )

    app.include_router(
        agent.router,
        prefix="/agent",
        tags=["agent"]
    )

    # Health Check
    @app.get("/health", tags=["system"])
    async def health_check():
        return {
            "status": "ok",
            "service": settings.app_name
        }

    return app


app = create_app()
