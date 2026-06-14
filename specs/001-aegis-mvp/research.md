# Phase 0 — Research & Decisions: AEGIS MVP

**Date**: 2026-06-13 | **Feature**: `001-aegis-mvp`

This document consolidates the technical decisions behind the plan. The closed stack (brief §3) is
binding, so most "unknowns" are not technology choices but **initial threshold/parameter values** for
deterred refinements (spec "Deferred to clarify"). These values are **starting points to be tuned by
backtest**; none blocks architecture or test design (C-8 tests are written against the values below
and re-run when tuning changes them).

---

## A. Technology decisions (closed stack — restated for traceability)

### A-1. Exchange data via ccxt async, public endpoints only
- **Decision**: ccxt `async_support`, `enableRateLimit=True`, per-venue backoff, paginated history via
  `since`. Failover order **Binance → MEXC → Coinbase → BitMart**.
- **Rationale**: unified interface; public-only ⇒ no keys, no fund risk (C-1/C-6). Binance/MEXC/
  Coinbase/BitMart confirmed for `fetch_ohlcv` (brief §4.1).
- **Alternatives rejected**: direct REST per exchange (duplicated effort); paid OHLCV (CoinAPI/CMC
  > €50, violates C-7).

### A-2. Indicators: TA-Lib (C engine) + pandas-ta-classic (idiomatic layer)
- **Decision**: TA-Lib for core math, `pandas-ta-classic` for idiomatic composition.
- **Rationale**: proven accuracy/speed (ADR-002).
- **⚠️ Hard exclusion**: original `pandas-ta` is FORBIDDEN (abandoned, supply-chain attack signals —
  deleted PyPI history, maintainer change). Pinned + audited deps (C-6, CLAUDE.md §9).

### A-3. Single store: PostgreSQL + TimescaleDB
- **Decision**: one store; hypertables for OHLC/indicators/derivatives, relational for the rest;
  continuous aggregates 1h→4h→1d.
- **Rationale**: time-series + relational in one engine; APScheduler jobstore co-located (ADR-003).
- **Alternatives rejected**: separate TSDB + RDBMS (operational overhead for a single-server MVP).

### A-4. Scheduler: APScheduler (AsyncIOScheduler, Postgres jobstore)
- **Decision**: single async scheduler in the same event loop as ccxt/FastAPI; jobs on 15m/1h candle
  close; `market-context` cached, refreshed every 1–2h or on event; `signal-analyst` invoked only
  when candidates exist.
- **Rationale**: a single local server does not need Celery; persistent jobstore survives restarts
  (ADR-010, C-7).

### A-5. AI layer: Claude Code skills, routed Haiku 4.5 + Opus 4.8
- **Decision**: `market-context` synthesis on **Haiku 4.5** (cheap, cached); final emit/discard/watch
  decision on **Opus 4.8** over already-filtered candidates only; low temperature; schema-validated
  structured output; single-round Bull/Bear debate. Token spend ≈ €15/month.
- **Rationale**: best quality/cost under the < €50/month ceiling (C-7, clarify session 2026-06-13).
- **Alternatives rejected**: Opus-for-everything (cost), single-Sonnet (loses Haiku savings + Opus
  decision depth), LangGraph/TradingAgents code adoption (non-determinism + token blow-up; taxonomy
  reused as concept only, ADR-009).

### A-6. Delivery: aiogram v3 (inbound + outbound)
- **Decision**: aiogram v3 from the start because the take/ignore confirmation loop needs inbound
  interactivity (ADR-019). Outbound alerts stay simple.
- **Alternatives rejected**: outbound-only Bot API (cannot capture confirmations for real P&L, C-16).

### A-7. Determinism boundary enforcement
- **Decision**: a post-AI reconciliation step asserts every figure in the emitted signal/order ticket
  is byte-identical to the persisted `signal_candidates`/`indicators` row; mismatch ⇒ discard +
  record incident (AC-04).
- **Rationale**: makes C-2 mechanically verifiable, not just a guideline.

### A-8. Validation engine: vectorbt + backtesting.py
- **Decision**: vectorbt for parameter sweeps (Numba-vectorized), backtesting.py for trade-by-trade
  debug; mandatory modeled fees (~0.1% taker) + slippage; walk-forward; deterministic outcome
  labeling feeds the alpha-vs-HODL benchmark (ADR-006/017).
- **Alternatives rejected**: tools with live-trading hooks (conflict with advisory-only C-1).

### A-9. Remote access: Cloudflare Zero Trust (Tunnel private-network + WARP)
- **Decision**: expose nothing publicly. A `cloudflared` **Tunnel runs in private-network mode (no
  public hostname)**; the operator reaches the dashboard/API only through **Cloudflare WARP** enrolled
  in the Zero Trust org. Service stays bound to loopback/Docker; the tunnel is outbound-only.
- **Rationale**: WARP is the VPN client, so this satisfies "remote access only via VPN" and "never on
  the public internet" (C-6, AC-07, FR-027, ADR-007) without opening any inbound port — and without a
  constitution amendment, since the principle is preserved, not relaxed.
- **Trade-off accepted**: Cloudflare sits in the control plane (a third party). Acceptable for the MVP;
  a fully self-hosted WireGuard/Tailscale path remains a no-third-party alternative if privacy needs tighten.
- **Alternatives rejected**: Cloudflare Tunnel with a **public hostname + Access** (reachable from the
  public internet even if login-gated → would contradict AC-07 and require a constitution amendment).

---

## B. Initial parameter values (deferred refinements — tunable by backtest)

