# Tasks: AEGIS MVP — Advisory Short-Swing Crypto Signals

**Input**: Design documents from `/specs/001-aegis-mvp/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: INCLUDED and mandatory — the constitution (C-8) and CLAUDE.md §2 require strict TDD.
Every test task is written FIRST and MUST FAIL before its implementation task begins.

**Organization**: Tasks are grouped by user story (priority order P1 → P2 → P2 → P3 → P3 → P3) so
each story is an independently testable increment.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: US1…US6 (story-phase tasks only); Setup/Foundational/Polish carry no story label
- Exact file paths are included in every task

## Path Conventions

Web app per plan.md: backend Python at `backend/src/aegis/`, tests at `backend/tests/`, dashboard at
`frontend/src/`, Claude Code skills at `skills/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and tooling.

- [X] T001 Create monorepo structure (`backend/`, `frontend/`, `skills/`, `docker-compose.yml`, `.env.example`) per plan.md
- [X] T002 Initialize backend Python 3.12 project with PINNED deps in `backend/pyproject.toml` (ccxt, TA-Lib, **pandas-ta-classic** — never `pandas-ta`, fastapi, pydantic v2, apscheduler[sqlalchemy], aiogram v3, vectorbt, backtesting.py, httpx, slowapi, asyncpg, alembic, pytest, pytest-asyncio)
- [ ] T003 [P] Initialize frontend Next.js + TypeScript + lightweight-charts in `frontend/`
- [X] T004 [P] Configure backend lint/format/type tools (ruff, black, mypy) in `backend/pyproject.toml`
- [ ] T005 [P] Configure frontend lint/format (eslint, prettier) in `frontend/`
- [X] T006 [P] Configure CI with coverage gate ≥ 80%, `pip-audit` dependency scan, and secret scan in `.github/workflows/ci.yml`
- [X] T007 Author `docker-compose.yml` (timescaledb, backend, scheduler, dashboard, Caddy reverse proxy, **`cloudflared` Tunnel in private-network mode — no public hostname**) bound to loopback/Docker network in repo root (remote access via Cloudflare WARP only, AC-07)
- [X] T008 [P] Create `.env.example` with all MVP keys and verify `.env` is gitignored

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure shared by ALL stories (determinism boundary, persistence, ingestion,
indicators, API skeleton). **⚠️ No user story can begin until this phase is complete.**

- [X] T009 [P] Define domain Pydantic v2 schemas for all entities in `backend/src/aegis/domain/` (candle, indicators, derivatives, context, macro_event, signal_candidate, signal, order_ticket, ai_audit, alert, outcome, position, strategy, backtest)
- [X] T010 Implement settings + secret loading in `backend/src/aegis/config/settings.py` (data-provider registry lands with ingestion)
- [ ] T011 [P] Implement structured logging (no secret/body leakage) + error-handling middleware in `backend/src/aegis/config/logging.py`
- [~] T012 Schema bootstrap with tables + hypertables (ohlc, indicators, derivatives) in `backend/src/aegis/persistence/schema.py` — DONE via SQLAlchemy + create_hypertable; PENDING: wrap as an Alembic migration + continuous aggregates 1h→4h→1d
- [X] T013 Implement persistence base (async engine/session, repository pattern) in `backend/src/aegis/persistence/base.py`
- [X] T014 Build pytest harness + real, traceable OHLCV fixtures in `backend/tests/conftest.py` and `backend/tests/fixtures/`
- [X] T015 [P] Write FAILING unit tests for indicators (EMA/RSI/MACD/BB/ATR/ADX/vol_rel/regime) against real fixtures in `backend/tests/unit/test_indicators.py`
- [X] T016 Implement indicators engine (TA-Lib + pandas-ta-classic) + regime classifier, idempotent, persist ≤ 5 s after candle close in `backend/src/aegis/indicators/` (AC-01)
- [ ] T017 Write FAILING integration test for ccxt OHLCV ingestion + failover in `backend/tests/integration/test_ingestion.py`
- [ ] T018 Implement OHLCV ingestion workers (ccxt async, rate-limit, backoff, failover Binance→MEXC→Coinbase→BitMart) in `backend/src/aegis/ingestion/ohlcv.py`
- [ ] T019 Implement `ContextProvider` interface + merge/dedup base in `backend/src/aegis/ingestion/context.py`
- [ ] T020 Implement APScheduler (AsyncIOScheduler + Postgres jobstore); schedule ingest/indicators on 15m/1h close in `backend/src/aegis/scheduler/`
- [ ] T021 Implement FastAPI app skeleton with private binding + reverse-proxy TLS wiring in `backend/src/aegis/api/app.py`
- [ ] T022 Write FAILING contract tests for auth (API key + JWT scopes) + rate limiting in `backend/tests/contract/test_auth.py`
- [ ] T023 Implement auth (X-API-Key + JWT read/admin scopes), slowapi rate limiting, CORS restricted to dashboard in `backend/src/aegis/api/auth.py`

