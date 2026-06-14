# Quality Checklist: AEGIS MVP

**Purpose**: "Unit tests for requirements" validating overall **requirements quality** —
completeness, clarity, consistency, measurability, and coverage across spec/plan/tasks.
**Created**: 2026-06-14
**Feature**: [spec.md](../spec.md) · [plan.md](../plan.md) · [tasks.md](../tasks.md)

## Requirement completeness
- [ ] CHK001 Does every user story (US1–US6) have an independent test that can be evaluated without other stories? [Completeness, Spec §User Scenarios]
- [ ] CHK002 Are all 27 FRs traceable to at least one task? [Coverage, tasks.md AC/FR mapping]
- [ ] CHK003 Are the deterministic pre-gates (G1–G5) each specified as a discrete requirement with an input and a pass/fail meaning? [Completeness, Spec §FR-005]
- [ ] CHK004 Are all Telegram alert types enumerated and each tied to a triggering requirement? [Coverage, Spec §FR-019, contracts/telegram-alerts.md]

## Requirement clarity
- [ ] CHK005 Is "short-swing" quantified (timeframes, holding horizon, target %)? [Clarity, Spec §Assumptions]
- [ ] CHK006 Are the confluence conditions stated precisely enough to be testable (EMA/RSI/MACD/volume/structure/ATR)? [Measurability, research.md §B-1]
- [ ] CHK007 Is the order-ticket structure (OCO / TP_SL / MARKET_TRAILING) and the venue-degrade rule unambiguous? [Clarity, Spec §FR-014, AC-11]
- [ ] CHK008 Is the default exit plan (TP1 +3% close 50% → BE → trail ≥ +5%) specified without ambiguity? [Clarity, Spec §FR-016, AC-18]

## Measurable acceptance criteria
- [ ] CHK009 Are all 12 Success Criteria expressed as numbers/units (not vague adjectives)? [Measurability, Spec §SC-001..012]
- [ ] CHK010 Is latency SC-005 (< 30 s to Telegram) and AC-01 (≤ 5 s recompute) each tied to a specific event boundary? [Clarity, Spec §SC-005, AC-01]
- [ ] CHK011 Is the uptime target SC-007 backed by a requirement that makes it buildable/measurable? [Gap, tasks.md T090]

## Consistency
- [ ] CHK012 Is the symbol universe described consistently across spec/plan/data-model (BTC, ETH + ~top-20, no meme/stablecoins)? [Consistency, Spec §FR-001]
- [ ] CHK013 Are entity names consistent between data-model.md, contracts, and tasks (e.g., `signal_candidates`, `order_tickets`)? [Consistency, data-model.md]
- [ ] CHK014 Is the AI routing (Haiku context / Opus decision, ≈ €15/mo) stated identically in spec, plan, research, and skill contracts? [Consistency, research.md §A-5]

## Scenario & edge-case coverage
- [ ] CHK015 Are requirements defined for the zero-signal day (no valid setup)? [Coverage, Spec §Edge Cases]
- [ ] CHK016 Are requirements defined for provider outage / tier change (failover, conservative macro fallback)? [Coverage, Spec §Edge Cases]
- [ ] CHK017 Are correlated-candidate and multiple-simultaneous-setup behaviors specified? [Coverage, Spec §Edge Cases]
- [ ] CHK018 Are requirements defined for theoretical-vs-real P&L divergence? [Coverage, Spec §Edge Cases, FR-021]

## Dependencies & assumptions
- [ ] CHK019 Are the free-tier data-provider assumptions documented and marked as risks where limits are unverified? [Assumption, research.md §C]
- [ ] CHK020 Are the remaining deferred items listed with working defaults so none blocks implementation? [Completeness, Spec §Deferred]

## Ambiguities & conflicts
- [ ] CHK021 Are there any remaining vague adjectives ("strong", "conservative", "solid") used without a measurable definition? [Ambiguity]
- [ ] CHK022 Do any tasks reference files/components not present in plan.md's structure? [Conflict, tasks.md]
- [ ] CHK023 Is the test coverage gate (≥ 80%) confirmed as a definitive requirement rather than a proposal? [Ambiguity, CLAUDE.md §13]

## Notes
- This validates the requirements' quality; it does not test the running system.
- CHK023 corresponds to the still-open "confirm coverage threshold" decision flagged earlier.
