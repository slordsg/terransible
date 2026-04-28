from fastapi import FastAPI

from app.db.migrate import migrate
from app.api.router import api_router


def create_app() -> FastAPI:
    app = FastAPI(title="Terraform+Ansible Config Service", version="0.1.0")

    @app.on_event("startup")
    def _startup() -> None:
        migrate()

    @app.get("/health")
    def health() -> dict:
        return {"ok": True}

    app.include_router(api_router)
    return app


app = create_app()

