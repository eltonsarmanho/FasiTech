from __future__ import annotations

from fastapi import FastAPI

from api.routes import webhooks

app = FastAPI(title="FasiTech API")


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Endpoint simples de health-check."""
    return {"status": "ok"}


app.include_router(webhooks.router, prefix="/api", tags=["webhooks"])
