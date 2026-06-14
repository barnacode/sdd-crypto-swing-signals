# Implementation Plan: AEGIS MVP — Advisory Short-Swing Crypto Signals

**Branch**: `001-aegis-mvp` | **Date**: 2026-06-13 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-aegis-mvp/spec.md` + `PROJECT-BRIEF.md` v1.3

## Summary

AEGIS is a private, local, 24/7 system that watches a curated crypto universe (BTC, ETH + ~top-20
by liquidity), computes technical indicators and market regime **deterministically in Python**, lets
a **Claude Code AI layer** reason over the resulting scored candidates, and delivers advisory
short-swing signals over Telegram with a complete, copy-paste-ready **order ticket** (entry, TP, SL,
OCO/trailing, size). Phase 1 is **advisory only** — the system never places, modifies, or cancels
orders. No strategy alerts live until it passes an automated validation gate that includes beating
risk-adjusted buy-and-hold.

**Technical approach**: an async Python monolith (modular, hexagonal-leaning) orchestrated by
APScheduler on each candle close, persisting everything to a single TimescaleDB store; a FastAPI read
API (the only data surface the AI may touch); an aiogram v3 Telegram bot for delivery and the
take/ignore confirmation loop; and a Next.js + lightweight-charts read-only dashboard. The AI layer
is a set of seven Claude Code skills with schema-validated structured I/O. The determinism boundary
(Python produces every number; the LLM only selects/weights/explains/decides) is enforced by a
post-AI numeric reconciliation check.

## Technical Context

**Language/Version**: Python 3.12 (backend/analysis); TypeScript / Node 20 (dashboard)
**Primary Dependencies**: ccxt (async, public endpoints only), TA-Lib + `pandas-ta-classic`
(⚠️ original `pandas-ta` FORBIDDEN — supply-chain risk), vectorbt + backtesting.py, APScheduler
(AsyncIOScheduler, Postgres jobstore), FastAPI + Pydantic v2, aiogram v3, slowapi (rate limit),
httpx; Next.js (React) + TradingView lightweight-charts; Claude Code skills on Opus 4.8 / Haiku 4.5
via the Anthropic API
**Storage**: PostgreSQL + TimescaleDB (single source of truth — hypertables for OHLC/indicators/
derivatives, relational tables for signals/alerts/outcomes/positions/strategies; continuous
aggregates 1h→4h→1d)
**Testing**: pytest + pytest-asyncio (backend, contract/integration/unit), schema validation tests
for AI structured output, vectorbt-backed strategy tests; Playwright/Vitest (dashboard)
**Target Platform**: single local Linux server via Docker Compose, 24/7, no inbound public exposure
(loopback/Docker network; remote access via VPN/Tailscale; TLS via Caddy/Traefik)
**Project Type**: web — backend (Python service) + frontend (Next.js dashboard) + Claude Code skills
**Performance Goals**: indicators recomputed and persisted ≤ 5 s after a 1h candle close (AC-01);
emitted signal reaches Telegram < 30 s from triggering candle close (SC-005); capture pipeline
≥ 99% uptime (SC-007)
**Constraints**: MVP data cost = €0; production < €50/month including AI tokens (AI ≈ €15/month via
Haiku-context + Opus-decision routing); advisory-only (zero orders placed — SC-011); zero numeric
hallucination reaches the operator (SC-010); fail-safe silence on any uncertainty
**Scale/Scope**: single private operator; ~22 symbols × 4 timeframes (15m/1h/4h/1d); ~2 signals/day
aspirational (uncapped, 0 on quiet days); 6 user stories, 27 FRs, 19 EARS acceptance criteria

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

Evaluated against constitution v1.0.0 (C-1…C-16). **Initial check: PASS** — the design is derived
from the constitution and introduces no violations.

| Principle | How the plan complies |
|-----------|------------------------|
| **C-1** Advisory only | No order-execution endpoint or capability exists; FastAPI exposes read + `/internal/signals` publish only; no exchange trading credentials anywhere (FR-023, AC-09). |
| **C-2** Determinism first | `indicators`/`candidates` modules produce every figure in Python and persist it; AI layer consumes via API and never originates numbers; post-AI reconciliation check (FR-004/009/010, AC-04). |
| **C-3** Auditable & reproducible | `ai_audit` persists prompt hash, inputs, summarized reasoning, model, decision; low temperature + schema-validated structured output (FR-011). |
| **C-4** Fail-safe | AI unavailability / invalid output / missing figure → no signal; incident recorded (FR-012, AC-05). |
| **C-5** Validation before production | Strategies stay in shadow mode until the validation pipeline + promotion gate pass; circuit breaker demotes on degradation (FR-024/025, AC-06). |
| **C-6** Private & secure | Loopback/Docker binding, VPN-only remote, TLS always, secrets in env/secrets, pinned+audited deps (FR-027, AC-07). |
| **C-7** Cost controlled | €0 data sources in MVP; AI routing Haiku-context + Opus-decision capped ≈ €15/mo; context cached, AI invoked only on filtered candidates, single-round debate (FR-013). |
| **C-8** TDD | Tests precede implementation; every bug fix ships a real-data regression test; one commit per task. Enforced by CLAUDE.md §2 and the tasks ordering. |
| **C-9** Zero tech debt | No `TODO: fix later`, no silenced errors; CLAUDE.md §7 + coverage gate. |
| **C-10** Not financial advice | Disclaimer in every alert and dashboard view (FR-026). |
| **C-11** Soundness over frequency | No daily cap; 0 signals when no confluence; gates never relaxed to hit cadence (Edge Cases, SC-006). |
| **C-12** Bounded sizing | Dual-constraint sizing, 6% aggregate cap, correlation cap, free-capital limit in `risk-guardian` (FR-015, AC-10). |
| **C-13** Beat HODL | Risk-adjusted alpha-vs-HODL is a hard promotion gate (FR-024/025, AC-16, SC-003). |
| **C-14** Systemic safeguards | Depeg/exchange-incident detection raises `SYSTEMIC_ALERT` + global pause (FR-005, AC-17). |
| **C-15** BTC rules | BTC master gate (1d close < EMA200 ⇒ bearish) blocks altcoin LONGs (FR-005, AC-14). |
| **C-16** Honest P&L | Theoretical vs real P&L separated; production metrics/throttle use real when present (FR-021, AC-19). |

**Result**: No violations. Complexity Tracking left empty.

## Project Structure

### Documentation (this feature)

```text
specs/001-aegis-mvp/
├── plan.md              # This file (/speckit.plan output)
├── research.md          # Phase 0 — decisions, rationale, alternatives, initial threshold values
├── data-model.md        # Phase 1 — entities, fields, relationships, state transitions
├── quickstart.md        # Phase 1 — local bring-up + first signal walkthrough
├── contracts/           # Phase 1 — interface contracts
│   ├── rest-api.openapi.yaml   # FastAPI /api/v1 surface
│   ├── ai-skills.md            # Structured I/O contracts for the 7 Claude Code skills
│   └── telegram-alerts.md      # Alert types + payload shapes + inline confirmation
├── spec.md
├── checklists/requirements.md
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created here)
```

### Source Code (repository root)

```text
backend/
├── src/aegis/
│   ├── domain/          # entities, value objects, Pydantic schemas (the contract types)
│   ├── ingestion/       # OHLCV workers (ccxt async, failover) + ContextProvider adapters
│   ├── indicators/      # TA-Lib + pandas-ta-classic; regime classifier (ADX/ATR); idempotent
│   ├── candidates/      # deterministic pre-gates (G1–G5) + confluence engine + sizing inputs
│   ├── ai/              # skill orchestration client + post-AI numeric reconciliation
│   ├── validation/      # backtest-runner (vectorbt), outcome labeler, signal-evaluator, promotion
│   ├── api/             # FastAPI app: routers, auth (API key + JWT scopes), deps, rate limiting
│   ├── telegram/        # aiogram v3 bot: outbound alerts + inbound confirmation/commands
│   ├── scheduler/       # APScheduler jobs (ingest/indicators per 15m/1h; context refresh; AI run)
│   ├── persistence/     # TimescaleDB models, repositories, migrations, continuous aggregates
│   └── config/          # settings, env loading, secrets, provider registry
└── tests/
    ├── contract/        # API schema + skill-I/O + Telegram payload contract tests
    ├── integration/     # ingest→compute→gate→AI→persist→alert flows against real fixtures
    └── unit/            # indicators, gates, sizing, reconciliation, regime — deterministic

frontend/
├── src/
│   ├── app/             # Next.js app router views: watchlist, asset detail, signals, context,
│   │                    #   performance, backtests
│   ├── components/      # lightweight-charts wrappers, tables, KPI cards, disclaimer banner
│   └── lib/             # typed API client (consumes /api/v1 with JWT)
└── tests/

skills/                  # Claude Code skills (project deliverables, each with SKILL.md + schema)
├── market-context/
├── signal-analyst/
├── risk-guardian/
├── exit-manager/
├── alert-composer/
├── backtest-runner/
└── signal-evaluator/

docker-compose.yml       # timescaledb + backend + scheduler + dashboard + reverse proxy (TLS)
```

**Structure Decision**: Web application layout (backend + frontend) plus a top-level `skills/`
directory for the Claude Code skills, which are first-class project deliverables (§9 of the brief).
The backend is a single async Python service organized by bounded module (ingestion / indicators /
candidates / ai / validation / api / telegram / scheduler / persistence) to keep the **deterministic
core (indicators + candidates) physically separated from the AI layer** (C-2). The AI reaches data
**only through the FastAPI internal API**, never the DB directly (least privilege, C-6).

## Complexity Tracking

> No Constitution Check violations — no entries required.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