**Checkpoint**: Deterministic core + persistence + ingestion + API skeleton ready.

---

## Phase 3: User Story 1 - Receive a vetted, executable signal (Priority: P1) 🎯 MVP

**Goal**: Ingest → compute → confluence candidate → AI decides → Telegram `SIGNAL` with a complete,
reconciled order ticket. No order is placed.

**Independent Test**: Feed a valid LONG setup → exactly one Telegram signal with a full order ticket;
every figure matches the persisted candidate; no order placed anywhere.

### Tests for User Story 1 (write first — must fail)

- [ ] T024 [P] [US1] Contract tests for GET `/signals`, `/signals/{id}`, `/signals/{id}/order` vs OpenAPI in `backend/tests/contract/test_signals_api.py`
- [ ] T025 [P] [US1] Contract tests for `market-context` + `signal-analyst` skill I/O schemas in `backend/tests/contract/test_skills_us1.py`
- [X] T026 [P] [US1] Unit test confluence engine + R:R < 1:2 discard without AI in `backend/tests/unit/test_confluence.py` (AC-03)
- [X] T027 [P] [US1] Unit test post-AI numeric reconciliation + fail-safe in `backend/tests/unit/test_reconciliation.py` (AC-04, AC-05)
- [ ] T028 [P] [US1] Integration test end-to-end happy path (valid setup → one SIGNAL, figures match, no order placed) in `backend/tests/integration/test_us1_signal.py`

### Implementation for User Story 1

- [X] T029 [P] [US1] Implement confluence engine (trend/momentum/MACD/volume/structure/volatility, R:R ≥ 1:2) → `signal_candidates` in `backend/src/aegis/candidates/confluence.py` (AC-03, FR-006/007)
- [X] T030 [P] [US1] Implement order-ticket builder + dual-constraint sizing (entry/stop/target/notional/structure, Binance default, TP_SL degrade) in `backend/src/aegis/candidates/order_ticket.py` (AC-09, AC-11, FR-014)
- [X] T031 [US1] Implement signals/candidates/order_tickets/ai_audit repositories in `backend/src/aegis/persistence/repositories/signals.py`
- [X] T032 [P] [US1] Author `market-context` skill (Haiku 4.5) SKILL.md + output schema in `skills/market-context/`
- [X] T033 [P] [US1] Author `signal-analyst` skill (Opus 4.8) SKILL.md + output schema in `skills/signal-analyst/`
- [X] T034 [US1] Implement AI orchestration client (invoke skills, schema-validated structured output — `temperature` is removed on Opus 4.8) in `backend/src/aegis/ai/orchestrator.py` (FR-009/013)
- [X] T035 [US1] Implement post-AI numeric reconciliation + incident recording in `backend/src/aegis/ai/reconciliation.py` (AC-04, C-2)
- [X] T036 [US1] Implement fail-safe guard (AI unavailable/invalid/missing figure → no signal) in `backend/src/aegis/ai/failsafe.py` (AC-05, FR-012)
- [X] T037 [P] [US1] Author `alert-composer` skill SKILL.md (English, disclaimer, copy-paste ticket) in `skills/alert-composer/`
- [ ] T038 [US1] Implement Telegram outbound `SIGNAL` alert (aiogram v3) with order ticket + disclaimer in `backend/src/aegis/telegram/outbound/signal.py` (+ shared `outbound/base.py`) (FR-019/026, C-10)
- [ ] T039 [US1] Implement POST `/internal/signals` (loopback) + GET `/signals`, `/signals/{id}`, `/signals/{id}/order`, `/candles`, `/indicators` in `backend/src/aegis/api/routers/signals.py`
- [ ] T040 [US1] Wire scheduler job: candidate(s) → AI pipeline → reconcile → persist → alert (< 30 s, SC-005) in `backend/src/aegis/scheduler/jobs/signal_run.py`

