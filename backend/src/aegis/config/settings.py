"""Application settings (T010).

Loaded from the environment with the ``AEGIS_`` prefix (and an optional ``.env``). Secrets stay
out of code (C-6 / CLAUDE.md §8); only non-secret defaults live here.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AEGIS_", env_file=".env", extra="ignore")

    db_dsn: str = "postgresql+asyncpg://aegis:aegis@127.0.0.1:5432/aegis"
    api_key: str = Field(default="change-me-internal-service-key")
    jwt_secret: str = Field(default="change-me-long-random-secret")
    # AI cost ceiling guidance (C-7); enforced by the cost monitor (T092).
    ai_monthly_eur_cap: float = 15.0
