# Contract — Claude Code AI Skills (structured I/O)

**Feature**: `001-aegis-mvp` | **Date**: 2026-06-13

Seven skills make up the AI layer (brief §9.2). Each has a `SKILL.md` and a **schema-validated
structured output** (low temperature). The AI reaches data **only via the FastAPI internal API**,
never the DB directly (C-6 least privilege). The AI **never originates a numeric value** — it
selects, weights, explains, and decides (C-2). Any output that fails its schema ⇒ no signal
(fail-safe, C-4). Routing: `market-context` → Haiku 4.5; `signal-analyst`/`risk-guardian`/
`exit-manager` decisions → Opus 4.8 (C-7).

These contracts are the basis for **contract tests** written before implementation (C-8): a test
feeds a fixed input and asserts the output validates against the schema and contains no figure absent
from the persisted candidate/indicators.

---

## 1. `market-context`  (Haiku 4.5)
Roles: News/Social/Fundamentals analyst. Synthesizes raw feeds into a cached snapshot.

**Input**: raw feeds (sentiment, news, geo, macro calendar, regime, BTC state, derivatives, security).
**Output**:
```json
{
  "sentiment": "bullish|bearish|neutral",
  "news_impact": "high|medium|low",
  "geo_risk": 0.0,
  "regime": "trending|ranging|high_vol",
  "btc_state": "bullish|bearish|neutral",
  "derivatives": { "funding": 0.0, "oi_trend": "up|down|flat", "liq_pressure": "high|low" },
  "upcoming_macro_events": [ { "name": "FOMC", "impact": "maximum|medium", "eta_hours": 0 } ],
  "security_flags": [ { "asset": "X", "severity": "high|med", "source": "PeckShield" } ],
  "systemic_flags": [ { "type": "depeg", "asset": "USDT", "deviation_pct": 0.0 } ],
  "summary": "string (<= 5 sentences)"
}
```
**Invariant**: all numeric fields are echoed from inputs, not invented.

## 2. `signal-analyst`  (Opus 4.8)
Roles: Bull/Bear researchers + Trader. Single-round debate over already-filtered candidates.

**Input**: `signal_candidates[]` (with order ticket + features) + `market-context` snapshot.
**Output** (per candidate, decision one of emit/discard/watch):
```json
{
  "decision": "emit|discard|watch",
  "side": "LONG",
  "entry": 0.0, "stop": 0.0, "target": 0.0, "rr": 0.0,
  "confidence": 0,
  "thesis": "string",
  "bull_case": "string",
  "bear_case": "string",
  "invalidation": "string",
  "exit_plan": { "tp1_pct": 3.0, "tp1_close_pct": 50, "move_to_be": true, "trail_callback_pct": 1.2 }
}
```
**Invariant**: `entry/stop/target/rr` MUST equal the candidate's persisted values byte-for-byte
(reconciliation, AC-04). `confidence` is the only number the AI originates (it is a judgment, not a
market figure) and is later calibration-checked.

## 3. `risk-guardian`  (Opus 4.8)
Roles: Risk/Portfolio manager. Vetoes signals violating sizing/exposure rules.

**Input**: candidate signal + current portfolio (open positions, free capital, correlation matrix).
**Output**:
```json
{
  "approved": true,
  "reasons": ["string"],
  "size_suggestion": { "quantity": 0.0, "notional": 0.0 }
}
```
**Invariant**: enforces dual-constraint sizing, 6% aggregate cap, correlation cap, free-capital limit
(FR-015, AC-10); rejects if no free capital for the notional.

## 4. `exit-manager`  (Opus 4.8)
Dynamic post-entry management (advisory). Runs per candle close on open positions.

**Input**: open `position` + current market (price, indicators, context).
**Output**:
```json
{ "action": "hold|take_partial|move_stop_be|trail|early_exit", "new_stop": 0.0, "take_pct": 0, "reason": "string" }
```
**Invariant**: at TP1 advises partial + move-to-breakeven (AC-18); never executes (C-1).

## 5. `alert-composer`
Renders the Telegram message (English) and persists. No decision-making.

**Input**: signal / management event.
**Output**: rendered message text + delivery result; persists `alerts` row. Must include the
"not financial advice" disclaimer (C-10) and the copy-paste order ticket.

## 6. `backtest-runner`
Launches vectorbt with modeled fees (~0.1% taker) + slippage; returns metrics.

**Input**: strategy + params + date range.
**Output**:
```json
{ "profit_factor": 0.0, "win_rate": 0.0, "max_dd": 0.0, "rr": 0.0, "trades": 0, "alpha_vs_hodl": 0.0 }
```

## 7. `signal-evaluator`  (validation, LLM-as-judge)
Judges signals vs deterministic outcomes; reports calibration. Does NOT label outcomes (code does).

**Input**: signals[] + outcomes[] (outcomes fixed by code).
**Output**:
```json
{ "precision": 0.0, "recall": 0.0, "false_pos": 0.0, "calibration_error": 0.0, "notes": "string" }
```
**Invariant**: receives outcomes as fixed ground truth; cannot optimize the labeling (anti-overfit, §13.2).
