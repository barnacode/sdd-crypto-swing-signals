# AEGIS — Roadmap

High-level phases and milestones. This is the **executive view**; the granular, per-task source of
truth is [`specs/001-aegis-mvp/tasks.md`](./specs/001-aegis-mvp/tasks.md) (check it for exact task
status). This file is intentionally coarse to avoid drifting from `tasks.md`.

**Legend:** ✅ done · 🔄 in progress · ⏳ planned · ⛔ blocked / needs amendment

_Last updated: 2026-06-14_

---

## Phase 0 — Spec-Driven Development ✅
Constitution → specify → clarify → plan → tasks → analyze → checklist. Complete and committed.
`taskstoissues` (GitHub epic + sub-issues) intentionally deferred.

## Phase 1 — MVP (advisory signal loop)

The MVP is delivered story by story, in priority order. Exit criterion for the MVP: **US1 + US2 +
US5** working end-to-end (a vetted signal, gated for safety, only alerting live after passing the
validation gate).

| Story | Goal | Status |
|---|---|---|
| Setup + Foundational | tooling, domain, persistence, indicators, ingestion, scheduler, API | 🔄 core done; ingestion/scheduler/logging pending |
| **US1 (P1) — vetted advisory signal** | ingest → compute → confluence → AI → reconcile → Telegram `SIGNAL` | 🔄 deterministic core + AI layer + persistence + read API done; **Telegram + scheduler wiring + e2e pending** |
| US2 (P2) — safety gates | deterministic pre-gates G1–G5 + macro filter + risk-guardian | ⏳ |
| US5 (P2) — validation gate | backtest, outcome labeling, alpha-vs-HODL, promotion/circuit-breaker | ⏳ |
| US3 (P3) — exit management | TP1/breakeven/trailing advisories | ⏳ |
| US4 (P3) — real P&L | inline take/ignore confirmation, real vs theoretical P&L | ⏳ |
| US6 (P3) — dashboard + API | Next.js read-only dashboard + remaining read endpoints | ⏳ |
| Polish | dedup/cooldown, equity throttle, disclaimer audit, hardening, coverage | ⏳ |

### Current snapshot (what runs and is verified)
- Domain schemas with the determinism guards (R:R ≥ 1:2, signal↔candidate reconciliation).
- Indicator engine (pandas-ta-classic) on **real** Binance fixtures.
- Confluence engine, order-ticket builder + dual-constraint sizing, AI fail-safe + reconciliation.
- AI orchestrator (Haiku-context / Opus-decision routing) + skill specs.
- Persistence over **TimescaleDB** (hypertables) + read API (FastAPI, API-key/JWT auth) — tested
  against a real database; `POST /internal/signals` rejects hallucinated figures with 409.

### Known partials / TODO within Phase 1
- Schema bootstrap works via SQLAlchemy; **Alembic migration + continuous aggregates** still TODO.
- API: `/candles`, `/indicators` and the admin/JWT endpoints pending (need ingestion data / US5/US6).
- Ingestion (ccxt OHLCV + context providers), APScheduler wiring, structured logging — pending.
- Telegram outbound (`SIGNAL` + confirmation loop) and the end-to-end US1 test — pending.

## Phase 2 — Hardening & validation
Forward-test in shadow mode, calibration, circuit breaker, TradingAgents external benchmark, CI
coverage/security gates, observability. No strategy alerts live until it passes the gate (C-5/C-13).

## Phase 3 — Post-MVP (roadmap, brief §17)
- Paid data upgrades **only once alpha is demonstrated** and within < €50/month (C-7): realtime
  social sentiment, paid on-chain (whales/flows), richer derivatives.
- Broader universe / additional venues; performance tuning.
- ⛔ **Real automated execution** — a future phase that **requires an explicit constitution
  amendment** of C-1 (ADR-011): trading keys without withdrawal, IP allowlist, secrets vault,
  mandatory paper mode, global kill-switch, per-exchange capability matrix. Not in scope until then.

---

## Open decisions (deferred, non-blocking)
Tracked in the spec's "Deferred to clarify"; revisited as stories land:
reference capital / risk %, exact TA thresholds (tuned by backtest), macro event classification,
shadow window, promotion KPIs, remaining gate thresholds, trailing % / TP2, real-P&L integration.

## How this file is maintained
Update the phase/story status here at each milestone; keep task-level detail in `tasks.md`. If the
two disagree, **`tasks.md` wins** for granular status and the constitution wins for principles.
