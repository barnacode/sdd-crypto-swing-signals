"""FastAPI application factory (T021/T023).

Builds the private read API: CORS restricted to the dashboard origin, slowapi rate limiting,
and the signals router (API-key protected). Health is the only public route. The app binds to
loopback / the Docker network in deployment (C-6, AC-07) — that is a uvicorn/compose concern,
not application code. There is no order-execution route (C-1, FR-023).
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from aegis.api.routers import market, signals
from aegis.config.settings import Settings
from aegis.persistence.base import make_engine, make_sessionmaker


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    app = FastAPI(title="AEGIS Internal API", version="1.0.0-mvp")
    app.state.settings = settings
    app.state.sessionmaker = make_sessionmaker(make_engine(settings.db_dsn))

    limiter = Limiter(key_func=get_remote_address, default_limits=["600/minute"])
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
    app.add_middleware(SlowAPIMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.dashboard_origin],
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    app.include_router(signals.router, prefix="/api/v1")
    app.include_router(market.router, prefix="/api/v1")

    @app.get("/api/v1/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
