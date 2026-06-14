# Feature Specification: AEGIS MVP — Advisory Short-Swing Crypto Signals

**Feature Branch**: `001-aegis-mvp`  
**Created**: 2026-06-13  
**Status**: Draft  
**Input**: PROJECT-BRIEF.md v1.3 (2026-06-13). AEGIS — Algorithmic Edge & Guidance Intelligence System: a private, local, 24/7 system that watches the crypto market, computes deterministic technical analysis, lets an AI agent reason over it, and delivers solid short-swing signals over Telegram with an executable order ticket. **Advisory only in Phase 1 — it never places or cancels orders.**

## Overview

AEGIS serves a **single private operator**. It continuously captures market and context data, computes technical indicators and market regime deterministically, applies conservative confluence rules behind a set of safety gates, and asks an AI agent to reason over the resulting candidates to decide whether to emit a signal. Every emitted signal arrives over Telegram with a complete, copy-paste-ready **order ticket** (entry, take-profit, stop-loss, OCO/trailing, size). The operator places the order manually; the system observes the position and advises on exits. No strategy is allowed to alert live until it passes an automated validation gate that includes beating buy-and-hold.

The non-negotiable boundaries that shape this specification come from the project constitution (C-1…C-16): advisory-only in Phase 1, determinism first (the AI never invents numbers), auditable & reproducible decisions, fail-safe silence over a bad signal, validation before production, privacy, cost control, soundness over frequency, bounded sizing, must beat HODL, systemic safeguards, and honest P&L.

## Clarifications

### Session 2026-06-13

- Q: Default venue for the order ticket and basis for the symbol→venue mapping? → A: **Binance spot** as the default venue (native OCO, deepest top-20 liquidity), with a per-symbol mapping and failover; venues lacking native OCO degrade to a TP+SL pair per AC-11.
- Q: Deterministic definition of "BTC bearish" for the master gate that blocks LONGs on alts? → A: **BTC daily close below its EMA200** (1d). While true, no LONG signals are emitted on altcoins (AC-14 / C-15).
- Q: AI model routing and monthly token-cost ceiling? → A: **Haiku 4.5 for cached market-context synthesis + Opus 4.8 for the final decision over already-filtered candidates**, capped at ≈ €15/month (within the < €50/month production ceiling, C-7).
- Q: Default exit plan (TP / breakeven / trailing) advised by exit-management? → A: **TP1 at +3% closes 50% and moves the stop to breakeven; the remainder trails toward ≥ +5%** (satisfies AC-18; the runner can reach/exceed the +5% target, AC-08).
- Q: Default symbol universe watched by the MVP? → A: **BTC, ETH + the ~top-20 by liquidity, configurable watchlist, excluding memecoins and stablecoins.**

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Receive a vetted, executable short-swing signal (Priority: P1)

The operator wants to be told, 24/7 and without manual chart-watching, when a high-conviction short-swing opportunity (target ≥ +5%, risk:reward ≥ 1:2) appears — and to receive it as a ready-to-place order, not as raw analysis.

**Why this priority**: This is the core product value. With only this story implemented (ingest → compute → reason → alert), the operator already receives actionable, vetted signals — a viable MVP. Everything else hardens, validates, or visualizes this loop.

**Independent Test**: Feed market data that forms a valid LONG setup on the base timeframe for a watched symbol. Verify exactly one Telegram signal is delivered containing a complete order ticket (entry, TP, SL, order structure, size, target venue, thesis, confidence, invalidation), that every number in the alert matches the persisted candidate, and that no order is placed anywhere.

**Acceptance Scenarios** *(EARS)*:

1. **AC-01** — *When* a base-timeframe (1h) candle closes for a watchlist symbol, *the system shall* recompute its indicators and persist them within ≤ 5 seconds.
2. **AC-03** — *When* a candidate does not reach risk:reward ≥ 1:2, *the system shall* discard it without invoking the AI agent.
3. **AC-04** — *When* the agent emits a signal, *the system shall* verify that every figure (including the order ticket) matches the persisted candidate/indicator values; if any differs, *the system shall* discard the signal and record the incident.
4. **AC-05** — *Where* the AI agent or its output fails to validate, *the system shall* emit no alert (fail-safe).
5. **AC-09** — *When* a signal is emitted, *the system shall* attach an executable order ticket (entry, TP, SL, OCO/trailing structure supported by the target venue, size) without placing any order.
6. **AC-11** — *When* the target venue does not support native OCO, *the system shall* express the ticket as a TP+SL pair (two orders) with an explanatory note.