**Checkpoint**: 🎯 MVP — US1 fully functional and independently testable.

---

## Phase 4: User Story 2 - Safety gates prevent unsafe signals (Priority: P2)

**Goal**: Deterministic pre-gates (regime, BTC master, liquidity, derivatives, systemic) + macro
pre-event filter + risk-guardian suppress unsafe signals, favoring 0 signals over a bad one.

**Independent Test**: Drive each adverse condition in isolation → the corresponding LONG is
suppressed/gated or a global pause is raised, without invoking the AI when a deterministic gate fails.

### Tests for User Story 2 (write first — must fail)

- [ ] T041 [P] [US2] Unit tests for pre-gates G1–G5 in isolation (regime; BTC 1d close < EMA200; liquidity; derivatives; systemic/depeg) in `backend/tests/unit/test_gates.py` (AC-02/14/15/17)
- [ ] T042 [P] [US2] Unit test macro pre-event blackout/caution window (12h before / 2h after) in `backend/tests/unit/test_macro_filter.py` (AC-12)
- [ ] T043 [P] [US2] Unit test risk-guardian sizing / 6% aggregate cap / correlation / free-capital veto in `backend/tests/unit/test_risk_guardian.py` (AC-10)
- [ ] T044 [P] [US2] Integration test: each adverse condition suppresses LONG / raises pause, AI not invoked on deterministic gate fail in `backend/tests/integration/test_us2_gates.py`

### Implementation for User Story 2

- [ ] T045 [P] [US2] Implement derivatives ingestion (Binance futures funding/OI/long-short + Coinglass liquidations) in `backend/src/aegis/ingestion/derivatives.py` (FR-002)
- [ ] T046 [P] [US2] Implement context providers (sentiment Fear&Greed/Reddit/Santiment; news/geo GDELT/RSS; security PeckShield/De.Fi; systemic/depeg) in `backend/src/aegis/ingestion/providers/`
- [ ] T047 [P] [US2] Implement macro calendar provider (FMP/FRED/FOMC) + `macro_events` persistence in `backend/src/aegis/ingestion/providers/macro.py`
- [ ] T048 [US2] Implement deterministic pre-gates G1–G5 (run BEFORE confluence; no LLM on fail) in `backend/src/aegis/candidates/gates.py` (AC-02/14/15/17, FR-005)
- [ ] T049 [US2] Implement macro pre-event filter (blackout/caution, market-wide) in `backend/src/aegis/candidates/macro_filter.py` (AC-12, FR-008)
- [ ] T050 [P] [US2] Author `risk-guardian` skill (Opus 4.8) SKILL.md + schema in `skills/risk-guardian/`
- [ ] T051 [US2] Implement risk-guardian sizing/exposure/correlation/free-capital veto in `backend/src/aegis/candidates/risk_guardian.py` (AC-10, FR-015)
- [ ] T052 [US2] Implement `SECURITY_ALERT` / `MACRO_EVENT` / `SYSTEMIC_ALERT` + global pause in `backend/src/aegis/telegram/outbound/context_alerts.py` (AC-13/17, C-14)
- [ ] T053 [US2] Integrate gates + macro + risk-guardian into the candidate→signal pipeline (gates precede confluence/AI) in `backend/src/aegis/scheduler/jobs/signal_run.py`

**Checkpoint**: US1 + US2 work; signals are gated by the full safety stack.

---

## Phase 5: User Story 5 - Validation gate before going live (Priority: P2)

**Goal**: No strategy alerts live until it passes automated backtest (fees/slippage/walk-forward),
shadow/forward test, deterministic outcome labeling, confidence calibration, and **alpha-vs-HODL > 0**.

**Independent Test**: A sub-KPI strategy stays in shadow (no Telegram); a strategy that fails to beat
HODL is not promoted.

### Tests for User Story 5 (write first — must fail)

