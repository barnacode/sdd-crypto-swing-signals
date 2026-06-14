# Constitution Checklist: AEGIS MVP

**Purpose**: "Unit tests for requirements" validating that the spec/plan/tasks **express** every
non-negotiable constitutional principle (C-1…C-16) as clear, complete, measurable requirements —
not whether the code works.
**Created**: 2026-06-14
**Feature**: [spec.md](../spec.md) · [constitution](../../../.specify/memory/constitution.md)

## C-1 Advisory only (no execution)
- [ ] CHK001 Is the "no order placed/modified/cancelled in Phase 1" requirement stated unambiguously and made objectively verifiable? [Clarity, Spec §FR-014/FR-023, SC-011]
- [ ] CHK002 Is the absence of any order-execution endpoint/capability specified as a requirement (not just an omission)? [Completeness, Spec §FR-023]
- [ ] CHK003 Is the boundary "no exchange trading credentials exist in Phase 1" documented as a requirement? [Completeness, Spec §FR-027]

## C-2 Determinism first
- [ ] CHK004 Is the requirement that every figure originates in Python and is persisted before AI use stated explicitly? [Clarity, Spec §FR-004/FR-009]
- [ ] CHK005 Is the post-AI numeric reconciliation requirement (signal figures must equal candidate/indicators) measurable? [Measurability, Spec §FR-010, AC-04]
- [ ] CHK006 Is "the AI never originates a numeric value" specified consistently across spec, plan, and skill contracts? [Consistency, Spec §FR-009]

## C-3 Auditable & reproducible
- [ ] CHK007 Are the exact fields to persist per decision (inputs, prompt hash, reasoning, model, decision) enumerated? [Completeness, Spec §FR-011]
- [ ] CHK008 Are "low temperature" and "schema-validated structured output" stated as requirements, not implementation notes? [Clarity, Spec §FR-009/FR-011]

## C-4 Fail-safe
- [ ] CHK009 Are all fail-safe triggers (AI unavailable, invalid output, missing/unresolved figure) enumerated as requirements? [Completeness, Spec §FR-012, AC-05]
- [ ] CHK010 Is the rule "never degrade to a lower-quality signal to avoid silence" expressed unambiguously? [Clarity, Spec §Edge Cases]

## C-5 Validation before production
- [ ] CHK011 Are the promotion-gate KPIs (precision, PF, R:R, calibration, alpha) specified with concrete thresholds? [Measurability, Spec §SC-001..004, FR-025]
- [ ] CHK012 Is the circuit-breaker demotion condition (precision < threshold for N signals) quantified? [Clarity, Spec §FR-025]
- [ ] CHK013 Is "fees and slippage modeled mandatorily" stated as a validation requirement? [Completeness, Spec §FR-024]

## C-6 Private & secure
- [ ] CHK014 Are "no inbound public exposure", "TLS always", and "secrets outside code" each stated as discrete requirements? [Completeness, Spec §FR-027, AC-07]
- [ ] CHK015 Is the AI's least-privilege data access (internal API only, never the DB) specified? [Clarity, Spec §FR-027]

## C-7 Cost controlled
- [ ] CHK016 Are the cost ceilings (€0 MVP data, < €50/month production, ≈ €15/month AI) stated as measurable requirements? [Measurability, Spec §SC-009]
- [ ] CHK017 Are the cost-bounding mechanisms (cached context, AI only on candidates, single-round debate) specified? [Completeness, Spec §FR-013]

## C-8 TDD
- [ ] CHK018 Does the tasks plan require tests authored and failing before each implementation task? [Coverage, tasks.md]
- [ ] CHK019 Is "every bug fix ships a real-data regression test" captured as a standing requirement? [Gap, CLAUDE.md §2]

## C-9 Zero technical debt
- [ ] CHK020 Is the prohibition on `TODO: fix later` / silenced errors stated as a requirement on the work, not just a guideline? [Clarity, CLAUDE.md §7]

## C-10 Not financial advice
- [ ] CHK021 Is the disclaimer requirement specified for **every** user-facing surface (each alert type + dashboard)? [Coverage, Spec §FR-026]

## C-11 Soundness over frequency
- [ ] CHK022 Is "0 signals when no confluence" specified and the cadence explicitly marked aspirational/uncapped? [Clarity, Spec §SC-006, Edge Cases]
- [ ] CHK023 Is the prohibition on relaxing gates to hit a cadence stated as a requirement? [Consistency, Spec §Edge Cases]

## C-12 Bounded sizing
- [ ] CHK024 Are all sizing constraints (dual-constraint, 6% aggregate, correlation cap, free-capital) enumerated with values? [Completeness, Spec §FR-015, AC-10]

## C-13 Beat HODL
- [ ] CHK025 Is "risk-adjusted alpha-vs-HODL > 0" specified as a hard promotion gate, not a soft goal? [Clarity, Spec §SC-003, AC-16]

## C-14 Systemic safeguards
- [ ] CHK026 Are the systemic triggers (stablecoin depeg threshold, exchange/chain incident) and the global-pause response specified? [Completeness, Spec §FR-005, AC-17]

## C-15 BTC rules
- [ ] CHK027 Is the "BTC bearish" definition (1d close < EMA200) stated precisely enough to be testable? [Measurability, Spec §FR-005, AC-14]

## C-16 Honest P&L
- [ ] CHK028 Is the separation of theoretical vs real P&L (and "use real when present") specified as a requirement? [Clarity, Spec §FR-021, AC-19]

## Governance & cross-cutting
- [ ] CHK029 Is it specified that no feature advances a phase while violating a C-principle without an approved amendment? [Consistency, constitution Governance]
- [ ] CHK030 Are there any requirements that conflict with a MUST principle anywhere in spec/plan/tasks? [Conflict]

## Notes
- Check items off as `[x]` once the requirement text satisfies the question (this validates the *spec*, not the build).
- Any unchecked CRITICAL (C-1, C-2, C-5, C-13) item blocks `/speckit.implement`.
