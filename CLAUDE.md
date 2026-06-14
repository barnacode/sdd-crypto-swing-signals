# CLAUDE.md — AEGIS Operating Rules

> Operational guide for the AI agent working on **AEGIS** (Algorithmic Edge & Guidance
> Intelligence System). These are **HARD RULES** — non-negotiable defaults for every turn.
> They complement, never override, the project constitution. When in doubt, the constitution wins.

## Sources of truth (read before acting)

1. `.specify/memory/constitution.md` — binding principles **C-1…C-16** + governance. Authoritative.
2. `PROJECT-BRIEF.md` (root) — vision, closed stack, ADR-001…020, EARS acceptance criteria.
3. `specs/001-aegis-mvp/` — current feature spec, checklists, and (later) plan/tasks.

This file does **not** restate the constitution; it makes it operational. If anything here seems to
conflict with `constitution.md`, the constitution prevails and you must flag the discrepancy.

---

## 1 · Language (HARD)

- **All repo artifacts are written in English**: code, comments, identifiers, commit messages,
  docs, specs, and the instructions in this file. App/dashboard user-facing strings: English (per
  constitution "Restricciones Tecnológicas").
- **Chat communication with the user is ALWAYS in Spanish, no exception.** Every reply, summary,
  question, and status update in the conversation is in Spanish, regardless of the language of the
  code or files being discussed.

## 2 · TDD first (HARD) — see C-8

- **Tests are written before implementation.** No production code without a failing test that
  justifies it. The **Red → Green → Refactor** cycle is mandatory.
- Every bug fix ships with a **regression test using real data** before the fix.
- One commit per task (C-8). A task with passing tests but no prior test is a TDD violation —
  call it out and correct it.

## 3 · Quality gates before "done" (HARD)

- A task is **not complete** until **lint + type-check + the full relevant test suite pass green**.
- Never report a task as finished without having actually run those checks this session.
- Honor the SDD quality gates: Constitution Check at `/speckit.plan`, AC coverage at
  `/speckit.analyze`, security/quality/constitution checklists before implementing.

## 4 · Verify before claiming (HARD)

- **Show real output.** When reporting results, base them on the actual output of the tests/commands
  you ran, not on expectation.
- If something fails, say so with the output. If a step was skipped, say it was skipped. No hedging,
  no "should work" — state what is verified and what is not.

## 5 · Commits & version control (HARD)

- **Conventional Commits**, written in English, atomic, one logical change per commit, each tied to
  its SDD task / AC-ID.
- **Never `git commit` or `git push` without explicit user authorization.** Approval for one commit
  does not extend to the next.
- **Never work directly on `main`.** Work on the feature branch (currently `001-aegis-mvp`); the
  spec-kit git hooks own branch creation.

## 6 · SDD traceability (HARD)

- **No code outside the SDD flow.** Order is mandatory and phases are never skipped:
  `constitution → specify → clarify → plan → tasks → analyze → taskstoissues → checklist → implement`.
  `clarify`, `analyze`, and `taskstoissues` are **mandatory** (sponsor rule).
- Every change traces to a concrete spec/task and, where applicable, an **AC-ID in EARS** format.
- No feature advances a phase if it violates a C-1…C-16 principle without an approved amendment.

## 7 · Small, reversible changes (HARD)

- Keep diffs scoped to the current task. **No unsolicited mass refactors**, no touching files outside
  the task's scope.
- Prefer reversible steps. For anything hard to reverse or outward-facing, confirm first.
- **Zero technical debt** (C-9): no `TODO: fix later`, no silenced errors, no unjustified shortcuts.

## 8 · Secrets & security (HARD)

- **Never commit secrets** (API keys, credentials, tokens). Everything via `.env` / Docker secrets;
  `.env` stays in `.gitignore`. Secrets never appear in logs.
- Respect the security posture in the constitution: no inbound exposure, TLS always, least privilege.
  The AI accesses data **only via the internal API**, never the DB directly, and **never** holds
  exchange trading credentials (they do not exist in Phase 1 — C-1).

## 9 · No invented APIs (HARD)

- **Do not hallucinate** function signatures, library APIs, or config. Before generating code against
  any library/framework, consult up-to-date docs (Context7 MCP / official docs).
- Respect the **closed stack** (constitution + brief §3). Notably: **`pandas-ta` original is
  FORBIDDEN** (abandoned, supply-chain attack signals) — use **`pandas-ta-classic`**. Use TA-Lib,
  `ccxt` async **public endpoints only**, FastAPI, aiogram v3, PostgreSQL + TimescaleDB, APScheduler,
  vectorbt + backtesting.py, Next.js + lightweight-charts. Adding/changing a dependency needs
  justification and pinning.

## 10 · Real, traceable market data (HARD)

- **Never mock or fabricate market data outside of tests.** Determinism boundary is sacred (C-2):
  every number (price, indicator, level, R:R, size, order ticket) is produced by Python and
  persisted; the LLM decides/prioritizes/explains but **never invents figures**.
- Test fixtures must use **real, traceable data**; data sources (CoinGecko, exchange public APIs,
  etc.) are explicit and verifiable.

## 11 · Advisory-only, not financial advice (HARD) — see C-10

- AEGIS **emits informational signals; it never executes orders** in Phase 1 (C-1) and is **not
  financial advice** (C-10).
- Every user-facing output (alert, UI, dashboard) **must carry an explicit disclaimer**. The human
  operator decides and trades manually.

## 12 · Constitution is untouchable without amendment (HARD)

- **Do not modify `constitution.md`** except through the explicit amendment process: an ADR, a
  semantic-version bump, and a migration plan when existing artifacts/code are affected.
- Enabling real automated execution (C-1) requires a **MAJOR** amendment with the controls listed in
  C-1 / ADR-011. Never quietly relax a principle.

## 13 · Test coverage gate (HARD)

- CI enforces a **minimum coverage threshold of ≥ 80%** (proposed default — confirm/adjust in the
  plan/CI config). Financial-critical logic (indicators, candidate engine, sizing, determinism check)
  targets higher. Coverage below the gate blocks merge.

---

**Precedence:** constitution.md > this file > spec/plan/tasks > ad-hoc decisions. Flag any conflict
instead of silently resolving it.

## Active Technologies
- Python 3.12 (backend/analysis); TypeScript / Node 20 (dashboard) + ccxt (async, public endpoints only), TA-Lib + `pandas-ta-classic` (001-aegis-mvp)
- PostgreSQL + TimescaleDB (single source of truth — hypertables for OHLC/indicators/ (001-aegis-mvp)

## Recent Changes
- 001-aegis-mvp: Added Python 3.12 (backend/analysis); TypeScript / Node 20 (dashboard) + ccxt (async, public endpoints only), TA-Lib + `pandas-ta-classic`