- [ ] T054 [P] [US5] Contract tests for POST/GET `/backtests` + GET `/performance` in `backend/tests/contract/test_backtests_api.py`
- [ ] T055 [P] [US5] Unit test deterministic outcome labeler HIT/STOP/EXPIRED in `backend/tests/unit/test_outcome_labeler.py` (AC-08)
- [ ] T056 [P] [US5] Unit test alpha-vs-HODL benchmark + promotion gate keeps sub-KPI strategy in shadow in `backend/tests/unit/test_promotion.py` (AC-06, AC-16)
- [ ] T057 [P] [US5] Integration test: sub-KPI stays shadow (no Telegram); fails-HODL not promoted in `backend/tests/integration/test_us5_validation.py`

### Implementation for User Story 5

- [ ] T058 [P] [US5] Implement deterministic outcome labeler (HIT/STOP/EXPIRED, realized_pct) in `backend/src/aegis/validation/outcome_labeler.py` (AC-08, FR-018)
- [ ] T059 [P] [US5] Author `backtest-runner` skill (vectorbt, fees/slippage, walk-forward) SKILL.md in `skills/backtest-runner/`
- [ ] T060 [US5] Implement backtest-runner integration (vectorbt) + `backtests` persistence in `backend/src/aegis/validation/backtest_runner.py` (FR-024)
- [ ] T061 [P] [US5] Implement risk-adjusted alpha-vs-HODL benchmark in `backend/src/aegis/validation/hodl_benchmark.py` (AC-16, C-13)
- [ ] T062 [P] [US5] Author `signal-evaluator` skill (LLM-as-judge, calibration) SKILL.md in `skills/signal-evaluator/`
- [ ] T063 [US5] Implement promotion gate + circuit breaker (shadow↔production by KPIs incl. alpha) + `strategies` persistence in `backend/src/aegis/validation/promotion.py` (AC-06, FR-025, C-5)
- [ ] T064 [US5] Implement POST/GET `/backtests` + GET `/performance` (admin scope) in `backend/src/aegis/api/routers/validation.py`
- [ ] T065 [US5] Wire validation pipeline + shadow-mode gating of Telegram alerts in `backend/src/aegis/scheduler/jobs/validation_run.py`

**Checkpoint**: No strategy can alert live without passing the gate.

---

## Phase 6: User Story 3 - Dynamic exit management after entry (Priority: P3)

**Goal**: After entry, advise partial take-profit, move-to-breakeven, trailing, and early exit on
invalidation. Never executes.

**Independent Test**: Price reaches TP1 → `TRADE_MANAGEMENT` advisory (partial + stop→BE); target hit
→ outcome labeled + `TARGET_HIT`.

### Tests for User Story 3 (write first — must fail)

- [ ] T066 [P] [US3] Unit test exit-manager TP1 partial + move-to-BE + trailing + early exit in `backend/tests/unit/test_exit_manager.py` (AC-18)
- [ ] T067 [P] [US3] Integration test: TP1 → TRADE_MANAGEMENT; target → TARGET_HIT in `backend/tests/integration/test_us3_exits.py` (AC-08, AC-18)

### Implementation for User Story 3

- [ ] T068 [P] [US3] Author `exit-manager` skill SKILL.md + schema in `skills/exit-manager/`
- [ ] T069 [US3] Implement exit-manager logic (scale-out/BE/trailing/early-exit, default plan TP1 +3% close 50% → BE → trail ≥ +5%) in `backend/src/aegis/candidates/exit_manager.py` (AC-18, FR-016)
- [ ] T070 [US3] Implement `TRADE_MANAGEMENT` + `TARGET_HIT`/`STOP_HIT`/`INVALIDATED` alerts in `backend/src/aegis/telegram/outbound/management.py` (AC-08, AC-18)
- [ ] T071 [US3] Wire per-candle position-watch job (uses outcome labeler from US5) in `backend/src/aegis/scheduler/jobs/position_watch.py`

**Checkpoint**: Open positions are actively managed via advisories.

---

## Phase 7: User Story 4 - Confirm a taken trade and track real P&L (Priority: P3)

**Goal**: Operator confirms a taken signal from the alert; system records the real position and
computes real (not just theoretical) P&L.

