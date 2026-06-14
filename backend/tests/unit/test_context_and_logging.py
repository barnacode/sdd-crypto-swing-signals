"""ContextProvider merge (T019) + logging config (T011) unit tests."""

from __future__ import annotations

from aegis.config.logging import configure_logging, get_logger
from aegis.ingestion.context import merge_security_flags


def test_merge_security_flags_dedups_by_asset_source():
    a = [{"asset": "BTC", "source": "PeckShield", "severity": "high"}]
    b = [
        {"asset": "BTC", "source": "PeckShield", "severity": "high"},  # duplicate
        {"asset": "ETH", "source": "DeFi", "severity": "med"},
    ]
    merged = merge_security_flags([a, b])
    assert len(merged) == 2
    assert {(f["asset"], f["source"]) for f in merged} == {("BTC", "PeckShield"), ("ETH", "DeFi")}


def test_logging_configures_and_emits():
    configure_logging("INFO")
    log = get_logger("test")
    log.info("event", key="value")  # must not raise or leak
    assert log is not None