---

### User Story 2 - Safety gates prevent unsafe signals (Priority: P2)

The operator wants strong, automatic guardrails so that signals are suppressed whenever market structure, positioning, liquidity, scheduled macro events, available capital, or systemic conditions make a trade unsafe — favoring zero signals over a bad one.

**Why this priority**: "Maximum guarantees" is a stated product pillar. These gates are what turn a naive signal generator into a conservative advisor. They are independently valuable and testable, but only meaningful once US1 exists.

**Independent Test**: Drive each adverse condition in isolation (BTC bearish, stablecoin depeg, macro blackout window, insufficient free capital, illiquid pair, active security alert, saturated derivatives) and confirm the corresponding LONG signal is suppressed, gated, or a global pause is raised — without the AI being invoked when a deterministic gate already fails.

**Acceptance Scenarios** *(EARS)*:

1. **AC-02** — *While* an active security alert affects an asset, *the system shall* prevent emission of LONG signals for that asset.
2. **AC-10** — *When* a candidate's required notional exceeds available capital or the 6% aggregate risk cap, *the system shall* not emit the signal.
3. **AC-12** — *While* the window (12h before / 2h after) of a maximum-impact macro event is active, *the system shall* not emit new LONG signals (blackout).
4. **AC-13** — *When* a maximum-impact macro event is ≤ 12h away, *the system shall* send a `MACRO_EVENT` alert indicating which open positions are affected.
5. **AC-14** — *While* BTC is in a bearish regime, *the system shall* not emit LONG signals on altcoins (BTC gate).
6. **AC-15** — *When* the candidate pair lacks sufficient liquidity/depth for the notional, *the system shall* discard it before invoking the AI agent.
7. **AC-17** — *When* a stablecoin depeg or serious exchange/chain incident is detected, *the system shall* activate a global pause and send a `SYSTEMIC_ALERT`.

---

### User Story 3 - Dynamic exit management after entry (Priority: P3)

After the operator takes a signal, the system continues to watch the position and advises on locking in gains (partial take-profit, moving the stop to breakeven, trailing the remainder) or exiting early when the thesis is invalidated. It never executes — it advises.

**Why this priority**: Capturing and protecting profit materially improves realized outcomes, but it depends on a signal having been issued (US1) and ideally confirmed (US4). It is a distinct, independently testable journey.

**Independent Test**: Simulate price reaching the first take-profit level on an open position and confirm a `TRADE_MANAGEMENT` advisory is sent recommending a partial close and a move of the stop to breakeven; simulate the target being hit and confirm the outcome is labeled and `TARGET_HIT` is sent.

**Acceptance Scenarios** *(EARS)*:

1. **AC-08** — *When* a signal reaches +5% before its stop, *the system shall* label its outcome `HIT` and notify `TARGET_HIT`.
2. **AC-18** — *When* a position reaches TP1, *the system shall* send a `TRADE_MANAGEMENT` advisory recommending a partial take and moving the stop to breakeven.

---

### User Story 4 - Confirm a taken trade and track real P&L (Priority: P3)

The operator wants to tell the system, directly from the alert, whether they actually took a signal, so the system can record the real position and compute real (not just theoretical) profit and loss.

**Why this priority**: Honest, real P&L (C-16) feeds the equity-curve throttle and production metrics, and connects to the operator's portfolio. Valuable but secondary to having signals and gates.

**Independent Test**: Respond to a `SIGNAL` alert with the inline "taken" action and confirm a real position is recorded and its P&L is computed and attributed to the confirmed (real) trade rather than the theoretical one.

**Acceptance Scenarios** *(EARS)*:

