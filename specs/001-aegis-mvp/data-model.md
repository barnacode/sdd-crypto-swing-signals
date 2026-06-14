# Phase 1 — Data Model: AEGIS MVP

**Date**: 2026-06-13 | **Feature**: `001-aegis-mvp` | **Store**: PostgreSQL + TimescaleDB (single source of truth)

Derived from the spec "Key Entities" and brief §14. Hypertables hold high-frequency time series;
relational tables hold signals and their lineage. **Every numeric figure originates in Python and is
persisted here before any AI sees it** (C-2). All money fields are EUR unless noted.

---

## Entity overview & lineage

```
ohlc ──► indicators ──► signal_candidates ──► signals ──► order_tickets
                            ▲                     │  ├──► ai_audit
derivatives ────────────────┤                     │  ├──► alerts
context / macro_events ─────┘                     │  └──► outcomes ──► positions
                                          strategies ◄── backtests
```

A `signal` is the AI-decided promotion of exactly one `signal_candidate`; it carries the auditable
decision (`ai_audit`), the executable `order_ticket`, the delivered `alerts`, the deterministic
`outcome`, and—if the operator confirms—a real `position`.

---

## Hypertables (time series)

### `ohlc`
| Field | Type | Notes |
|-------|------|-------|
| symbol | text | e.g. `BTC/USDT` |
| exchange | text | source venue (ccxt id) |
| tf | enum | `15m` `1h` `4h` `1d` |
| ts | timestamptz | candle open time (PK part) |
| open, high, low, close | numeric | |
| volume | numeric | base volume |
- **PK**: (symbol, exchange, tf, ts). Hypertable on `ts`. Idempotent upsert. Continuous aggregates roll 1h→4h→1d.

### `indicators`
| Field | Type | Notes |
|-------|------|-------|
| symbol, tf, ts | — | PK; one row per closed candle |
| ema50, ema200 | numeric | |
| rsi14 | numeric | |
| macd, macd_sig, macd_hist | numeric | |
| bb_upper, bb_mid, bb_lower | numeric | Bollinger |
| atr14 | numeric | stop sizing |
| adx14 | numeric | regime gate G1 |
| vol_rel | numeric | volume / MA(volume,20) |
| regime | enum | `trending` `ranging` `high_vol` |
- **Validation**: recomputed and persisted ≤ 5 s after candle close (AC-01). Recompute is idempotent.

### `derivatives`
| Field | Type | Notes |
|-------|------|-------|
| symbol, ts | — | PK |
| funding_rate | numeric | per-8h |
| open_interest | numeric | |
| long_short_ratio | numeric | |
| liquidations_24h | numeric | feeds gate G4 + context |

---

## Relational tables

### `context` (market-wide + per-symbol snapshot)
| Field | Type | Notes |
|-------|------|-------|
| ts | timestamptz | PK; refreshed every 1–2h or on event |
| fear_greed | int | 0–100 (daily, regime filter) |
| social_score | numeric | nullable (lagged source) |
| news | jsonb | array of {source, title, impact, ts} |
| geo_risk | numeric | GDELT tone |
| btc_dominance | numeric | |
| btc_state | enum | `bullish` `bearish` `neutral` (1d close vs EMA200) |
| security_flags | jsonb | array of active security alerts |
| systemic_flags | jsonb | array of depeg/exchange-incident flags |
| macro_blackout | bool | derived from `macro_events` window |
| global_pause | bool | systemic safeguard active (C-14) |

### `macro_events`
| Field | Type | Notes |
|-------|------|-------|
| id | uuid | PK |
| name | text | e.g. "FOMC rate decision" |
| category | text | |
| impact | enum | `maximum` `medium` |
| scheduled_at | timestamptz | |
| consensus, prior, actual | numeric | nullable |
| source | text | FMP / FRED / FOMC |
- **Window rule**: 12h before / 2h after; `maximum` ⇒ blackout, `medium` ⇒ caution (FR-008, AC-12/13).

### `signal_candidates` (deterministic output — the numeric source of truth)
| Field | Type | Notes |
|-------|------|-------|
| id | uuid | PK |
| symbol, tf, ts | — | |
| side | enum | `LONG` (MVP: long-only spot) |
| entry, stop, target | numeric | target ≥ +5% |
| rr | numeric | must be ≥ 2.0 or candidate not created (AC-03) |
| score | int | 0–100 confluence score |
| features | jsonb | indicator snapshot + gate results used by the AI |
- Created only after gates G1–G5 pass AND confluence holds AND R:R ≥ 1:2 (FR-005/006/007).

### `signals` (AI-decided)
| Field | Type | Notes |
|-------|------|-------|
| id | uuid | PK |
| candidate_id | uuid | FK → signal_candidates (1:1) |
| side, entry, stop, target, rr | — | **must match candidate exactly** (AC-04) |
| confidence | int | 0–100 calibrated |
| thesis, bull_case, bear_case, invalidation | text | |
| ai_rationale | text | summarized reasoning |
| status | enum | see state machine below |
| ts | timestamptz | |

