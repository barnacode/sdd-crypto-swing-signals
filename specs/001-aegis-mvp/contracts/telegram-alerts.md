# Contract — Telegram Alerts (aiogram v3)

**Feature**: `001-aegis-mvp` | **Date**: 2026-06-13

Single private chat, 24/7. aiogram v3 handles outbound alerts and the inbound take/ignore loop
(ADR-019). Messages are in **English** (UI string language; chat/docs with the user are Spanish).
Every alert carries a **"not financial advice" disclaimer** (C-10, FR-026). No alert ever triggers an
order (C-1). Dedup + per-symbol cooldown; no global daily cap; optional digest on bursts (FR-020).

## Alert types (`alerts.type`)
| Type | Trigger | Carries | AC |
|------|---------|---------|----|
| `SIGNAL` | AI emits + reconciliation passes | order ticket + inline ✅/❌ buttons | AC-09 |
| `TRADE_MANAGEMENT` | position reaches TP1 / management event | partial + move-to-BE / trail / early-exit advice | AC-18 |
| `INVALIDATED` | invalidation condition hit | reason | — |
| `TARGET_HIT` | +5% reached before stop | realized % | AC-08 |
| `STOP_HIT` | stop reached | realized % | — |
| `SECURITY_ALERT` | active exploit/hack affecting an asset | asset, source, severity | AC-02 |
| `MACRO_EVENT` | max-impact event ≤ 12h | affected open positions | AC-13 |
| `SYSTEMIC_ALERT` | depeg / exchange incident → global pause | flag detail | AC-17 |

## `SIGNAL` payload (rendered)
```
🟢 SIGNAL — {symbol} {tf} LONG   confidence {n}/100   R:R {rr}
Thesis: {thesis}  (bull: {bull_case} / bear: {bear_case})
Invalidation: {invalidation}
Context: regime={regime} BTC={btc_state} sentiment={sentiment} derivs={...} security={...}

ORDER TICKET ({order_structure} @ {target_exchange})
  Entry  {entry_type} {entry_price}
  Size   {quantity} ({notional} €)
  TP     {take_profit}    SL {sl_trigger}/{sl_limit}
  Exit   TP1 +3% close 50% → stop to BE, trail rest → ≥+5% (callback {cb}%)
  TIF    {tif}   valid until {valid_until}
Dashboard: {link}
⚠️ Not financial advice. You place and manage the order manually.
[ ✅ Taken ]   [ ❌ Ignored ]
```

## Inbound confirmation loop (AC-19, C-16)
- `✅ Taken` → create `positions` row (`taken=true`), compute **real** P&L distinctly from theoretical;
  optionally link to CryptoLedger iOS as portfolio source.
- `❌ Ignored` → signal tracked as theoretical only.

## Commands
`/status` · `/signals` · `/positions` · `/pnl` · `/mute` · `/pause` (manual global pause).

## Contract tests (written before implementation, C-8)
- Each alert type renders required fields and the disclaimer.
- `SIGNAL` includes inline buttons and a fully-populated order ticket whose figures equal the
  persisted ticket (no hallucinated number, SC-010/SC-012).
- `✅ Taken` callback creates exactly one `positions` row and attributes real P&L.
- No code path in the bot can place/cancel an exchange order (SC-011, C-1).