> These resolve the spec's open "Deferred to clarify" items enough to **write tests and build the
> deterministic engine now**. They are defaults, not constitutional commitments; backtest tuning
> updates them (and their regression tests).

### B-1. Confluence & timeframes (brief §7.0–7.1) — LONG candidate requires ALL
- Base TF **1h**, entry confirmation **15m**, trend context **4h/1d**; holding hours–~2 days; no sub-15m.
- Trend: price > EMA50 > EMA200 (1h), 4h trend not bearish, **ADX ≥ 20**.
- Momentum: RSI(14) rising through 45→55, < 70.
- MACD: bullish cross, rising histogram.
- Volume: trigger candle ≥ 1.5× MA(volume, 20).
- Structure: confirmed resistance break or validated support bounce, confirmed on 15m.
- Volatility/stop: ATR(14) sets the technical stop; +5% target must be ≥ 2× stop distance (R:R ≥ 1:2).

### B-2. Deterministic pre-gates (brief §7.0b, G1–G5)
- **G1 Regime**: ADX ≥ 20 ⇒ trending; ATR percentile for volatility regime; no breakout LONG in weak
  ranging or extreme high-vol.
- **G2 BTC master**: **BTC bearish = 1d close < EMA200** ⇒ no altcoin LONG (clarify 2026-06-13);
  weight by BTC dominance; BTC/ETH judged on their own.
- **G3 Liquidity/spread**: pair must have enough 24h volume + depth/spread to fill €500–1,000 without
  material slippage; initial floor **≥ €5M 24h quote volume** (tunable).
- **G4 Derivatives sanity**: funding not extreme (initial band **|funding| ≤ 0.10%/8h**), coherent OI;
  massive recent liquidations ⇒ caution; very negative funding + support ⇒ possible squeeze (reinforce).
- **G5 Systemic**: no active stablecoin depeg (initial threshold **> 0.5% off $1** sustained) or
  serious exchange/chain incident; else global pause + `SYSTEMIC_ALERT` (C-14).

### B-3. Sizing (brief §7.4, ADR-012)
- `size = min(configured notional €500–1,000, size risking 2% of capital between entry and stop)`.
- Reference capital default **€3,000** (within €2–5k); aggregate risk cap **6%**; correlation cap
  (initial **|ρ| ≥ 0.8** treated as same bet); free-capital limit; daily-loss circuit breaker;
  per-symbol cooldown; **no global daily signal cap**.

### B-4. Exit plan (brief §7.4b, clarify 2026-06-13)
- **TP1 +3% closes 50%, move stop to breakeven; remainder trails toward ≥ +5%** with initial trailing
  **callback 1.2%** (tunable); early exit on invalidation. TP2 tier deferred (open item #9).

### B-5. Macro pre-event filter (brief §7.5, ADR-013)
- Window **12h before / 2h after**, market-wide.
- **Maximum impact** (FOMC rate decision, CPI, NFP) ⇒ blackout (no new LONG).
- **Medium impact** (PCE, retail sales, unemployment, FOMC minutes, FED speeches) ⇒ caution flag
  (reinforced confluence + reduced size). Exact event→impact mapping configurable (open item #3).

### B-6. Order ticket venue (clarify 2026-06-13)
- Default `target_exchange` **Binance spot** (native OCO); per-symbol venue mapping + failover; venues
  without native OCO degrade to `TP_SL` (two orders) + note (AC-11). Per-exchange capability matrix is
  a Phase-1 artifact and the precursor to future execution (ADR-011).

### B-7. Validation / promotion KPIs (brief §1.3, §13)
- Shadow/forward window **2–4 weeks** (default 3); promotion gate: precision ≥ 60%, profit factor
  ≥ 1.8, R:R ≥ 1:2, calibration error ≤ 10%, **alpha-vs-HODL > 0**; production circuit breaker demotes
  to shadow if precision < threshold for N signals (initial **N = 10**).

---

## C. Data providers (brief §4 — all €0 in MVP)

| Domain | Primary | Failover / cross-check | Keys |
|--------|---------|------------------------|------|
| OHLCV | Binance klines | MEXC → Coinbase → BitMart | none |
| Market cap / BTC dominance | CoinGecko free | — | `COINGECKO_DEMO_KEY` |
| Sentiment (regime filter) | Fear & Greed (daily) | Reddit OAuth, Santiment free | `REDDIT_*`, `SANTIMENT_API_KEY` |
| News / geo-macro | GDELT DOC 2.0 | CoinDesk/Cointelegraph RSS, CryptoPanic (free dies 2026-04-01 → RSS+GDELT fallback) | none |
| Macro calendar | FMP economic calendar | FRED, FOMC dates | `FMP_API_KEY`, `FRED_API_KEY` |
| Security/exploits | PeckShield (Telegram) | De.Fi REKT DB, rekt.news RSS | `DEFI_API_KEY` |
| Derivatives | Binance Futures public (funding/OI/long-short) | Coinglass free (liquidations) | `COINGLASS_API_KEY` |
| Systemic (depeg) | CoinGecko/exchange tickers | security feeds | — |
| On-chain (DIY) | Etherscan V2 / TronGrid / Blockscout | — | `ETHERSCAN_KEY`, `TRONGRID_KEY` |

> Sentiment is a **slow regime filter, not an intraday trigger** (free tiers lag: Fear&Greed daily,
> Santiment free +30d). Intraday triggers rest on price/volume/structure + near-real-time news/security
> (GDELT/PeckShield). Missing/late macro-calendar data is treated conservatively (uncertainty ⇒ blackout).

**Output**: all open items either resolved (clarify session) or assigned tunable initial values
above. No blocking `NEEDS CLARIFICATION` remains for Phase 1 design.