### `order_tickets`
| Field | Type | Notes |
|-------|------|-------|
| signal_id | uuid | PK/FK (1:1) |
| entry_type | enum | `LIMIT` `MARKET` |
| entry_price | numeric | |
| quantity, notional | numeric | from sizing (FR-015) |
| order_structure | enum | `OCO` `TP_SL` `MARKET_TRAILING` |
| take_profit | numeric | |
| sl_trigger, sl_limit | numeric | |
| trailing | jsonb | {activation, callback} nullable |
| exit_plan | jsonb | TP1 +3% close 50% → BE, runner trails ≥ +5% |
| tif | enum | `GTC` default |
| target_exchange | text | Binance default; per-symbol mapping |
| valid_until | timestamptz | opportunity expiry |
- **Invariant**: every figure reconciles to the candidate/indicators; never placed/modified/cancelled (C-1, AC-09/11).

### `ai_audit`
| Field | Type | Notes |
|-------|------|-------|
| signal_id | uuid | PK/FK |
| prompt_hash | text | |
| inputs | jsonb | candidates + context passed to the AI |
| reasoning | text | summarized chain |
| model | text | `claude-opus-4-8` (decision) / `claude-haiku-4-5` (context) |
| ts | timestamptz | |

### `alerts`
| Field | Type | Notes |
|-------|------|-------|
| id | uuid | PK |
| signal_id | uuid | FK (nullable for SYSTEMIC/MACRO) |
| type | enum | `SIGNAL` `TRADE_MANAGEMENT` `INVALIDATED` `TARGET_HIT` `STOP_HIT` `SECURITY_ALERT` `MACRO_EVENT` `SYSTEMIC_ALERT` |
| channel | text | telegram |
| payload | jsonb | rendered message + inline buttons |
| sent_at | timestamptz | |

### `outcomes` (deterministic ground truth — never AI)
| Field | Type | Notes |
|-------|------|-------|
| signal_id | uuid | PK/FK |
| result | enum | `HIT` `STOP` `EXPIRED` |
| realized_pct | numeric | |
| closed_at | timestamptz | |
- HIT when +5% reached before stop within horizon (AC-08); computed by code.

### `positions` (real, operator-confirmed — C-16)
| Field | Type | Notes |
|-------|------|-------|
| id | uuid | PK |
| signal_id | uuid | FK |
| taken | bool | from inline confirmation (AC-19) |
| entry_fill | numeric | |
| qty | numeric | |
| partials | jsonb | scale-out events |
| stop_current | numeric | moved to BE after TP1 |
| status | enum | `open` `closed` `cancelled` |
| realized_pnl | numeric | **real** P&L, distinct from theoretical |
| source | enum | `manual` `cryptoledger` |

### `strategies` & `backtests`
| `strategies` | Type | Notes |
|--------------|------|-------|
| id, name | — | |
| params | jsonb | thresholds (research.md §B) |
| status | enum | `shadow` `production` `retired` |
| kpis | jsonb | precision, PF, R:R, calibration, alpha_vs_hodl |

| `backtests` | Type | Notes |
|-------------|------|-------|
| id | uuid | |
| strategy | text/FK | |
| params | jsonb | |
| metrics | jsonb | incl. `alpha_vs_hodl`, `calibration`, fees+slippage modeled |
| range | tstzrange | walk-forward window |
| created_at | timestamptz | |

### `users` / `api_keys` (auth)
| Field | Type | Notes |
|-------|------|-------|
| hash | text | API key hash / password hash |
| scopes | text[] | `read` `admin` |
| rotated_at | timestamptz | |

---

## State machines

### `signals.status`
```
candidate ──AI emits──► EMITTED ──delivered──► ACTIVE ──┬─ +5% before stop ─► TARGET_HIT
   │                       │                            ├─ stop hit ────────► STOPPED
   │ AI discards/          │ reconciliation             ├─ invalidation ────► INVALIDATED
   │ fail-safe             │ mismatch (AC-04)           └─ horizon elapsed ─► EXPIRED
   ▼                       ▼
DISCARDED               DISCARDED (incident recorded)
```
- `ACTIVE` only after the post-AI reconciliation passes; any mismatch → `DISCARDED` + incident (C-2/C-4).

### `strategies.status` (validation gate, C-5/C-13)
```
shadow ──passes promotion gate (incl. alpha-vs-HODL > 0)──► production
production ──precision < threshold for N signals──► shadow (circuit breaker)
any ──manual retire──► retired
```

### `positions.status`
```
open ──partial/BE/trail advisories──► open ──target/stop/manual close──► closed
open ──never filled / cancelled──► cancelled
```

---

## Cross-cutting validation rules
- R:R ≥ 1:2 enforced at candidate creation; non-compliant candidates are never created (AC-03).
- Signal figures must equal candidate/indicator figures byte-for-byte (AC-04, SC-010).
- No row in any table represents a placed order; `order_tickets` is advisory only (SC-011, C-1).
- `positions.realized_pnl` (real) and theoretical signal P&L are computed and reported separately (C-16).
- All API reads are private-network only; no table is exposed to the WAN (AC-07).
