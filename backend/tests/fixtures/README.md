# Test fixtures — provenance (real, traceable data)

Per CLAUDE.md §10 and C-8, test fixtures use **real, traceable market data** — never fabricated.

## `btcusdt_1h.json`
- **Source**: Binance public REST `GET /api/v3/klines` (no key required).
- **Request**: `symbol=BTCUSDT`, `interval=1h`, `limit=300`.
- **Captured**: 2026-06-14 (snapshot frozen for reproducible tests).
- **Format**: raw Binance kline arrays `[openTime, open, high, low, close, volume, closeTime, ...]`.
- **Use**: indicator-engine unit tests (EMA/RSI/MACD/BB/ATR/ADX/vol_rel/regime).

To refresh: re-run the documented request and commit the new snapshot (note the new capture date).
