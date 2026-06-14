"""Scheduler wiring unit test (T020)."""

from __future__ import annotations

from aegis.ingestion.ohlcv import OhlcvIngestor
from aegis.scheduler import build_scheduler


def test_build_scheduler_registers_one_job_per_symbol():
    scheduler = build_scheduler(
        sessionmaker=None,  # type: ignore[arg-type]  -- not invoked; only registration is tested
        ingestor=OhlcvIngestor(["binance"]),
        symbols=["BTC/USDT", "ETH/USDT"],
    )
    jobs = scheduler.get_jobs()
    assert len(jobs) == 2
    assert scheduler.get_job("ingest:BTC/USDT:1h") is not None
    assert scheduler.get_job("ingest:ETH/USDT:1h") is not None
