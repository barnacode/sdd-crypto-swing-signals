"""Settings unit tests (T010)."""

from __future__ import annotations

from aegis.config.settings import Settings


def test_defaults_present():
    s = Settings()
    assert s.db_dsn.startswith("postgresql+asyncpg://")
    assert s.ai_monthly_eur_cap == 15.0


def test_env_override(monkeypatch):
    monkeypatch.setenv("AEGIS_DB_DSN", "postgresql+asyncpg://x:y@db:5432/z")
    monkeypatch.setenv("AEGIS_AI_MONTHLY_EUR_CAP", "25")
    s = Settings()
    assert s.db_dsn.endswith("/z")
    assert s.ai_monthly_eur_cap == 25.0
