# Security Checklist: AEGIS MVP

**Purpose**: "Unit tests for requirements" validating that **security requirements** are complete,
clear, measurable, and consistent — testing the written requirements, not the implementation.
**Created**: 2026-06-14
**Feature**: [spec.md](../spec.md) · [plan.md](../plan.md)

## Network exposure & transport
- [ ] CHK001 Is "no inbound public exposure" specified with the concrete binding requirement (loopback/Docker network)? [Clarity, Spec §FR-027, AC-07]
- [x] CHK002 Is the remote-access mechanism defined as a requirement (Cloudflare Zero Trust: Tunnel private-network + WARP, no public hostname)? [Resolved 2026-06-14, research.md §A-9, AC-07]
- [ ] CHK003 Is "TLS always, including intranet" stated as a requirement for all transport? [Completeness, Spec §FR-027]
- [ ] CHK004 Are the negative requirements ("no port open to the WAN") expressed verifiably? [Measurability, AC-07]

## Authentication & authorization
- [ ] CHK005 Are the two auth schemes (API key for services/AI, JWT scopes for dashboard) specified with their scope boundaries (`read`/`admin`)? [Completeness, Spec §FR-027]
- [ ] CHK006 Is the per-endpoint auth requirement defined for every route in the contract (incl. `/internal/signals` loopback)? [Coverage, contracts/rest-api.openapi.yaml]
- [ ] CHK007 Are least-privilege requirements for the AI (read endpoints + `/internal/signals` only) unambiguous? [Clarity, Spec §FR-027]

## Secrets & data handling
- [ ] CHK008 Is "secrets outside code, never in logs" stated as a requirement with the storage mechanism (`.env`/Docker secrets)? [Completeness, Spec §FR-027, CLAUDE.md §8]
- [ ] CHK009 Are the required secret keys enumerated and the "never commit `.env`" rule captured? [Traceability, research.md §C / CLAUDE.md §8]
- [ ] CHK010 Is structured logging "without dumping sensitive bodies" specified as a requirement? [Clarity, Spec §FR-027]

## Rate limiting, CORS, hardening
- [ ] CHK011 Are rate-limiting and CORS-restricted-to-dashboard stated as requirements (even if thresholds are tuned later)? [Completeness, Spec §FR-027]
- [ ] CHK012 Are "pinned + audited dependencies" and the `pandas-ta` exclusion captured as security requirements? [Consistency, plan.md, CLAUDE.md §9]
- [ ] CHK013 Is vulnerability scanning in CI specified as a requirement? [Gap, plan.md Testing]
- [ ] CHK014 Are read-only filesystem / minimal images specified where feasible? [Coverage, Spec §plan]

## Threat model & failure response
- [ ] CHK015 Is the threat surface ("single-operator private financial system") documented so requirements trace to it? [Traceability]
- [ ] CHK016 Are requirements defined for the security-alert false-positive bound (< 5%)? [Measurability, Spec §SC-008]
- [ ] CHK017 Are incident/breach response requirements (e.g., global pause on exploit) defined? [Coverage, Spec §FR-005, AC-02/AC-17]
- [ ] CHK018 Is the "no exchange credentials in Phase 1" requirement consistent across security and C-1 sections? [Consistency, Spec §FR-023/FR-027]

## Notes
- These validate the *requirements*; runtime verification lives in tests (T022, T077, T085, T089/T091).
- Unchecked items in Network/Auth/Secrets are release-gate blockers for a financial system.
