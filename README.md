# AEGIS — Algorithmic Edge & Guidance Intelligence System

Private, local, 24/7 system that watches a curated crypto universe, computes technical analysis
**deterministically in Python**, lets a **Claude Code AI layer** reason over the scored candidates,
and delivers **advisory** short-swing signals over Telegram with a copy-paste order ticket.

> ⚠️ **Advisory only — not financial advice.** Phase 1 never places, modifies, or cancels orders.
> The human operator decides and trades manually (constitution C-1 / C-10).

## Status

Built with **Spec-Driven Development** (spec-kit). The full SDD flow (constitution → specify →
clarify → plan → tasks → analyze → checklist) is complete; implementation is in progress on the MVP
(User Story 1). Live progress: [`ROADMAP.md`](./ROADMAP.md) (high level) and
[`specs/001-aegis-mvp/tasks.md`](./specs/001-aegis-mvp/tasks.md) (per-task).

## Sources of truth

| Document | What |
|---|---|
| [`.specify/memory/constitution.md`](./.specify/memory/constitution.md) | Binding principles **C-1…C-16** (authoritative) |
| [`PROJECT-BRIEF.md`](./PROJECT-BRIEF.md) | Vision, closed stack, ADRs, acceptance criteria |
| [`specs/001-aegis-mvp/`](./specs/001-aegis-mvp/) | Feature spec, plan, data model, contracts, tasks |
| [`CLAUDE.md`](./CLAUDE.md) | Hard operating rules for the AI agent |

## Stack (closed)

Python 3.12 · ccxt (async, public endpoints only) · TA-Lib + **`pandas-ta-classic`** (⚠️ original
`pandas-ta` is forbidden — supply-chain risk) · PostgreSQL + **TimescaleDB** · FastAPI · aiogram v3 ·
APScheduler · vectorbt + backtesting.py · Next.js + lightweight-charts · Claude Opus 4.8 / Haiku 4.5 ·
Docker Compose, Caddy/TLS, Cloudflare Zero Trust (remote access).

## Requirements

- **Python 3.12** via [`uv`](https://docs.astral.sh/uv/) (manages the interpreter and venv)
- **Docker** (Docker Desktop or Colima) for TimescaleDB; `docker compose` v2 or `docker-compose`
- **Node 20** (dashboard, later)
- Optional: TA-Lib C library (`brew install ta-lib`) — only to enable the optional accelerator;
  `pandas-ta-classic` is the primary engine and needs no system lib
- Free-tier API keys + `ANTHROPIC_API_KEY` in `.env` (see [`.env.example`](./.env.example))

## Quick start

```bash
# 1. Secrets (never commit .env — it is gitignored)
cp .env.example .env            # fill ANTHROPIC_API_KEY and the free-tier keys

# 2. Database (TimescaleDB)
docker run -d --name aegis-tsdb \
  -e POSTGRES_USER=aegis -e POSTGRES_PASSWORD=aegis -e POSTGRES_DB=aegis \
  -p 127.0.0.1:5432:5432 timescale/timescaledb:2.17.2-pg16
#   (or, once the image is local: docker-compose up -d timescaledb)

# 3. Backend deps (uv pins Python 3.12 and installs everything)
cd backend && uv sync --group dev --extra indicators
```

## Commands (run from `backend/`)

```bash
uv run pytest                      # full test suite (DB tests auto-skip if no TimescaleDB)
uv run pytest --cov                # with coverage (gate: >= 80%)
uv run ruff check .                # lint
uv run ruff check --fix .          # lint + autofix
uv run mypy                        # type-check (strict)
uv run uvicorn aegis.api.app:create_app --factory --host 127.0.0.1 --port 8000   # run the API (dev)
```

The integration/contract tests run against a real TimescaleDB; point them elsewhere with
`AEGIS_TEST_DB_DSN`. Without a database they skip automatically so the unit suite still runs.

## API

Private read API under `/api/v1` (loopback / VPN only — never public, AC-07). Try it with the
[Postman collection](./docs/postman/) or the OpenAPI contract at
[`specs/001-aegis-mvp/contracts/rest-api.openapi.yaml`](./specs/001-aegis-mvp/contracts/rest-api.openapi.yaml).
**No order-execution endpoint exists** (C-1).

## Development rules

Read [`CLAUDE.md`](./CLAUDE.md): Spanish chat / English repo, **TDD first**, quality gates before
"done", Conventional Commits, no commit/push without authorization, secrets hygiene, advisory-only
disclaimer, and the determinism boundary (Python owns every number; the AI never invents figures).