1. **AC-19** — *When* the operator confirms a signal as "taken", *the system shall* record the position and compute its real P&L.

---

### User Story 5 - Validation gate before going live (Priority: P2)

Before any strategy is allowed to send live Telegram alerts, the operator wants it to prove itself automatically — through backtesting (with fees/slippage), forward/shadow testing, outcome labeling, confidence calibration, and beating buy-and-hold — with the operator only reading the verdict.

**Why this priority**: This is a hard constitutional gate (C-5, C-13): no strategy alerts live without passing it. It protects the operator from acting on unproven strategies, which is as important as the signal loop itself, hence P2.

**Independent Test**: Run a strategy whose forward-test metrics fall short of the KPIs and confirm it remains in shadow mode (no Telegram alerts); run one that fails to beat buy-and-hold and confirm it is not promoted.

**Acceptance Scenarios** *(EARS)*:

1. **AC-06** — *When* a strategy does not meet the validation KPIs, *the system shall* keep it in shadow mode (no Telegram alerts).
2. **AC-16** — *When* a strategy does not beat risk-adjusted buy-and-hold of BTC/ETH in forward-test, *the system shall* not promote it to production.

---

### User Story 6 - Monitor signals, context and performance (Priority: P3)

The operator wants a private dashboard and an API to review candles with indicators, market regime and context, active and historical signals with their thesis and outcome, performance KPIs (including alpha vs HODL), and the full audit trail of any AI decision — all accessible only from the private network.

**Why this priority**: Visibility and auditability matter for trust and tuning, but the signals themselves (delivered via Telegram) are usable without the dashboard, so this is P3.

**Independent Test**: From inside the private network/VPN, open the dashboard and the API and confirm candles+indicators, the signal list with thesis/outcome, performance KPIs, and the decision audit trail are visible read-only; from the public internet, confirm the API/dashboard is unreachable.

**Acceptance Scenarios** *(EARS)*:

1. **AC-07** — *While* the system runs, *the system shall* expose the API only on the local network/VPN, never on the public internet.

---

### Edge Cases

- **No valid setup**: On a quiet day with no setup passing confluence, the system emits **0 signals** (soundness over frequency — never relax gates to hit a cadence).
- **Multiple simultaneous solid setups**: All solid signals are emitted (no daily cap), de-duplicated and cooldown-limited per symbol; optionally grouped into a digest if many arrive in a short window.
- **Correlated candidates**: When several candidates are highly correlated with each other or with open positions, exposure is limited so they are not treated as independent bets.
- **AI unavailable or invalid output**: No signal is emitted (fail-safe); the incident is recorded.
- **Provider outage / tier change**: A market-data venue failover order exists; a missing or delayed macro-calendar source is treated conservatively (uncertainty ⇒ treat as blackout).
- **Data figure missing**: If the AI needs a number that is not present, it requests it from the system rather than inventing it; an unresolved missing figure suppresses the signal.
- **Equity-curve drawdown**: When recent signal performance deteriorates, position size is automatically reduced or signaling is paused (real-time meta-risk throttle).
- **Macro window overlap with open position**: A heads-up identifies which open positions are exposed to the imminent event so the operator can choose to protect them.
- **Venue capability mismatch**: When the chosen venue cannot express the requested order structure (e.g., native trailing), the ticket degrades gracefully with an explanatory note.
- **Theoretical vs real divergence**: Signals the operator did not confirm as taken are tracked as theoretical only; production metrics and the throttle use real P&L when it exists.

## Requirements *(mandatory)*

### Functional Requirements

**Capture & context**
- **FR-001**: System MUST continuously (24/7) capture price/volume history across multiple venues for the watched universe — **BTC, ETH plus the ~top-20 assets by liquidity, via a configurable watchlist that excludes memecoins and stablecoins** — on the base and confirmation timeframes plus higher timeframes for trend context, with automatic failover between venues.
- **FR-002**: System MUST capture context signals at no cost: community sentiment/regime, news, geopolitical/macro tone, a forward macro-economic calendar, derivatives/positioning data, market-wide BTC dominance, and security/exploit alerts.
- **FR-003**: System MUST treat slow/lagged sentiment sources as a regime filter, not as an intraday trigger; intraday triggers MUST rest on price/volume/structure plus near-real-time news/security signals.