**Independent Test**: Reply to a `SIGNAL` with inline "Taken" → a real position is recorded and its
P&L is attributed to the confirmed (real) trade.

### Tests for User Story 4 (write first — must fail)

- [ ] T072 [P] [US4] Integration test inline "Taken" confirmation records a real position + real P&L in `backend/tests/integration/test_us4_confirm.py` (AC-19)

### Implementation for User Story 4

- [ ] T073 [US4] Implement aiogram inbound callbacks (✅ Taken / ❌ Ignored) + commands (`/status`,`/signals`,`/positions`,`/pnl`,`/mute`,`/pause`) in `backend/src/aegis/telegram/inbound.py` (FR-021)
- [ ] T074 [US4] Implement `positions` persistence + real vs theoretical P&L computation in `backend/src/aegis/persistence/repositories/positions.py` (AC-19, C-16)
- [ ] T075 [P] [US4] Implement CryptoLedger portfolio-source integration stub in `backend/src/aegis/ingestion/providers/cryptoledger.py`

**Checkpoint**: Real P&L tracked distinctly from theoretical.

---

## Phase 8: User Story 6 - Monitor signals, context and performance (Priority: P3)

**Goal**: A private read-only dashboard + API for candles/indicators, signals with thesis/outcome,
context, performance KPIs, and the AI decision audit trail — private network only.

**Independent Test**: From inside the VPN, dashboard + API show data read-only; from the public
internet they are unreachable.

### Tests for User Story 6 (write first — must fail)

- [ ] T076 [P] [US6] Contract test remaining read endpoints (`/symbols`, `/context`, `/audit`, `/performance`) in `backend/tests/contract/test_read_api.py`
- [ ] T077 [P] [US6] Integration test private-only access (intranet reachable, WAN unreachable) in `backend/tests/integration/test_us6_private.py` (AC-07)

### Implementation for User Story 6

- [ ] T078 [US6] Implement GET `/symbols`, `/context/{symbol}`, `/audit/{signal_id}` in `backend/src/aegis/api/routers/read.py`
- [ ] T079 [P] [US6] Build dashboard views (watchlist, asset detail w/ lightweight-charts, signals, context, performance, backtests) read-only + disclaimer in `frontend/src/app/`
- [ ] T080 [P] [US6] Build typed API client (JWT) in `frontend/src/lib/api.ts`
- [ ] T081 [US6] Verify no order-placing controls + disclaimer present in dashboard in `frontend/tests/` (FR-022, C-10)

**Checkpoint**: All six stories independently functional.

---

## Phase 9: Polish & Cross-Cutting Concerns

- [ ] T082 [P] Implement dedup + per-symbol cooldown + optional digest in `backend/src/aegis/telegram/dedup.py` (FR-020)
- [ ] T083 [P] Implement equity-curve throttle (reduce size / pause on degradation) in `backend/src/aegis/candidates/throttle.py` (FR-017)
- [ ] T084 [P] Contract test asserting "not financial advice" disclaimer across all alerts + dashboard in `backend/tests/contract/test_disclaimer.py` (FR-026, C-10)
- [ ] T085 [P] Security hardening (read-only FS, minimal images, pinned+audited deps, vuln scan in CI) per `docker-compose.yml` and CI (C-6)
- [ ] T086 [P] Add unit tests to reach coverage gate ≥ 80% (financial-critical logic higher) in `backend/tests/unit/`
- [ ] T087 [P] Documentation (README, operator runbook) in `docs/`
- [ ] T088 Run `quickstart.md` end-to-end validation (smoke + first-signal + safety checks)
- [ ] T089 Static + test sweep confirming ZERO order-execution paths exist anywhere (SC-011, C-1)
- [ ] T090 [P] Implement ingestion resilience (per-venue reconnect/backoff + heartbeat) and an uptime monitor for the capture pipeline in `backend/src/aegis/ingestion/health.py` (SC-007)
- [ ] T091 [P] Implement security-alert false-positive measurement/calibration (track FP rate, target < 5%) in `backend/src/aegis/validation/security_fp.py` (SC-008)
- [ ] T092 [P] Implement monthly AI-token + data-cost monitor with the < €50/month ceiling alarm in `backend/src/aegis/ai/cost_monitor.py` (SC-009, C-7)

