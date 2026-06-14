# Quickstart — AEGIS MVP (local bring-up)

**Feature**: `001-aegis-mvp` | **Date**: 2026-06-13

Local, private, single-operator setup. Everything runs via Docker Compose with **no inbound public
exposure** (loopback / Docker network; remote access via VPN/Tailscale; TLS via Caddy/Traefik).

## Prerequisites
- Docker + Docker Compose
- Python 3.12 (for backend dev/tests), Node 20 (dashboard dev)
- TA-Lib C library available to the Python build
- Free-tier API keys in `.env` (never commit it — CLAUDE.md §8):
  `COINGECKO_DEMO_KEY`, `REDDIT_CLIENT_ID/SECRET`, `SANTIMENT_API_KEY`, `DEFI_API_KEY`,
  `FMP_API_KEY`, `FRED_API_KEY`, `COINGLASS_API_KEY`, `ETHERSCAN_KEY`, `TRONGRID_KEY`,
  `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `ANTHROPIC_API_KEY`.
  (Exchanges public, GDELT, RSS, FOMC dates need no key.)

## Bring-up
```bash
cp .env.example .env        # fill in the keys above
docker compose up -d        # timescaledb + backend + scheduler + dashboard + reverse proxy
docker compose exec backend alembic upgrade head   # create schema + hypertables + continuous aggregates
```

## Verify (smoke)
```bash
curl -k https://localhost/api/v1/health           # 200
curl -k -H "X-API-Key: $AEGIS_API_KEY" https://localhost/api/v1/symbols
# from the public internet the same call MUST fail/time out (AC-07)
```

## First-signal walkthrough (integration happy path — US1)
1. Scheduler ingests OHLCV (15m/1h) for the universe (BTC, ETH + top-20) with failover.
2. On a 1h candle close, indicators + regime are recomputed and persisted ≤ 5 s (AC-01).
3. Deterministic pre-gates G1–G5 run; if any fails, no candidate (no LLM spend).
4. Confluence rules + R:R ≥ 1:2 produce a `signal_candidate` with a complete order ticket.
5. `market-context` (Haiku) snapshot is read from cache; `signal-analyst` (Opus) decides emit/discard/watch.
6. `risk-guardian` checks sizing/exposure/correlation/free-capital; vetoes if needed.
7. Post-AI **reconciliation**: every figure must equal the persisted candidate (AC-04) — else discard + incident.
8. `alert-composer` posts a `SIGNAL` to Telegram with the order ticket, disclaimer, and ✅/❌ buttons,
   < 30 s from the candle close (SC-005). No order is placed (SC-011).
9. Tap `✅ Taken` → a real `position` is recorded and real P&L tracked (AC-19).

## Validation gate (before any live alerting — US5)
```bash
curl -k -X POST -H "Authorization: Bearer $JWT_ADMIN" https://localhost/api/v1/backtests -d @strategy.json
```
A strategy stays in **shadow mode** (logs only, no Telegram) until it passes the promotion gate:
precision ≥ 60%, PF ≥ 1.8, R:R ≥ 1:2, calibration ≤ 10%, **alpha-vs-HODL > 0** (AC-06/AC-16, C-5/C-13).

## Tests (TDD — written first, C-8)
```bash
docker compose exec backend pytest tests/unit tests/integration tests/contract -q
# coverage gate enforced in CI (CLAUDE.md §13)
```

## Safety checks you can assert locally
- No `/api/v1/**` route places/cancels an order (SC-011, C-1).
- A bad/invalid AI output yields **no** alert (fail-safe, AC-05).
- A figure mismatch between signal and candidate is rejected and logged (AC-04, SC-010).
- Dashboard exposes no order-placing controls (FR-022); shows the disclaimer (C-10).
