# Postman collection — AEGIS Internal API

`AEGIS.postman_collection.json` documents the **currently implemented** `/api/v1` endpoints.
Authoritative schema: [`specs/001-aegis-mvp/contracts/rest-api.openapi.yaml`](../../specs/001-aegis-mvp/contracts/rest-api.openapi.yaml).

## Import & configure
1. Postman → **Import** → select `AEGIS.postman_collection.json`.
2. Collection → **Variables**, set:
   - `baseUrl` — dev default `http://127.0.0.1:8000/api/v1`. Behind the Caddy/TLS reverse proxy it is `https://localhost/api/v1`, reachable only over the VPN (AC-07).
   - `apiKey` — must equal `AEGIS_API_KEY` in your `.env`.
   - `signalId` — paste a UUID from a `List signals` response to exercise the by-id requests.
3. Every request except **Health** sends `X-API-Key` automatically (collection-level auth).

## Requests
| Request | Method | Path | Auth | Notes |
|---|---|---|---|---|
| Health | GET | `/health` | none | private network only |
| List signals | GET | `/signals?status=` | API key | most-recent first; `status` optional |
| Get signal by id | GET | `/signals/{id}` | API key | 404 if unknown |
| Get order ticket | GET | `/signals/{id}/order` | API key | advisory ticket; never placed (C-1) |
| Publish signal (internal) | POST | `/internal/signals` | API key (loopback) | 201 ok · 409 reconciliation mismatch (AC-04) · 404 unknown candidate |

## Notes
- **Advisory only**: there is no order-execution endpoint anywhere (C-1, FR-023).
- Numeric fields are Decimal **strings** (e.g. `"2.00000000"`) — the deterministic source of truth (C-2).
- `POST /internal/signals` is the AI loopback path; a tampered figure returns **409** and is not persisted.

## Planned (not yet implemented — will be added as the stories land)
`GET /candles/{symbol}`, `GET /indicators/{symbol}`, `GET /context/{symbol}`,
`GET /signals/{id}/outcome`, `GET /performance`, `POST|GET /backtests` (admin/JWT),
`GET /audit/{signal_id}` (admin/JWT). See the OpenAPI contract for the full target surface.