**Deterministic computation & gates**
- **FR-004**: System MUST compute all indicators, levels, market regime, and risk:reward figures deterministically and persist them; these figures are the single source of truth for any downstream decision.
- **FR-005**: System MUST evaluate deterministic pre-gates BEFORE confluence and BEFORE any AI invocation: market regime, BTC master gate, liquidity/spread, derivatives sanity, and systemic safeguard. The **BTC master gate treats BTC as bearish when its daily (1d) close is below its EMA200**, and while bearish it blocks all altcoin LONG candidates. Failing any gate produces no candidate.
- **FR-006**: System MUST apply conservative multi-condition confluence rules to surface scored signal candidates, each carrying a complete order ticket and feature set.
- **FR-007**: System MUST enforce risk:reward ≥ 1:2 and a target of ≥ +5%, discarding non-compliant candidates without invoking the AI.
- **FR-008**: System MUST apply a deterministic pre-event macro filter with a 12h-before / 2h-after window: blackout for maximum-impact events; a caution flag (reinforced confluence, reduced size) for medium-impact events; applied market-wide.

**AI reasoning (advisory)**
- **FR-009**: System MUST use an AI agent to reason over filtered candidates plus synthesized context and decide to emit, discard, or watch — assigning a calibrated confidence (0–100), a thesis with bull/bear cases, and an explicit invalidation. The AI MUST NOT originate any numeric value.
- **FR-010**: System MUST validate, after AI output, that every figure in the signal matches the persisted candidate/indicators; on mismatch the signal is discarded and the incident recorded.
- **FR-011**: System MUST persist, for every signal, the inputs, summarized reasoning, model, and decision so each decision is auditable and reproducible.
- **FR-012**: System MUST, on any AI unavailability, invalid output, or unresolved missing input, emit no signal (fail-safe).
- **FR-013**: System MUST bound AI cost: **market-context synthesis runs on Haiku 4.5 (cached, refreshed periodically or on event, not on every candle); the final emit/discard/watch decision runs on Opus 4.8 over already-filtered candidates only**; the bull/bear debate is limited to a single round; total AI token spend MUST stay within ≈ €15/month (inside the < €50/month production ceiling, C-7).

**Order ticket, sizing & exit management**
- **FR-014**: System MUST attach to every signal an executable order ticket — entry, take-profit, stop, order structure (OCO / TP+SL / market+trailing) supported by the target venue, size, target venue, and validity — and MUST NOT place, modify, or cancel any order in Phase 1. The **default target venue is Binance spot** (native OCO), resolved per symbol via a configurable symbol→venue mapping with failover; on a venue without native OCO the ticket degrades to a TP+SL pair (AC-11).
- **FR-015**: System MUST size every signal by the dual-constraint model (configured notional vs a percentage-of-capital risk ceiling), respect the aggregate risk cap, the per-correlation cap, and available free capital; a signal with no free capital for its notional is not emitted.
- **FR-016**: System MUST, after entry, advise on dynamic exit management — via management advisories, without executing — following the **default exit plan: at TP1 (+3%) advise closing 50% and moving the stop to breakeven; trail the remainder toward the ≥ +5% target; exit early on invalidation**. The plan is configurable per strategy.
- **FR-017**: System MUST automatically reduce size or pause signaling when recent (real where available, else simulated) equity-curve performance deteriorates.
- **FR-018**: System MUST label every signal's outcome deterministically (HIT / STOP / EXPIRED) within its horizon as the ground truth, independent of the AI.