---

## Dependencies & Execution Order

### Phase Dependencies
- **Setup (P1)** → no deps.
- **Foundational (P2)** → after Setup; **blocks all stories**.
- **US1 (P1)** → after Foundational. The MVP.
- **US2 (P2)** → after Foundational; integrates into US1's pipeline (gates precede confluence).
- **US5 (P2)** → after Foundational; gates Telegram alerting (shadow mode) for all stories.
- **US3 (P3)** → after Foundational; reuses US5's outcome labeler (T058) for `TARGET_HIT`.
- **US4 (P3)** → after Foundational; consumes US1's `SIGNAL` alerts for the confirmation loop.
- **US6 (P3)** → after Foundational; reads everything produced by US1/US2/US5.
- **Polish (P9)** → after the targeted stories are complete.

### Within Each Story (TDD)
Tests written and FAILING → models/schemas → services/logic → endpoints/skills → integration/wiring.

### Cross-story note (kept minimal)
US3→US5 (outcome labeler) and US4→US1 (signal alerts) are forward dependencies satisfied by phase
order. Each story remains independently testable with fixtures if implemented out of order.

### Parallel Opportunities
- Setup: T003, T004, T005, T006, T008 in parallel.
- Foundational: T009/T011 in parallel; T015 (test) parallel to other test authoring.
- Per story: all `[P]` test tasks run together first; then `[P]` skills/models/providers in parallel.
- With capacity, US2 and US5 (both P2) can progress in parallel after Foundational.

---

## Parallel Example: User Story 1

```bash
# 1) Author all failing tests together:
Task: T024 Contract tests for /signals endpoints
Task: T025 Contract tests for market-context + signal-analyst schemas
Task: T026 Unit test confluence + R:R discard
Task: T027 Unit test reconciliation + fail-safe
Task: T028 Integration test end-to-end happy path

# 2) Then parallel implementation of independent pieces:
Task: T029 Confluence engine
Task: T030 Order-ticket builder + sizing
Task: T032 market-context skill
Task: T033 signal-analyst skill
Task: T037 alert-composer skill
```

---

## Implementation Strategy

### MVP First (US1 only)
Setup → Foundational → US1 → **STOP & VALIDATE** the independent test → demo. At this point AEGIS
already emits vetted, reconciled, advisory signals over Telegram (no orders placed).

### Incremental Delivery
US1 (MVP) → US2 (safety gates) → US5 (validation gate, before any live alerting) → US3 (exits) →
US4 (real P&L) → US6 (dashboard). Each adds value without breaking earlier stories.

---

## Acceptance Criteria → Task coverage (for /speckit.analyze)

| AC | Tasks |
|----|-------|
| AC-01 | T015, T016, T020 |
| AC-02 | T041, T048, T052 |
| AC-03 | T026, T029 |
| AC-04 | T027, T035 |
| AC-05 | T027, T036 |
| AC-06 | T056, T063, T065 |
| AC-07 | T077, T021, T023 |
| AC-08 | T055, T058, T067, T070 |
| AC-09 | T030, T038, T039 |
| AC-10 | T043, T051 |
| AC-11 | T030 |
| AC-12 | T042, T049 |
| AC-13 | T052 |
| AC-14 | T041, T048 |
| AC-15 | T041, T048 |
| AC-16 | T056, T061, T063 |
| AC-17 | T041, T048, T052 |
| AC-18 | T066, T069, T070 |
| AC-19 | T072, T073, T074 |

---

## Notes
- `[P]` = different files, no incomplete-task dependency.
- Every test task is RED before its implementation task (C-8); one commit per task (CLAUDE.md §2/§5).
- No task places, modifies, or cancels an exchange order — advisory only (C-1). T089 verifies this.
- The determinism boundary (Python numbers vs AI judgment) is enforced by T035 reconciliation.
- Total: 92 tasks — Setup 8, Foundational 15, US1 17, US2 13, US5 12, US3 6, US4 4, US6 6, Polish 11.
- Telegram outbound is modularized under `telegram/outbound/` (signal / context_alerts / management)
  so US1/US2/US3 do not contend on a single file.
- SC coverage closed by Polish: SC-007→T090, SC-008→T091, SC-009→T092.
