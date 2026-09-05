from fastapi import FastAPI

from green_v2.api.routes.health import router as health_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="綠能 V2 API",
        version="0.1.0",
        description="與既有綠能環境隔離的模組化重寫服務",
    )
    app.include_router(health_router)
    return app


app = create_app()