**Delivery & interaction**
- **FR-019**: System MUST deliver alerts over Telegram to a single private chat, 24/7, including: `SIGNAL` (with order ticket and an inline take/ignore confirmation), `TRADE_MANAGEMENT`, `INVALIDATED`, `TARGET_HIT`/`STOP_HIT`, `SECURITY_ALERT`, `MACRO_EVENT`, and `SYSTEMIC_ALERT`.
- **FR-020**: System MUST de-duplicate and cooldown alerts per symbol with no global daily cap, optionally grouping bursts into a digest.
- **FR-021**: System MUST let the operator confirm from the alert whether a signal was taken, record the resulting real position, and compute its real P&L distinctly from theoretical P&L.
- **FR-022**: System MUST provide a read-only dashboard (watchlist, asset detail with candles+indicators, signals with thesis/outcome, market context, performance KPIs, backtests) and a secured read API, accessible only from the private network/VPN; the dashboard exposes no order-placing controls.
- **FR-023**: System MUST expose no order-execution endpoint or capability of any kind in Phase 1.

**Validation & promotion**
- **FR-024**: System MUST run an automated validation pipeline — backtest with modeled fees/slippage and walk-forward, deterministic outcome labeling, shadow/forward test, risk-adjusted alpha-vs-HODL benchmark, and AI-as-judge evaluation with confidence calibration.
- **FR-025**: System MUST keep any strategy in shadow mode (logging, no Telegram alerts) until it meets the promotion KPIs including positive alpha vs HODL; a strategy whose production precision falls below threshold for N signals is automatically demoted back to shadow.

**Cross-cutting safeguards**
- **FR-026**: System MUST display a "not financial advice" disclaimer in the UI and in alerts; the operator decides and trades manually.
- **FR-027**: System MUST run privately with no inbound public exposure, encrypted transport even on the intranet, secrets held outside code, least-privilege access for the AI (read access plus the internal signal-publish path only), and pinned/audited dependencies.

### Key Entities *(conceptual — no implementation detail)*

- **Candle (OHLC)**: A price/volume bar for a symbol, venue, and timeframe at a timestamp.
- **Indicator set**: Computed technical values (trend, momentum, volatility, volume, trend-strength) and the derived **market regime** for a symbol/timeframe/timestamp.
- **Derivatives reading**: Funding rate, open interest, long/short ratio, recent liquidations for a symbol.
- **Context snapshot**: Aggregated sentiment, news, geopolitical risk, BTC dominance/state, security flags, systemic flags, macro-blackout and global-pause states at a timestamp.
- **Macro event**: A scheduled economic event with category, impact (maximum/medium), scheduled time, consensus/prior/actual.
- **Signal candidate**: A deterministically produced, scored potential signal with side, entry, stop, target, risk:reward, and features.
- **Signal**: The AI-decided final signal — side, levels, risk:reward, calibrated confidence, thesis, bull/bear cases, invalidation, status, and audit reference.
- **Order ticket**: The executable order attached to a signal — entry type/price, quantity/notional, structure (OCO/TP+SL/trailing), TP, SL trigger/limit, trailing, validity, target venue, exit plan.
- **AI audit record**: Inputs, summarized reasoning, model, and decision for a signal.
- **Alert**: A delivered notification of a given type tied to a signal.
- **Outcome**: The deterministic result of a signal (HIT/STOP/EXPIRED) with realized percentage.
- **Position**: A trade the operator confirmed as taken, with fills, partials, current stop, status, and real P&L.
- **Backtest / Strategy**: A parameter set and its metrics (including alpha-vs-HODL and calibration), with a lifecycle status (shadow / production / retired).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: At least **60%** of emitted signals reach +5% before their stop within the horizon, in forward-test.
- **SC-002**: Simulated **profit factor ≥ 1.8** and realized **risk:reward ≥ 1:2** across backtest and forward-test.
- **SC-003**: The strategy delivers **positive risk-adjusted alpha versus buy-and-hold** of BTC/ETH over the same period (hard promotion gate).
- **SC-004**: Confidence is calibrated to within a **≤ 10%** error (declared confidence ≈ real hit rate).
- **SC-005**: An emitted signal reaches the operator's Telegram **in under 30 seconds** from the triggering candle close.
- **SC-006**: Signal cadence is aspirationally **~2 per day with no cap** (and 0 on days without valid setups) — never a quota.
- **SC-007**: The 24/7 capture pipeline maintains **≥ 99% uptime**.
- **SC-008**: Irrelevant security alerts (false positives) stay **below 5%** of security alerts.
- **SC-009**: Monthly data cost is **0 €** in MVP and **< 50 €** in production; any paid upgrade requires demonstrated alpha.
- **SC-010**: **Zero** signals are emitted whose figures do not match the persisted deterministic values (no numeric hallucination reaches the operator).
- **SC-011**: **Zero** orders are placed, modified, or cancelled by the system in Phase 1.
- **SC-012**: **100%** of emitted signals carry a complete order ticket and an auditable decision trail.

## Assumptions

These reasonable defaults were taken from the binding brief where details were unspecified; the items under "Deferred to clarification" are refinements for `/speckit.clarify`, not blockers.

- **Operator model**: A single private operator (not multi-user / not SaaS); the operator places orders manually in Phase 1.
- **Direction & instrument**: LONG-only on **spot** in the MVP (no shorts, no leverage/derivatives trading — derivatives data is used only as a signal input).
- **Cadence & horizon**: Short-swing — base 1h with 15m confirmation and 4h/1d trend context; holding hours to ~1–2 days; no scalping (nothing sub-15m). Target +5% fixed; cadence ~2/day aspirational, uncapped.
- **Universe (default)**: BTC, ETH, and ~top-20 by liquidity, with a configurable watchlist; memecoins and stablecoins are excluded.
- **Target venue (default)**: Binance spot (native OCO), with a configurable per-symbol venue mapping and failover.
- **AI routing (default)**: Haiku 4.5 for cached context synthesis, Opus 4.8 for the final decision; ≈ €15/month token-cost ceiling.
- **Capital & risk (default)**: Reference capital €2,000–5,000; notional €500–1,000 per trade; dual-constraint sizing with a 2% per-trade risk ceiling, 6% aggregate risk cap, plus a correlation cap and free-capital limit.
- **Macro policy (default)**: Hybrid by impact — blackout for maximum-impact (rate decision, CPI, NFP), caution for medium-impact — with a 12h-before / 2h-after window, applied market-wide.
- **Validation horizon (default)**: A 2–4 week shadow/forward period before promotion; promotion KPIs precision ≥ 60%, profit factor ≥ 1.8, risk:reward ≥ 1:2, calibration error ≤ 10%, alpha-vs-HODL > 0.
- **Delivery**: Telegram to a single private chat, 24/7; UI strings in English (documentation/chat in Spanish).
- **Access**: Private only — no inbound public exposure; remote access via Cloudflare Zero Trust (Tunnel in private-network mode + WARP, no public hostname), which is unreachable from the public internet.
- **Data cost**: All MVP data sources are free; multi-source design tolerates provider tier changes via fallbacks.

### Deferred to `/speckit.clarify` (refinements with working defaults already in place)

_(Resolved in the Clarifications session 2026-06-13: exact universe, default target venue, AI model routing & cost ceiling, "BTC bearish" definition, and the default exit plan. Resolved 2026-06-14: Telegram alert language = **English** (aligned with the constitution's UI-string language; documentation/chat stay Spanish); remote access = **Cloudflare Zero Trust — Tunnel in private-network mode + WARP, no public hostname**, which keeps the service unreachable from the public internet and satisfies C-6/AC-07 (WARP is the VPN client; the tunnel is outbound-only). The items below remain open.)_

1. Exact reference capital within €2–5k and definitive risk percentage (2% accepted as ceiling).
2. Exact TA thresholds (EMA periods, RSI levels, MACD/Bollinger params, ATR stop multiplier) — initial values exist, to be tuned by backtest.
3. Macro-event impact classification (which events are maximum vs medium) and exact free-tier limits of the calendar source.
4. Exact shadow/forward duration before promotion.
5. Definitive promotion KPIs.
6. Remaining new-gate thresholds (minimum ADX, "extreme" funding, minimum 24h liquidity, depeg threshold, maximum correlation).
7. Exact trailing callback % and whether a second take-profit (TP2) tier is added beyond the default TP1+runner plan.
8. Real-P&L integration mechanism with the operator's portfolio tool and the derivatives/liquidations source free-tier limits.
