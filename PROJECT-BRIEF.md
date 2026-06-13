# AEGIS — Algorithmic Edge & Guidance Intelligence System
### Documento de instrucciones del proyecto · Semilla para planificación SDD estricta

> **Qué es esto:** brief maestro y vinculante para arrancar un proyecto *greenfield* mediante Spec-Driven Development (spec-kit). Alimenta directamente `/speckit.constitution` y `/speckit.specify`. Contiene visión, alcance, stack, proveedores, arquitectura, seguridad, skills de IA, plan de validación y los `[NEEDS CLARIFICATION]` a resolver en `/speckit.clarify`.
>
> **Estado:** borrador v1.3 (2026-06-13). Decisiones de producto cerradas con el patrocinador (cadencia short-swing, ficha de orden, sizing, calendario macro y las 8 mejoras del gap analysis "mejor advisor"). Pendiente: ejecutar el flujo SDD.
>
> **Cambios v1.1 vs v1.0:** cadencia **short-swing intradía** (base 1h + confirmación 15m) en vez de swing de días-semanas; objetivo **aspiracional ~2 señales/día sin tope** (se notifican todas las sólidas); cada señal incluye **ficha de orden ejecutable** (entrada, TP/SL, OCO, trailing); **ejecución automática real** movida a fase futura con enmienda constitucional (ADR-011); **modelo de sizing de doble restricción** (ADR-012); operación **24/7**.
>
> **Cambios v1.2 vs v1.1:** **calendario económico macro** (FOMC, CPI, NFP, PIB USA, PCE) como fuente forward (FMP + FRED + fechas FOMC, 0€); **política pre-evento híbrida por impacto** — blackout en eventos de máximo impacto, flag de cautela en los medios — con ventana **12h antes / 2h después** (ADR-013); nuevo aviso Telegram `MACRO_EVENT`.
>
> **Cambios v1.3 vs v1.2 (gap analysis "mejor advisor"):** (1) **régimen de mercado + gate BTC** (ADX/volatilidad/dominancia; alts gateadas por estado de BTC, ADR-014); (2) **datos de derivados/posicionamiento** funding/OI/long-short/liquidaciones (ADR-015); (3) **gestión dinámica de salida** scale-out + breakeven + trailing (ADR-016); (4) **KPI alpha vs HODL** + **matriz de correlación** de cartera (ADR-017); (5) **chequeo de liquidez/spread** por activo; (6) **salvaguardas sistémicas** depeg de stablecoins + salud de exchange (ADR-018); (7) **bucle de confirmación de trade + P&L real** e integración con CryptoLedger iOS (requiere Telegram interactivo/aiogram, ADR-019); (8) **calibración de confianza + throttle por curva de equity** (ADR-020). Constitución ampliada a C-1…C-16.

---

## 0. TL;DR — qué vamos a construir

Un sistema **privado, local y 24/7** que vigila el mercado cripto, calcula análisis técnico determinista (EMA/RSI/MACD/…), lo cruza con sentimiento de comunidad, noticias, geopolítica y alertas de seguridad, y deja que un **Agente de IA (Claude Code)** razone sobre todo ello para **emitir señales short-swing sólidas** (cadencia **aspiracional ~2/día, sin tope**; objetivo ≥5% por posición; perfil conservador) que llegan **por Telegram** con una **ficha de orden lista para ejecutar** (entrada, TP/SL, OCO, trailing). Incluye **API** y **Dashboard** (Next.js + TradingView).

**Es un sistema de SOLO-SEÑAL (advisory). En Fase 1 NUNCA ejecuta órdenes:** emite la ficha de orden completa pero el *humano* (o, en una fase futura, un módulo de ejecución separado) la coloca en Binance, MEXC, Coinbase o BitMart. La **ejecución automática real** es una **fase futura** con su propia enmienda constitucional (ADR-011).

**Arquitectura de decisión (híbrida):** Python calcula los números (determinismo, reproducibilidad); Claude Code razona, filtra y emite la alerta con justificación auditable. El LLM nunca inventa cifras: solo decide, prioriza y explica sobre datos ya calculados.

**MVP 100% gratis** en proveedores de datos; se paga solo si se demuestra alpha.

---

## 1. Visión y objetivos

### 1.1 Problema
Tomar decisiones de swing trading consistentes exige vigilar simultáneamente precio/volumen, indicadores técnicos, sentimiento social, noticias macro/geopolíticas y eventos de seguridad (hacks/exploits) — imposible de hacer a mano 24/7 sin sesgo emocional ni fatiga.

### 1.2 Solución
Automatizar la **captura → cálculo → razonamiento → alerta** con un agente de IA que aplica reglas de confluencia estrictas y entrega señales accionables con su tesis, nivel de confianza, entrada/stop/objetivo y motivo de invalidación.

### 1.3 Objetivos medibles (North-Star + KPIs)
| KPI | Meta MVP | Cómo se mide |
|---|---|---|
| **Precisión de señal** (señales que alcanzan +5% antes del stop, en el horizonte) | ≥ 60% en forward-test | Etiquetado automático de outcomes (ver §13) |
| **Profit factor** (ganancia bruta / pérdida bruta simulada) | ≥ 1.8 | Backtest + forward-test |
| **Ratio R:R medio realizado** | ≥ 1:2 | Por señal |
| **Alpha vs HODL** (¿bate a comprar-y-aguantar BTC/ETH, ajustado por riesgo?) | **> 0** (gate de promoción) | Comparativa vs buy-and-hold (§13) |
| **Calibración de confianza** (¿la confianza declarada ≈ hit rate real?) | error de calibración ≤ 10% | signal-evaluator (§13) |
| **Latencia señal→alerta Telegram** | < 30 s desde cierre de vela 1h/15m | Telemetría |
| **Cadencia de señal** | aspiracional **~2/día** (sin tope; 0 en días flojos) | Conteo |
| **Uptime del scraper 24/7** | ≥ 99% | Healthchecks |
| **Falsos positivos de seguridad** (alertas de hack irrelevantes) | < 5% | Revisión muestral IA |
| **Coste mensual de datos** | 0 € en MVP, < 50 € en producción | Facturación |

> El objetivo "≥5% por posición con máximas garantías" se materializa como: **perfil conservador + confluencia múltiple + R:R mínimo 1:2 + gate de validación antes de ir a producción** (§7, §13). La cadencia de ~2/día es **aspiracional, no una cuota**: prevalece la solidez (un día sin setups válidos = 0 señales); si hay más de 2 setups sólidos, se notifican todos (con dedup/cooldown por símbolo).

### 1.4 No-objetivos (MVP)
- ❌ **Ejecución automática real de órdenes** / conexión a fondos / claves con permisos de trading. *(Sí se emite la ficha de orden; colocarla es manual en Fase 1. La ejecución automática es fase futura — ADR-011.)*
- ❌ Gestión de cartera real, contabilidad fiscal (eso es el otro proyecto, CryptoLedger iOS).
- ❌ **Scalping / HFT / velas sub-15m.** El short-swing opera en base **1h con confirmación 15m**; no bajamos de ahí.
- ❌ Derivados/apalancamiento en el MVP (solo spot; perps en roadmap).
- ❌ Multiusuario / SaaS (es privado, un solo operador).

---

## 2. Alcance del MVP

### 2.1 Dentro de alcance (MVP = API + Dashboard + Alertas Telegram, sin ejecución automática)
1. **Ingestión 24/7** de OHLCV (**15m/1h** base + 4h/1d para contexto de tendencia) de Binance, MEXC, Coinbase, BitMart vía `ccxt` (público, sin keys), **+ derivados** (funding/OI/long-short/liquidaciones) y **dominancia BTC**.
2. **Universo:** Top majors (BTC, ETH y ~top 20 por liquidez). Watchlist configurable. *(ver `[NEEDS CLARIFICATION #1]`)*
3. **Cálculo determinista** de indicadores: EMA(s), SMA, RSI, MACD, Bollinger, ATR, **ADX (fuerza de tendencia)**, volumen relativo, niveles soporte/resistencia, **régimen de mercado**.
3b. **Régimen de mercado + gate BTC, chequeo de liquidez/spread y lectura de derivados** como filtros previos a toda señal (§7).
4. **Capa de contexto (gratis):** Fear & Greed, sentimiento social (Reddit + Santiment free), noticias (RSS CoinDesk/Cointelegraph + CryptoPanic), geopolítica/macro reactiva (GDELT), **calendario económico forward (FMP + FRED + fechas FOMC)**, seguridad (PeckShield Telegram + De.Fi + rekt.news). *(A escala intradía el sentimiento actúa como filtro de régimen, no como trigger — ver §4.2; el calendario macro habilita el filtro pre-evento — ver §4.4 y §7.6.)*
5. **Motor de candidatos** (Python, determinista): aplica reglas de confluencia y produce "candidatos de señal" puntuados, con **ficha de orden** (entrada, TP/SL, OCO, trailing, tamaño).
6. **Agente de IA (Claude Code, cron):** razona sobre candidatos + contexto, decide la señal final, asigna confianza, redacta tesis y publica.
7. **API REST (FastAPI)** securizada: señales, velas, indicadores, contexto, salud, backtests.
8. **Dashboard (Next.js + lightweight-charts):** velas + indicadores + régimen + derivados + panel de señales + ficha de orden + plan de salida + contexto de mercado + histórico/performance (incl. alpha vs HODL).
9. **Alertas Telegram** salientes con la señal completa **+ ficha de orden lista para ejecutar** (copiar/pegar), **avisos de gestión de salida** y **confirmación interactiva de trade** (botón "¿la tomaste?") → P&L real.
10. **Backtesting + forward-test automatizados** con etiquetado de outcomes, **modelado de comisiones/slippage** y reporte de métricas (§13).
11. **Persistencia** en PostgreSQL + TimescaleDB (OHLC, indicadores, señales, fichas de orden, alertas, outcomes, contexto).

### 2.2 Fuera de alcance (roadmap post-MVP)
- **Ejecución automática real** (módulo separado, ADR-011) · Perps/futuros y funding rates · On-chain de pago (Santiment Pro) · Sentimiento social realtime de pago · Más exchanges · ML propio de sentimiento · App móvil · Multiusuario.

---

## 3. Stack tecnológico (decisiones cerradas + justificación)

| Capa | Elección | Por qué (resumen de la investigación) |
|---|---|---|
| **Lenguaje backend/análisis** | **Python 3.12** | Ecosistema cuantitativo y de datos superior (TA, backtesting, NLP). |
| **Datos de exchange** | **ccxt (async)** | Interfaz unificada; **Binance, MEXC, Coinbase y BitMart confirmados** con `fetch_ohlcv`. Solo endpoints públicos (sin claves, sin riesgo de fondos). |
| **Indicadores técnicos** | **TA-Lib** (motor C) **+ `pandas-ta-classic`** (capa idiomática) | Exactitud y velocidad probadas. ⚠️ **PROHIBIDO `pandas-ta` original**: abandonado y con señales de supply-chain attack (historial PyPI borrado, cambio de mantenedor). |
| **Backtesting** | **vectorbt** (barridos de parámetros) + **backtesting.py** (debug trade-a-trade) | vectorbt vectoriza barridos masivos (Numba); backtesting.py es legible y **no tiene live trading** (alineado con "sin ejecución"). |
| **Scheduler 24/7** | **APScheduler** (AsyncIOScheduler + jobstore en Postgres) | Un solo servidor local no necesita Celery. Mismo event loop que ccxt async/FastAPI. Jobstore persistente. **Cadencia short-swing:** ingesta/indicadores en cada cierre de **15m/1h**; `market-context` (IA) **cacheado y refrescado cada 1-2h o ante evento** (no en cada vela) para acotar tokens; `signal-analyst` (IA) solo se invoca cuando hay candidatos. |
| **Base de datos** | **PostgreSQL + TimescaleDB** | Único store: hypertables/compresión para OHLC + SQL relacional para señales/alertas/outcomes. Continuous aggregates 1h→4h→1d. |
| **API** | **FastAPI** | Async nativo, Pydantic, OpenAPI auto, DI para seguridad por ruta. |
| **Notificaciones** | **aiogram v3** en MVP (no solo Bot API saliente) | El **bucle de confirmación de trade** (botones inline "¿la tomaste?") exige interactividad entrante → aiogram desde el inicio. Las alertas salientes siguen siendo simples. |
| **Dashboard** | **Next.js (React) + TradingView lightweight-charts** | Velas e indicadores nivel TradingView, máximo control de UX, consume la FastAPI. |
| **Agente de IA** | **Claude Code** (skills + cron en el servidor) sobre **Claude Opus/Sonnet** según routing de coste | Cumple el requisito explícito de "análisis mediante Claude Code skills". Razona; no calcula. |
| **Orquestación** | **Docker Compose** | Un comando levanta todo el sistema local. |
| **Observabilidad** | **Grafana + Prometheus/Loki** (opcional) sobre métricas del sistema | Monitorizar ingestión/latencia/errores; NO para análisis de trading. |
| **Reverse proxy/TLS** | **Caddy** o **Traefik** | TLS automático; expone solo el dashboard/API tras auth. |
| **Idioma de UI** | **Inglés** (strings de la app/dashboard) | Convención de los proyectos del patrocinador; doc y chat en español. |

> **Nota de continuidad:** este proyecto reaprovecha conocimiento del proyecto hermano (CryptoLedger iOS): patrón *rate-limiter por exchange*, *merge/dedup multi-fuente*, providers de Binance/MEXC/Coinbase. Aquí se reimplementa en Python, no se comparte código (repos separados).

---

## 4. Proveedores de datos seleccionados

> Investigación junio 2026, cifras de páginas oficiales. **MVP a 0 €.** Conversión usada 1 USD ≈ 0,92 €.

### 4.1 Datos de mercado (OHLCV + volumen) — **0 €**
| Proveedor | Rol | Detalle | Coste |
|---|---|---|---|
| **Binance** `/api/v3/klines` | **Primario** | 1h/2h/4h/…/1d, 1000 velas/call, ~3.000 calls/min, sin key/KYC | 0 € |
| **MEXC** `/api/v3/klines` | Failover | Compatible Binance (`60m`, `1W`, `1M`), 1000 velas, sin key/KYC | 0 € |
| **Coinbase** Exchange API `/products/{id}/candles` | Secundario majors | 1m/5m/15m/1h/6h/1d (sin 4h nativo), 300 velas/call | 0 € |
| **BitMart** `/spot/quotation/v3/klines` | Long-tail | 200 velas hist / 1000 lite, incluye 1h/2h/4h | 0 € |
| **CoinGecko free** | Agregado mcap/precio + resolución de tokens + **dominancia BTC** (`/global`) | 10k calls/mes, 365d histórico, OHLC auto. *Upgrade Basic $35 (~32€) solo si escala* | 0 € |

### 4.2 Sentimiento de comunidad — **0 €**
| Proveedor | Qué aporta | Límites free |
|---|---|---|
| **Fear & Greed (alternative.me)** | Índice macro 0–100 (filtro de régimen) | Sin key, histórico completo. **Actualiza 1×/día** |
| **Reddit API (OAuth)** | Posts/comments crudos para NLP propio | 100 QPM, requiere app aprobada |
| **Santiment free** | Social volume, trending words, sentiment | 1.000/mes; histórico 1 año **con lag de 30 días** (research, no realtime) |

> ⚠️ **Consecuencia de la cadencia short-swing (decisión 2026-06-13):** a escala 1h/15m las fuentes de sentimiento gratuitas **no dan timing intradía** (Fear&Greed es diario; Santiment free tiene 30 días de lag). Por tanto el sentimiento entra como **filtro de régimen lento** (¿el ánimo general apoya o no?), **no como disparador**; los triggers intradía se apoyan en **precio/volumen/estructura + noticias/seguridad** (GDELT y PeckShield sí son near-realtime). Recuperar sentimiento social realtime exigiría pago (LunarCrush ~220€ fuera; Santiment Pro ~40€ con realtime limitado) → **se acepta el modo 0€** y queda como upgrade de roadmap si demuestra alpha.

### 4.3 Noticias + geopolítica/macro — **0 €**
| Proveedor | Qué aporta | Notas |
|---|---|---|
| **GDELT DOC 2.0** | **Geopolítica/macro global**, 65 idiomas, tono | Sin key, refresh 15 min, ventana 3 meses. *Insustituible a este precio.* |
| **CoinDesk RSS + Cointelegraph RSS** | Flujo editorial cripto | Sin key, ilimitado |
| **CryptoPanic free** | Sentiment bullish/bearish + flag "important" | ⚠️ **El free se elimina 1-abr-2026** → fallback ya previsto (RSS + GDELT) |

### 4.4 Calendario económico macro (eventos programados) — **0 €**
> Cubre el hueco *forward*: anticipar eventos que pueden girar el mercado (no solo reaccionar como GDELT/CryptoPanic). Eventos diana US de alto impacto: **decisión de tipos FOMC, CPI, NFP, PIB (GDP), PCE**, y secundarios (retail sales, unemployment, FOMC minutes, discursos FED).

| Fuente | Qué aporta | Coste / límites |
|---|---|---|
| **FMP economic calendar** | Calendario forward con **fecha/hora + consenso + previo + actual** e impacto | Free tier (límites exactos a verificar en clarify); **fuente primaria** |
| **FRED (Federal Reserve)** | Valores **reales** publicados + fechas de release oficiales (GDP/CPI/PCE) | **Gratis**, oficial; cross-check de actuals y fechas |
| **FOMC dates (federalreserve.gov)** | Fechas oficiales de reuniones FED | **Gratis**; hardcode/scrape, fechas garantizadas |
| **Fallbacks** | TradingEconomics free / ForexFactory (rating ★★★) / financeflowapi ($5/mo) | Si FMP se queda corto |

> **Referencia de skill:** `tradermonty/economic-calendar-fetcher` (Smithery; mismo autor del repo de trading-skills) sirve de spec para nuestra skill de calendario. **Clasificación de impacto** (máximo vs medio) → `[NEEDS CLARIFICATION]`.

### 4.5 Seguridad / exploits / hacks — **0 €**
| Fuente | Qué aporta | Acceso |
|---|---|---|
| **PeckShield Alert (Telegram)** | Exploits/hacks en **tiempo real** (el trigger más rápido) | Canal Telegram, ilimitado |
| **De.Fi API (REKT DB)** | Hacks/rugs estructurados (la mayor BD pública) | API REST free + key |
| **rekt.news RSS** | Post-mortems / contexto | RSS |

### 4.6 On-chain (whales / flujos) — **0 € DIY en MVP**
- **Etherscan V2 + TronGrid + Blockscout** (gratis): etiquetar hot-wallets de exchanges + umbral USD ⇒ *exchange flows* y *whale alerts* propios.
- **Roadmap de pago (cuando aporte alpha, dentro de <50€):** **Santiment Pro (~40€/mes)** — flows + whale counts + active addresses + MVRV en una sola API. Alternativa media: **Whale Alert (~27€/mes)**.

### 4.7 Derivados / posicionamiento — **0 €**
> Indicadores *adelantados* de posicionamiento saturado y riesgo de squeeze (aunque operemos spot).

| Fuente | Qué aporta | Coste / límites |
|---|---|---|
| **Binance Futures API (pública)** | **Funding rate**, **open interest**, **long/short ratio** (top traders y global) por símbolo | Gratis, sin key |
| **Coinglass (free tier)** | **Liquidaciones** agregadas, OI multi-exchange, heatmaps | Free tier (key; límites a verificar) |

### 4.8 Salvaguardas sistémicas (depeg / salud de exchange) — **0 €**
> Red de seguridad ante *tail risk* que invalida cualquier señal técnica.

| Fuente | Qué aporta | Coste |
|---|---|---|
| **CoinGecko / exchange tickers** | Precio de **USDT/USDC/DAI vs $1** → detección de **depeg** | 0 € |
| **Estado de retiros / incidentes de exchange** | Señales de problemas operativos (vía status pages + noticias/seguridad ya integradas) | 0 € |
| **De.Fi / rekt / PeckShield (ya integrados)** | Insolvencias/exploits a nivel plataforma | 0 € |

> **Acción:** depeg > umbral o incidente grave de un exchange/cadena → **pausa global de señales** (`SYSTEMIC_ALERT`) hasta normalización (C-14).

### 4.9 Proveedores evaluados y descartados (presupuesto)
Kaiko, Amberdata, Messari, Glassnode (API solo en tier enterprise), Nansen/Dune (créditos por llamada, riesgo de coste), LunarCrush (API ~220€), X/Twitter API (free no lee), NewsAPI.org (pago 413€), CryptoCompare/CCData (**free muere 21-may-2026**), CoinAPI/CMC OHLCV (>50€), CertiK/Chainalysis (enterprise).

### 4.10 Claves/secretos necesarios (MVP)
`COINGECKO_DEMO_KEY`, `REDDIT_CLIENT_ID/SECRET`, `SANTIMENT_API_KEY` (free), `DEFI_API_KEY`, `FMP_API_KEY`, `FRED_API_KEY`, `COINGLASS_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `ETHERSCAN_KEY`, `TRONGRID_KEY`, `ANTHROPIC_API_KEY`. *Exchanges (spot y futures público), GDELT, RSS y FOMC dates no requieren clave.*

---

## 5. Arquitectura del sistema

```
                       SERVIDOR LOCAL (Docker Compose · 24/7 · sin exposición entrante)
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                            │
│  FUENTES                         ┌────────────────────────────┐                            │
│  Exchanges (ccxt) ─────────────► │ (1) INGESTA OHLCV (async)   │◄── dispara ──┐             │
│  CoinGecko ────────────────────► │     normaliza multi-venue   │              │             │
│  Fear&Greed/Reddit/Santiment ──► ├────────────────────────────┤      ┌───────┴────────┐    │
│  GDELT/RSS/CryptoPanic ────────► │ (1b) INGESTA CONTEXTO       │      │ (S) SCHEDULER  │    │
│  FMP/FRED/FOMC (calendario) ───► │     sentim/noticias/macro/  │      │ APScheduler    │    │
│  PeckShield/De.Fi/rekt ────────► │     calendario/seguridad/   │      │ cron 15m/1h    │    │
│  Etherscan/TronGrid ───────────► │     on-chain                │      │ jobstore→PG    │    │
│                                  └──────────────┬─────────────┘      └────────────────┘    │
│                                                 │ upsert                                     │
│                                                 ▼                                           │
│                          ┌────────────────────────────────────────┐                        │
│                          │ (2) TimescaleDB (single source of truth)│                        │
│                          │  ohlc · indicators · context · signals  │                        │
│                          │  alerts · outcomes · backtests          │                        │
│                          └───────┬───────────────────────┬────────┘                        │
│                       lee velas  │                        │ persiste                         │
│                                  ▼                        │                                  │
│                    ┌──────────────────────────┐          │                                  │
│                    │ (3) INDICADORES (det.)    │          │                                  │
│                    │  TA-Lib + pandas-ta-classic│         │                                  │
│                    └────────────┬─────────────┘          │                                  │
│                                 ▼                         │      ┌─────────────────────────┐ │
│                    ┌──────────────────────────┐          │      │ VALIDACIÓN (batch)       │ │
│                    │ (4) MOTOR DE CANDIDATOS   │──────────┘◄────►│ vectorbt (barridos)      │ │
│                    │  confluencia conservadora │                 │ backtesting.py (debug)   │ │
│                    │  → candidatos puntuados   │                 │ etiquetado de outcomes   │ │
│                    └────────────┬─────────────┘                 └─────────────────────────┘ │
│                                 │ candidatos + contexto                                      │
│                                 ▼                                                            │
│              ╔══════════════════════════════════════════════════╗                           │
│              ║ (5) AGENTE IA — Claude Code (cron, skills)        ║                           │
│              ║   skills: market-context · signal-analyst ·       ║                           │
│              ║           risk-guardian · alert-composer          ║                           │
│              ║   razona, filtra, decide CONFIANZA + tesis,       ║                           │
│              ║   nunca inventa cifras → emite SEÑAL FINAL        ║                           │
│              ╚════════════════════════┬═════════════════════════╝                           │
│                                       │ señal persistida + decisión auditable                │
│                                       ▼                                                      │
│            ┌──────────────────────────────────────────────────┐                             │
│            │ (6) API — FastAPI (async)                          │                             │
│            │   API Key (servicios) + JWT/scopes (UI), rate-limit│                             │
│            └───────┬───────────────────────────────┬──────────┘                             │
│           HTTPS    │ (Caddy/Traefik, solo intranet) │ on-signal                              │
│                    ▼                                 ▼                                        │
│        ┌────────────────────────┐        ┌───────────────────────────┐                      │
│        │ (8) DASHBOARD Next.js   │        │ (7) TELEGRAM (httpx async)│──► chat privado     │
│        │  lightweight-charts     │        └───────────────────────────┘                      │
│        └────────────────────────┘                                                            │
│   [ Observabilidad opcional: Grafana/Prometheus sobre métricas del sistema ]                 │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

**Principio de oro:** la frontera (3)(4) **determinista** ↔ (5) **IA** es sagrada. Todo número (precio, RSI, R:R, tamaño) lo produce Python y queda persistido; el LLM solo selecciona, pondera, explica y decide *emitir o no*. Así la señal es **reproducible y auditable**.

---

## 6. Componentes detallados

1. **Ingesta OHLCV** — workers `ccxt.async_support`, `enableRateLimit=True`, backoff por venue, paginación histórica con `since`. Failover Binance→MEXC→Coinbase→BitMart.
2. **Ingesta de contexto** — adaptadores por fuente con interfaz común `ContextProvider`; merge/dedup de incidentes de seguridad por contrato+ventana temporal (patrón heredado del proyecto hermano).
3. **Cálculo de indicadores + régimen** — job que, tras cada cierre de vela, recalcula indicadores (incl. ADX), clasifica régimen y persiste; idempotente.
3b. **Ingesta de derivados** — funding/OI/long-short (Binance futures) + liquidaciones (Coinglass); alimenta gates y contexto.
4. **Motor de candidatos** — gates previos (§7.0b) + reglas deterministas de confluencia (§7) → fila en `signal_candidates` con score, ficha de orden, plan de salida y features.
5. **Agente IA (Claude Code)** — §8/§9. Incluye `exit-manager` para gestión post-entrada.
6. **API** — §10.
7. **Telegram** — §11.
8. **Dashboard** — §12.
9. **Validación** — §13.

---

## 7. Motor de señales — lógica técnica (perfil CONSERVADOR · short-swing)

> Objetivo: **señales sólidas, con ≥5% de recorrido objetivo y R:R ≥ 1:2**, cadencia aspiracional ~2/día (sin tope). Valores iniciales (afinables en `/speckit.clarify` y por backtest).

### 7.0 Marcos temporales (cadencia short-swing)
- **Timeframe base: 1h** (régimen y disparo principal).
- **Confirmación de entrada: 15m** (afinar timing/precio de entrada).
- **Contexto de tendencia mayor: 4h/1d** (no operar contra la tendencia superior).
- **Holding esperado:** horas a ~1-2 días. No scalping (nada sub-15m).

### 7.0b Gates previos (deterministas) — se evalúan ANTES de la confluencia (ADR-014/015)
Si falla cualquiera, no hay candidato (no se gasta LLM):
- **G1 · Régimen de mercado:** clasificar el activo como *trending / ranging / high-vol* con **ADX** (p.ej. ADX≥20 = tendencia) + régimen de volatilidad (ATR percentil). En *ranging* débil o *high-vol* extremo → no LONG de ruptura.
- **G2 · Gate BTC (master):** no abrir LONG en una **alt** mientras **BTC** esté en régimen bajista o cayendo con fuerza; ponderar por **dominancia BTC** (BTC subiendo + dominancia subiendo = alts penalizadas). BTC/ETH se evalúan por sí mismos.
- **G3 · Liquidez/spread:** el par debe tener **volumen 24h** y **profundidad/spread** suficientes para llenar el nocional (€500–1.000) sin slippage relevante. Pares ilíquidos se descartan.
- **G4 · Derivados (sanity):** **funding** no extremo (evitar entrar en posicionamiento saturado/euforia), **OI** coherente; liquidaciones recientes masivas → cautela. Funding muy negativo + soporte = posible squeeze alcista (refuerza).
- **G5 · Salvaguarda sistémica:** sin depeg de stablecoins ni incidente grave de exchange/cadena activo (si lo hay → pausa global, §4.8 / C-14).

### 7.1 Reglas de confluencia (deben cumplirse TODAS para candidato LONG)
1. **Tendencia:** precio > EMA50 > EMA200 en **1h**, alineado con tendencia 4h no bajista y **ADX≥20**. *(filtro de régimen alcista)*
2. **Momentum:** RSI(14) saliendo de zona neutra (45→55) y < 70 (no sobrecomprado).
3. **MACD:** cruce alcista (MACD > señal) con histograma creciente.
4. **Volumen:** volumen de la vela de disparo ≥ 1.5× la media de volumen(20).
5. **Estructura:** ruptura confirmada de resistencia o rebote en soporte validado (swing high/low), confirmada en 15m.
6. **Volatilidad/stop:** ATR(14) define stop técnico; el objetivo a +5% debe quedar a **≥ 2× la distancia al stop** (R:R ≥ 1:2). Si no, se descarta.
7. **Gate de contexto (lo evalúa la IA):** sentimiento de régimen NO marcadamente bajista, derivados sin euforia extrema, sin alerta de seguridad activa, sin evento geopolítico/macro de alto impacto inminente.

### 7.2 Salida del candidato (incluye ficha de orden)
`{symbol, tf, side, entry, stop, target(+≥5%), rr, score(0-100), order_ticket{...}, features{...}, ts}`

### 7.3 Ficha de orden ejecutable (`order_ticket`)
Cada señal lleva la orden completa, lista para colocar (manual en Fase 1; automatizable en fase futura). Estructura por defecto **OCO** (entrada atada a TP+SL); alternativa **MARKET+TRAILING**:

| Campo | Descripción | Ejemplo |
|---|---|---|
| `entry_type` | `LIMIT` / `MARKET` | `LIMIT` |
| `entry_price` | precio de entrada | 62.350 |
| `quantity` + `notional` | tamaño calculado (§7.4) | 0.0152 BTC / €950 |
| `order_structure` | `OCO` / `TP_SL` / `MARKET_TRAILING` | `OCO` |
| `take_profit` | objetivo (+≥5%) | 65.500 |
| `stop_loss_trigger` / `stop_loss_limit` | disparo + límite del stop | 61.100 / 61.000 |
| `trailing` | activación + callback (si aplica) | `activation: 64.000, callback: 1.2%` |
| `exit_plan` | plan de salida dinámico (§7.4b) | `TP1 +3% (50%), mover stop a BE, trailing resto a +5%` |
| `time_in_force` | vigencia | `GTC` |
| `target_exchange` | dónde ejecutar (mejor liquidez del par) | Binance |
| `valid_until` | caducidad de la oportunidad | ts + horizonte |

> ⚠️ **Capacidades por exchange:** OCO y trailing **no están igual de soportados** en los 4 venues (Binance: OCO+trailing nativos; MEXC/Coinbase/BitMart varían). La ficha indica `order_structure` soportada por `target_exchange`; si el venue no soporta OCO nativo, se emite como `TP_SL` con dos órdenes + nota. La **matriz de capacidades por exchange** se detalla en `/speckit.plan` (precursor del módulo de ejecución futura, ADR-011).

### 7.4 Gestión de riesgo y sizing (`risk-guardian` skill) — ADR-012
**Modelo de doble restricción** (capital total de referencia configurable; por defecto el tramo €2.000–5.000 acordado):
- `tamaño = min( nocional configurado [€500–1.000] , tamaño que arriesga el 2% del capital total entre entrada y stop )`.
- Como los stops intradía son estrechos (~2–4%), el nocional normalmente **manda**; el **2% es techo de seguridad**.
- **Tope de riesgo agregado:** suma del riesgo de todas las posiciones abiertas ≤ **6%** del capital.
- **Límite de capital desplegado / posiciones concurrentes:** con capital €2–5k y nocional €500–1.000, el factor que limita es el **capital disponible** (con €2k, máx. ~2 posiciones de €1.000). `risk-guardian` no propone una señal si no hay capital libre para su nocional.
- **Cap de correlación (ADR-017):** matriz de correlación entre activos abiertos/candidatos; **no abrir posiciones muy correlacionadas a la vez** (en cripto, 3 "diversificadas" suelen ser una sola apuesta). Limita la exposición correlacionada efectiva, no solo el sector.
- **Throttle por curva de equity (ADR-020):** si el rendimiento reciente de las señales (curva de equity simulada/real) cae, **reducir tamaño o pausar** automáticamente (meta-riesgo en tiempo real, más fino que el circuit breaker de estrategia).
- **R:R mínimo 1:2** (rechazo automático si no).
- **Pérdida diaria máxima** (circuit breaker diario) y **cooldown por símbolo** (anti-overtrading). **No hay tope global de nº de señales/día** (la cadencia 2/día es aspiracional): se notifican todas las sólidas, solo se deduplican por símbolo.
- **Invalidación explícita** en cada señal (precio o evento que la anula).

### 7.4b Gestión dinámica de salida (`exit-manager`) — ADR-016
No basta un TP fijo: el sistema **gestiona la posición tras la entrada** (avisos, no ejecuta en Fase 1) para bloquear ganancias:
- **Scale-out (toma parcial):** p.ej. cerrar **50% en TP1 (+3%)**, dejar correr el resto hacia el objetivo (+5%+).
- **Mover stop a breakeven** tras alcanzar TP1 → operación libre de riesgo.
- **Trailing del remanente** para capturar extensión por encima de +5%.
- **Reevaluación:** si se dispara la invalidación (rotura de estructura, evento, giro de derivados), avisar de **salida anticipada**.
- Tras la entrada, el sistema vigila la posición en cada cierre de vela y emite `TRADE_MANAGEMENT` (mover stop / tomar parcial / salir) por Telegram.
- Parámetros (niveles de TP1/TP2, % a cerrar, gatillo de BE) configurables (`[NEEDS CLARIFICATION]`).

### 7.5 Filtro pre-evento macro (calendario económico) — ADR-013
Regla **determinista** en el motor de candidatos, alimentada por el calendario macro (§4.4). Política **híbrida por impacto** con ventana **12h antes / 2h después** del evento:
- **Eventos de MÁXIMO impacto** (decisión de tipos FOMC, CPI, NFP) → **BLACKOUT**: no se emiten nuevas señales LONG dentro de la ventana.
- **Eventos de impacto MEDIO** (PCE, retail sales, unemployment, minutes, discursos FED) → **flag de cautela**: la señal puede emitirse pero exige **confluencia reforzada** y **tamaño reducido**; la IA lo pondera.
- **Heads-up:** se emite alerta `MACRO_EVENT` por Telegram anunciando el evento inminente y marcando las posiciones abiertas afectadas (para que el operador valore proteger).
- **Aplica al mercado global** (un FOMC mueve todo el cripto), no solo a un símbolo.
- La clasificación máximo/medio de cada evento es configurable (`[NEEDS CLARIFICATION]`).

### 7.6 Por qué "máximas garantías"
Gates previos (régimen/BTC/liquidez/derivados/sistémico) + confluencia múltiple + R:R + gate de contexto + filtro pre-evento macro + sizing acotado + cap de correlación + gestión dinámica de salida + **gate de validación obligatorio** (§13, incl. **batir al HODL**): ninguna estrategia llega a emitir alertas en vivo sin superar backtest y forward-test (con comisiones/slippage modelados) y las métricas objetivo de §1.3.

---

## 8. Capa de IA — el Agente (Claude Code)

### 8.1 Rol
Claude Code corre **vía cron** en el servidor tras cada cierre de vela base (**1h**, con confirmación 15m). Lee de la API/DB los **candidatos** (con su ficha de orden ya calculada) y el **contexto** (cacheado, refresco 1-2h/evento), y ejecuta un pipeline de **skills** que culmina en una decisión: **emitir / descartar / vigilar**, con tesis, confianza (0–100), ficha de orden validada y parámetros. Si hay >2 candidatos sólidos, los emite todos (dedup por símbolo).

### 8.2 Garantías de fiabilidad (no-negociables)
- **Cero alucinación numérica:** la IA recibe los números; si necesita uno que no está, lo pide a la API, no lo inventa. Validación: toda cifra de la señal debe existir idéntica en `signal_candidates`/`indicators` (check determinista post-IA).
- **Auditable:** se persiste el prompt, las entradas, la cadena de razonamiento resumida y la decisión en `signals.ai_rationale` + `ai_audit`.
- **Reproducible:** misma entrada → misma decisión esperable; temperatura baja; el resultado pasa por un validador de esquema (structured output).
- **Fail-safe:** si la IA no está disponible o su salida no valida, **no se emite señal** (silencio > señal mala).

### 8.3 Flujo del agente
```
cron → market-context (sintetiza sentimiento/noticias/geo/seguridad)
     → signal-analyst (toma candidatos + contexto → debate Bull/Bear acotado → decide y puntúa confianza)
     → risk-guardian (verifica R:R, exposición, invalidación; veta si procede)
     → alert-composer (redacta y publica en Telegram + persiste señal)
```

### 8.4 Patrón multi-agente (inspirado en TradingAgents, ADR-009)
La capa IA reimplementa, **como skills de Claude Code**, la taxonomía de roles probada por **TradingAgents** (TauricResearch, ~51k★, Apache-2.0): *Analyst Team → Researchers Bull/Bear → Trader → Risk/Portfolio Manager*. Diferencias deliberadas que preservan nuestros pilares:
- **Frontera determinista intacta (C-2):** TradingAgents deja que el LLM maneje cifras; AEGIS NO. Los números (TA, niveles, R:R) los produce Python; el debate solo razona sobre ellos.
- **Coste acotado (C-7):** el **debate Bull/Bear se limita a 1 ronda y SOLO sobre los candidatos ya filtrados** (pocos al día), no sobre todo el universo 24/7. Evita la explosión de tokens del framework original.
- **Stack propio:** no se adopta LangGraph ni el fork cripto (`auronsun/TradingAgents-crypto`, 8★, inmaduro, depende de CryptoCompare que muere el 21-may-2026 y con Telegram/Binance sin implementar). Se toma la **estructura conceptual**, no el código.
- **Mapeo:** News/Social/Fundamentals Analyst → `market-context`; Bull/Bear + Trader → `signal-analyst`; Risk/Portfolio Manager → `risk-guardian`.

---

## 9. Skills de Claude Code necesarias

> **Hallazgo de la investigación:** **no existe** ninguna skill de Claude Code cripto *plug-and-play y contrastada*. Lo serio del ecosistema son **MCP servers** (Node/Python) y una skill de **bolsa US** (`tradermonty/claude-trading-skills`, 1.9k★, **no cripto**). Por tanto **construimos las skills desde cero**, usando como **especificación** las referencias contrastadas siguientes.

### 9.1 Referencias contrastadas (inspiración, NO dependencia runtime)
| Referencia | Uso |
|---|---|
| `kukapay/crypto-indicators-mcp` (126★, MIT) | Spec de fórmulas TA y mapeo a señal −1/0/1. |
| `marketcalls/vectorbt-backtesting-skills` (154★, MIT, **es Skill real**) | Spec del motor de backtest, plantillas (EMA cross, RSI, MACD, walk-forward) y costes realistas. |
| `tradermonty/claude-trading-skills` (1.9k★, MIT) | Patrón de estructura de skills, *risk gates*, journaling. |
| **`TauricResearch/TradingAgents`** (~51k★, **Apache-2.0**, soporta Claude) | **Referencia principal de arquitectura multi-agente** (Analyst Team → Bull/Bear → Trader → Risk/Portfolio Manager). Es de acciones y LLM-céntrico/LangGraph; tomamos la **taxonomía de roles y el debate Bull/Bear**, no el código. Ver ADR-009 y §8.4. Apto además como **benchmark externo** en validación (§13). |
| `auronsun/TradingAgents-crypto` (8★, Apache-2.0) | Fork cripto inmaduro (Telegram/Binance sin implementar, depende de CryptoCompare que muere 21-may-2026). Solo referencia puntual de qué agentes cripto añadir; **NO construir encima**. |
| `crypto-feargreed-mcp`, `crypto-sentiment-mcp` (kukapay) | Spec de integración Fear&Greed / Santiment. |
| `tradermonty/economic-calendar-fetcher` (Smithery) | Spec de la skill de **calendario económico macro** (§4.4). |
| **CoinGecko MCP oficial** | Referencia de qué endpoints de mercado cubrir. |

### 9.2 Skills a construir (entregables del proyecto)
| Skill | Propósito | Entrada → Salida |
|---|---|---|
| **`market-context`** | Roles News/Social/Fundamentals Analyst (TradingAgents): sintetizar sentimiento + noticias + geopolítica + **calendario macro** + **régimen de mercado/BTC** + **derivados** + seguridad/sistémico | feeds crudos → `{sentiment, news_impact, geo_risk, regime, btc_state, derivatives, upcoming_macro_events[], security_flags[], systemic_flags[], summary}` |
| **`signal-analyst`** | Roles Bull/Bear + Trader (TradingAgents): **debate acotado (1 ronda) sobre los candidatos ya filtrados**, luego decidir señal final, confianza y tesis. No inventa cifras (C-2) | candidatos + contexto → `Signal{side,entry,stop,target,rr,confidence,thesis,bull_case,bear_case,invalidation,exit_plan}` |
| **`risk-guardian`** | Roles Risk/Portfolio Manager (TradingAgents): verificar R:R, tamaño, exposición, **correlación**, **throttle por equity**, capital disponible; vetar señales que no cumplen | señal + cartera → `{approved, reasons[], size_suggestion}` |
| **`exit-manager`** | Gestión dinámica de salida (§7.4b): tras la entrada, decidir parciales/breakeven/trailing/salida anticipada | posición + mercado → `{action, new_stop, take_pct, reason}` |
| **`alert-composer`** | Redactar mensaje Telegram (inglés) con ficha de orden y avisos de gestión; publicar; persistir | señal/gestión → mensaje + envío |
| **`backtest-runner`** | Lanzar vectorbt (con fees/slippage) y devolver métricas **incl. alpha vs HODL** | estrategia+rango → `{profit_factor, win_rate, max_dd, rr, trades, alpha_vs_hodl}` |
| **`signal-evaluator`** | (validación, §13) *LLM-as-judge* de señales vs outcome real + **calibración de confianza** | señales+outcomes → `{precision, recall, false_pos, calibration_error, notes}` |

> Cada skill se especifica en su `SKILL.md`, con contrato de I/O (structured output validado por esquema), y se versiona. El acceso a datos lo hace vía la **API interna** (no acceso directo a DB desde el LLM) para mantener la frontera determinista.

---

## 10. API — endpoints y securización

### 10.1 Endpoints (FastAPI, prefijo `/api/v1`)
| Método | Ruta | Descripción | Auth |
|---|---|---|---|
| GET | `/health` | Liveness/readiness del sistema | público (solo intranet) |
| GET | `/symbols` | Universo vigilado + estado | API key/JWT |
| GET | `/candles/{symbol}?tf=1h&from=&to=` | OHLCV (tf: 15m/1h/4h/1d) | API key/JWT |
| GET | `/indicators/{symbol}?tf=1h` | Indicadores calculados | API key/JWT |
| GET | `/context/{symbol}` | Sentimiento/noticias/geo/seguridad agregados | API key/JWT |
| GET | `/signals?status=active&from=&to=` | Señales (filtros) | API key/JWT |
| GET | `/signals/{id}` | Señal + tesis + auditoría IA | API key/JWT |
| GET | `/signals/{id}/order` | Ficha de orden ejecutable (TP/SL/OCO/trailing) | API key/JWT |
| GET | `/signals/{id}/outcome` | Resultado etiquetado (hit/stop/expired) | API key/JWT |
| GET | `/performance?from=&to=` | KPIs agregados (precisión, PF, R:R) | API key/JWT |
| POST | `/backtests` | Lanzar backtest de estrategia/parámetros | JWT scope `admin` |
| GET | `/backtests/{id}` | Resultado de backtest | JWT scope `admin` |
| POST | `/internal/signals` | (solo loopback) la IA publica señal | mTLS/loopback + API key interna |
| GET | `/audit/{signal_id}` | Traza completa de decisión IA | JWT scope `admin` |

> **No hay endpoints de ejecución de órdenes. Nunca.** (Constitución, §15.)

### 10.2 Securización ("máximas garantías")
- **Sin exposición entrante a Internet:** binding a `127.0.0.1`/red Docker; acceso remoto solo vía **VPN/Tailscale**. Nada de puertos abiertos al WAN.
- **TLS siempre** (Caddy/Traefik con certs locales), incluso en intranet.
- **Doble esquema de auth:** **API key** (`X-API-Key`) para servicios/scripts/IA; **JWT** (access corto + refresh) con **scopes OAuth2** (`read`, `admin`) para el dashboard.
- **Rate limiting** (slowapi) y **CORS** restringido al origen del dashboard.
- **Secretos** fuera del código: Docker secrets / `.env` cifrado / vault; rotación de keys; nunca en logs.
- **Logging estructurado** sin volcar cuerpos sensibles; financiero con privacidad.
- **Principio de mínimo privilegio:** la IA accede solo a endpoints de lectura + `/internal/signals`; jamás a credenciales de exchange (que **no existen**, porque no se opera).
- **Hardening:** dependencias pinneadas y auditadas (lección `pandas-ta`), imágenes mínimas, escaneo de vulnerabilidades en CI, `read-only` filesystem donde se pueda.

---

## 11. Notificaciones Telegram

- **aiogram v3** (entrante + saliente). Bot privado, un solo `chat_id`. **24/7** (alerta a cualquier hora; ejecución manual del operador en Fase 1).
- **Formato de alerta (inglés):** símbolo, timeframe, lado, R:R, confianza (calibrada), tesis (2–3 líneas, con bull/bear case), invalidación, **plan de salida**, flags de contexto (régimen/BTC/sentimiento/derivados/seguridad), enlace al dashboard, y la **ficha de orden lista para copiar/pegar** (entry, TP, SL, OCO/trailing, tamaño, exchange).
- **Bucle de confirmación (ADR-019):** la alerta `SIGNAL` lleva **botones inline** ("✅ Tomada" / "❌ Ignorada"); si se confirma, se registra la posición real y el sistema calcula **P&L real** (no solo teórico) y la integra con **CryptoLedger iOS** (proyecto hermano) como fuente de cartera.
- **Tipos:** `SIGNAL` (con ficha de orden + confirmación), `TRADE_MANAGEMENT` (mover stop a BE / tomar parcial / salir — §7.4b), `INVALIDATED`, `TARGET_HIT`/`STOP_HIT` (outcome), `SECURITY_ALERT`, `MACRO_EVENT`, `SYSTEMIC_ALERT` (depeg / salud de exchange / pausa global).
- **Anti-spam (clave a esta cadencia):** dedup + **cooldown por símbolo** (sin tope global de señales/día), agrupación opcional en *digest* si se acumulan muchas en poco tiempo.
- Comandos: `/status`, `/signals`, `/positions`, `/pnl`, `/mute`, `/pause` (pausa global manual).

---

## 12. Dashboard (Next.js + lightweight-charts)

- **Vistas:** (a) *Watchlist* con mini-gráficos y estado de señal; (b) *Detalle de activo* con velas + indicadores (EMA/RSI/MACD/Bollinger/volumen) sobre lightweight-charts; (c) *Señales* (activas/históricas con tesis y outcome); (d) *Contexto de mercado* (Fear&Greed, sentimiento, noticias, geopolítica, seguridad); (e) *Performance* (KPIs §1.3); (f) *Backtests*.
- Consume la FastAPI con JWT. UI en **inglés**. Solo lectura (sin botones de orden).
- Tema oscuro, responsive, gráficos optimizados para datasets grandes.

---

## 13. Fase de validación — gestionada por IA, sin intervención humana

> Materializa "verificar las señales del mercado, todo gestionado a través de IA, sin intervención humana". Es un **gate**: ninguna estrategia emite alertas en vivo sin superarlo. El humano solo lee el veredicto.

### 13.1 Etapas (pipeline automático)
1. **Backtest histórico** (`backtest-runner`/vectorbt): barrido de parámetros sobre histórico intradía (15m/1h, lo dan gratis los exchanges) por símbolo/timeframe. Métricas: profit factor, win rate, max drawdown, R:R, nº trades. **Comisiones (~0,1% taker) + slippage modelados obligatoriamente** (a esta cadencia pesan; sin ellos las métricas mienten). **Walk-forward** para evitar overfitting al ruido intradía. ➕ Más trades/semana ⇒ **significancia estadística más rápida** (veredicto en menos calendario).
2. **Etiquetado de outcomes (determinista):** para cada señal (histórica o forward), un job evalúa si alcanzó **+5% (objetivo) antes del stop** dentro del horizonte → `HIT` / `STOP` / `EXPIRED`. Esto es la *verdad terreno*, calculada por código, no por el LLM.
3. **Forward-test / shadow mode:** el sistema corre en vivo **emitiendo señales a un log, NO a Telegram**, durante un periodo (p.ej. 2–4 semanas). Se etiquetan outcomes reales según (2).
3b. **Benchmark vs HODL (determinista):** se calcula el rendimiento de **comprar-y-aguantar BTC/ETH** en el mismo periodo y se compara, ajustado por riesgo (Sharpe/Sortino). El **alpha vs HODL** es la métrica de honestidad: si no bate al pasivo, la estrategia no aporta.
4. **Evaluación IA (`signal-evaluator`, LLM-as-judge):** analiza el conjunto señales↔outcomes, reporta **precisión/recall/falsos positivos** y la **calibración de confianza** (¿una confianza de 70% acierta ~70%?), detecta patrones de fallo (p.ej. "falla en alta volatilidad / cuando BTC pierde dominancia") y propone ajustes de umbrales.
5. **Gate de promoción (automático):** si se cumplen los KPIs de §1.3 **incluido alpha vs HODL > 0** (precisión ≥60%, PF ≥1.8, R:R ≥1:2, calibración ≤10%) en forward-test → la estrategia/umbral se **promueve a producción** (empieza a alertar por Telegram). Si no, vuelve al paso 1 con los ajustes propuestos. Todo el bucle lo orquesta el scheduler + Claude Code; el humano recibe un **informe**, no decide manualmente.

### 13.1bis Benchmark externo (TradingAgents en shadow)
Como contraste independiente, durante el forward-test se ejecuta **TradingAgents** (Apache-2.0, configurado con Claude) en **shadow mode** sobre el mismo universo y se comparan sus recomendaciones con las señales de AEGIS y con los outcomes reales. Objetivo: detectar si AEGIS pierde o gana señales frente a un sistema multi-agente del estado del arte. Es un **benchmark de validación, NO una dependencia de producción** (su coste de tokens y no-determinismo lo descartan para el ciclo 24/7).

### 13.2 Salvaguardas anti-overfitting / anti-engaño
- Separación train/validation/test temporal (walk-forward).
- El `signal-evaluator` (LLM) **no** ve el etiquetado como algo a optimizar; recibe outcomes ya fijados por código.
- *Circuit breaker:* si en producción la precisión cae bajo umbral durante N señales, la estrategia se **despromociona** automáticamente y vuelve a shadow mode.
- Registro inmutable de cada decisión y su resultado (para auditoría retrospectiva).

---

## 14. Modelo de datos (TimescaleDB · esquema inicial)

| Tabla | Tipo | Campos clave |
|---|---|---|
| `ohlc` | hypertable | symbol, exchange, tf, ts, o/h/l/c, volume |
| `indicators` | hypertable | symbol, tf, ts, ema50, ema200, rsi14, macd, macd_sig, bb_*, atr14, **adx14**, vol_rel, **regime** |
| `derivatives` | hypertable | symbol, ts, funding_rate, open_interest, long_short_ratio, liquidations_24h |
| `context` | tabla | ts, fear_greed, social_score, news[], geo_risk, **btc_dominance**, **btc_state**, security_flags[], **systemic_flags[]**, macro_blackout(bool), **global_pause(bool)** |
| `macro_events` | tabla | id, name, category, impact(max/medium), scheduled_at, consensus, prior, actual, source |
| `signal_candidates` | tabla | id, symbol, tf, side, entry, stop, target, rr, score, features(jsonb), ts |
| `signals` | tabla | id, candidate_id, side, entry, stop, target, rr, confidence, thesis, bull_case, bear_case, invalidation, ai_rationale, status, ts |
| `order_tickets` | tabla | signal_id, entry_type, entry_price, quantity, notional, order_structure(OCO/TP_SL/MARKET_TRAILING), take_profit, sl_trigger, sl_limit, trailing(jsonb), tif, target_exchange, valid_until |
| `ai_audit` | tabla | signal_id, prompt_hash, inputs(jsonb), reasoning, model, ts |
| `alerts` | tabla | signal_id, channel, payload, sent_at, type |
| `outcomes` | tabla | signal_id, result(HIT/STOP/EXPIRED), realized_pct, closed_at |
| `positions` | tabla | id, signal_id, taken(bool), entry_fill, qty, partials(jsonb), stop_current, status, realized_pnl, source(manual/cryptoledger) |
| `backtests` | tabla | id, strategy, params(jsonb), metrics(jsonb incl. alpha_vs_hodl, calibration), range, created_at |
| `strategies` | tabla | id, name, params(jsonb), status(shadow/prod/retired), kpis(jsonb) |
| `api_keys` / `users` | tabla | hash, scopes, rotated_at |

---

## 15. Constitución del proyecto (para `/speckit.constitution` — principios NO-NEGOCIABLES)

- **C-1 · Advisory en Fase 1 (sin ejecución):** en el MVP el sistema **emite la ficha de orden** (entrada/TP/SL/OCO/trailing) pero **jamás coloca/cancela órdenes ni almacena credenciales con permisos de trading**. Ningún endpoint, skill o job de Fase 1 puede ejecutar. **La ejecución automática real es una fase futura que requiere enmienda explícita de esta constitución** (ADR-011): keys de trading sin retirada, IP whitelist, vault, modo paper obligatorio, kill-switch que cancele todo, y matriz de capacidades por exchange.
- **C-2 · Determinismo primero:** todo número proviene de Python y queda persistido; el LLM decide/explica pero **no inventa cifras**. Check post-IA obligatorio.
- **C-3 · Auditable y reproducible:** cada señal guarda entradas, razonamiento y decisión. Temperatura baja + structured output validado.
- **C-4 · Fail-safe:** ante duda, error o dato faltante, **no se emite señal**. Silencio > señal mala.
- **C-5 · Validación antes de producción:** ninguna estrategia alerta en vivo sin superar el gate de §13. Circuit breaker activo en producción.
- **C-6 · Privado y seguro:** sin exposición entrante, TLS siempre, secretos en vault, dependencias auditadas y pinneadas.
- **C-7 · Coste controlado:** MVP a 0 €; producción < 50 €/mes; cualquier upgrade de proveedor exige evidencia de alpha.
- **C-8 · TDD constitucional:** test antes que implementación; bug fix con test de regresión y datos reales (heredado del proyecto hermano).
- **C-9 · Cero deuda técnica:** error detectado = error resuelto; nada de `TODO: fix later`, `try?`/`try!` sin justificar.
- **C-10 · No es consejo financiero:** disclaimers en UI y alertas; el operador decide y opera manualmente.
- **C-11 · Solidez sobre frecuencia:** la cadencia (~2/día) es **aspiracional, nunca una cuota**. Si no hay setups que cumplan la confluencia, se emiten **0 señales**. Prohibido relajar el gate para "llegar" a un número.
- **C-12 · Sizing acotado:** toda señal respeta el modelo de doble restricción (nocional + 2% de riesgo), el tope de riesgo agregado (6%), el cap de correlación y el capital disponible (ADR-012/017). Una señal sin capital libre para su nocional no se emite.
- **C-13 · Debe batir al HODL:** una estrategia que no supera *buy-and-hold* de BTC/ETH ajustado por riesgo **no se promueve** (ADR-017). Si no hay alpha, no hay producto.
- **C-14 · Salvaguardas sistémicas:** depeg de stablecoin por encima del umbral o incidente grave de exchange/cadena → **pausa global de señales** hasta normalización (ADR-018).
- **C-15 · BTC manda:** prohibido emitir LONG en alts contra un BTC en régimen bajista (gate de régimen, ADR-014).
- **C-16 · P&L honesto:** distinguir P&L **teórico** (todas las señales) del **real** (trades confirmados por el operador); las métricas de producción y el throttle usan el real cuando existe (ADR-019/020).

---

## 16. Plan SDD estricto (flujo spec-kit a aplicar)

> Seguir **en orden, sin saltar fases** (regla del patrocinador: Clarify, Analyze y Tasks-to-Issues son OBLIGATORIAS).

```
1. /speckit.constitution   → constitution.md con C-1…C-16
2. /speckit.specify        → spec.md (6 áreas + AC-IDs en EARS)
3. /speckit.clarify        → resolver los [NEEDS CLARIFICATION] de §18
4. /speckit.plan           → plan.md (Phase -1 Gates + ADRs)
5. /speckit.tasks          → tasks.md atómico, orden TDD (test antes que impl)
6. /speckit.analyze        → analyze-report.md (cobertura AC, orden SHA, drift)
7. /speckit.taskstoissues  → épico + sub-issues (GraphQL addSubIssue, labels)
8. /speckit.checklist      → checklists de seguridad, calidad, constitución
9. /speckit.implement      → en orden TDD, commit por tarea
```

### 16.1 Ejemplos de Acceptance Criteria en EARS (para `/speckit.specify`)
- **AC-01** — *When* una vela de 1h cierra para un símbolo de la watchlist, *the system shall* recalcular sus indicadores y persistirlos en ≤ 5 s.
- **AC-02** — *While* exista una alerta de seguridad activa que afecte a un activo, *the system shall* impedir la emisión de señales LONG para ese activo.
- **AC-03** — *When* un candidato no alcanza R:R ≥ 1:2, *the system shall* descartarlo sin invocar al LLM.
- **AC-04** — *When* el agente emite una señal, *the system shall* verificar que toda cifra (incluida la ficha de orden) coincide con `signal_candidates`/`indicators`; si no, *shall* descartarla y registrar el incidente.
- **AC-05** — *Where* el LLM o su salida no validan, *the system shall* no emitir alerta (fail-safe).
- **AC-06** — *When* una estrategia no supera los KPIs de validación, *the system shall* mantenerla en shadow mode (no alertar por Telegram).
- **AC-07** — *While* el sistema corre, *the system shall* exponer la API solo en la red local/VPN, nunca en el WAN.
- **AC-08** — *When* una señal alcanza +5% antes del stop, *the system shall* etiquetar su outcome como `HIT` y notificar `TARGET_HIT`.
- **AC-09** — *When* se emite una señal, *the system shall* adjuntar una ficha de orden ejecutable (entry, TP, SL, estructura OCO/trailing soportada por `target_exchange`, tamaño) sin colocar ninguna orden.
- **AC-10** — *When* el nocional requerido por un candidato excede el capital disponible o el tope de riesgo agregado (6%), *the system shall* no emitir la señal.
- **AC-11** — *When* el `target_exchange` no soporta OCO nativo, *the system shall* emitir la ficha como `TP_SL` (dos órdenes) con nota explicativa.
- **AC-12** — *While* esté activa la ventana (12h antes / 2h después) de un evento macro de máximo impacto, *the system shall* no emitir nuevas señales LONG (blackout).
- **AC-13** — *When* un evento macro de máximo impacto está a ≤12h, *the system shall* enviar una alerta `MACRO_EVENT` indicando las posiciones abiertas afectadas.
- **AC-14** — *While* BTC esté en régimen bajista, *the system shall* no emitir señales LONG en alts (gate BTC).
- **AC-15** — *When* el par candidato no tiene liquidez/profundidad suficiente para el nocional, *the system shall* descartarlo antes de invocar al LLM.
- **AC-16** — *When* una estrategia no bate al *buy-and-hold* BTC/ETH ajustado por riesgo en forward-test, *the system shall* no promoverla a producción.
- **AC-17** — *When* se detecta un depeg de stablecoin o incidente grave de exchange, *the system shall* activar pausa global y enviar `SYSTEMIC_ALERT`.
- **AC-18** — *When* una posición alcanza TP1, *the system shall* emitir `TRADE_MANAGEMENT` recomendando toma parcial y mover el stop a breakeven.
- **AC-19** — *When* el operador confirma una señal como "tomada", *the system shall* registrar la posición y calcular su P&L real.

### 16.2 ADRs previsibles
ADR-001 ccxt como capa de exchange · ADR-002 TA-Lib+pandas-ta-classic (prohibido pandas-ta) · ADR-003 TimescaleDB single-store · ADR-004 frontera determinista↔IA · ADR-005 Claude Code como motor de decisión · ADR-006 gate de validación con circuit breaker · ADR-007 sin exposición entrante (VPN-only) · ADR-008 MVP zero-cost data · **ADR-009** patrón multi-agente inspirado en TradingAgents (Analyst Team → Bull/Bear → Trader → Risk/Portfolio Manager) reimplementado como skills de Claude Code, con debate acotado a 1 ronda sobre candidatos filtrados y frontera determinista intacta; NO se adopta LangGraph ni el fork cripto; TradingAgents como benchmark externo de validación (§13.1bis) · **ADR-010** cadencia short-swing: base 1h + confirmación 15m + contexto 4h/1d, holding horas–2 días, sin scalping; `market-context` cacheado (refresco 1-2h/evento) para acotar tokens · **ADR-011** ficha de orden ejecutable (OCO/TP-SL/trailing) en Fase 1 sin colocar órdenes; **ejecución automática real como fase futura** con enmienda de C-1, keys de trading, modo paper, kill-switch y matriz de capacidades por exchange · **ADR-012** sizing de doble restricción `min(nocional €500-1.000, 2% riesgo del capital)` + tope agregado 6% + límite por capital disponible · **ADR-013** calendario económico macro (FMP + FRED + fechas FOMC, 0€) con **política pre-evento híbrida por impacto** (blackout en máximo impacto FOMC/CPI/NFP; flag de cautela + confluencia reforzada en impacto medio) y ventana **12h antes / 2h después** · **ADR-014** régimen de mercado (ADX/volatilidad/dominancia) + gate BTC (alts gateadas por estado de BTC) · **ADR-015** datos de derivados/posicionamiento (funding/OI/long-short/liquidaciones) como gate y filtro · **ADR-016** gestión dinámica de salida (scale-out + breakeven + trailing, skill `exit-manager`) · **ADR-017** KPI alpha-vs-HODL como gate de promoción + matriz de correlación de cartera · **ADR-018** salvaguardas sistémicas (depeg stablecoins + salud de exchange → pausa global) · **ADR-019** bucle de confirmación de trade (Telegram interactivo/aiogram) + P&L real + integración CryptoLedger iOS · **ADR-020** calibración de confianza + throttle por curva de equity.

---

## 17. Roadmap por fases

| Fase | Contenido | Salida |
|---|---|---|
| **F0 · Cimientos** | Docker Compose, TimescaleDB, FastAPI esqueleto, ingesta OHLCV ccxt, scheduler | Velas fluyendo + healthcheck |
| **F1 · Indicadores + régimen + candidatos** | TA-Lib (incl. ADX), clasificador de régimen + gate BTC, derivados, gates de liquidez, motor de confluencia conservador | Candidatos puntuados con gates |
| **F2 · Contexto** | Adaptadores sentimiento/noticias/geo/**calendario macro**/**derivados**/seguridad/**sistémico** (gratis) + filtro pre-evento + salvaguardas | Tablas `context`/`macro_events`/`derivatives` pobladas |
| **F3 · Agente IA** | Skills (market-context, signal-analyst, risk-guardian, **exit-manager**, alert-composer), cron | Señales auditables + gestión de salida |
| **F4 · Telegram + Dashboard** | aiogram (alertas + **confirmación interactiva** + P&L real), Next.js/lightweight-charts, integración CryptoLedger | Operador recibe señales ejecutables, confirma y visualiza |
| **F5 · Validación** | Backtesting vectorbt (con fees/slippage), **alpha vs HODL**, etiquetado outcomes, shadow mode, signal-evaluator (+calibración), gate | Promoción automática a producción |
| **F6 · Hardening** | Seguridad, observabilidad, circuit breaker, coverage gate | Producción privada estable |
| **F7 · Ejecución automática (FUTURA, requiere enmienda C-1)** | Módulo de ejecución separado: keys de trading sin retirada + vault, modo paper obligatorio, OCO/trailing por exchange, kill-switch, reconciliación | De advisory a ejecución supervisada |
| **F8+ · Roadmap** | On-chain de pago (Santiment), sentimiento social realtime, perps, más exchanges, ML sentimiento | — |

---

## 18. Decisiones abiertas — `[NEEDS CLARIFICATION]` (resolver en `/speckit.clarify`)

### Cerradas (2026-06-13) — ya integradas
- ✅ **Cadencia/timeframe:** short-swing, base **1h** + confirmación **15m** + contexto 4h/1d (ADR-010).
- ✅ **Horizonte/holding:** horas a ~1-2 días (define ventana `EXPIRED`).
- ✅ **Objetivo:** **+5% fijo**, aceptando menos señales (prevalece solidez).
- ✅ **Cadencia objetivo:** ~2/día **aspiracional, sin tope** (C-11).
- ✅ **Capital total de referencia:** **€2.000–5.000**; nocional **€500–1.000/op**; sizing doble restricción + 2% techo + 6% agregado (ADR-012).
- ✅ **Ventana operativa:** **24/7, notificar siempre**.
- ✅ **Ejecución:** ficha de orden en Fase 1; ejecución automática como fase futura (ADR-011).
- ✅ **Calendario macro:** política híbrida por impacto, ventana 12h/2h (ADR-013).
- ✅ **8 mejoras "mejor advisor":** régimen+BTC, derivados, salida dinámica, alpha-vs-HODL+correlación, liquidez, sistémico, confirmación+P&L real, calibración+throttle (ADR-014…020).

### Pendientes
1. **Universo exacto:** ¿BTC/ETH + top 20 fijo, o watchlist manual? ¿Incluir stablecoins/excluir memecoins?
2. **Capital total exacto** dentro de €2-5k (valor configurable) y **% de riesgo definitivo** (acordado 2% como techo; confirmar).
3. **Exchange por defecto de la ficha de orden** (`target_exchange`): ¿Binance preferente por OCO/trailing nativos? ¿Mapeo símbolo→exchange?
4. **Umbrales TA exactos:** periodos EMA, niveles RSI, parámetros MACD/Bollinger, multiplicador ATR del stop (valores iniciales en §7, afinar por backtest).
4b. **Clasificación de eventos macro** (cuáles son "máximo impacto" → blackout vs "medio" → cautela) y límites exactos del free tier de FMP.
5. **Duración del forward-test/shadow** antes de promover (sugerido 2–4 semanas; a esta cadencia podría bastar menos).
6. **KPIs de promoción definitivos** (sugeridos: precisión ≥60%, PF ≥1.8, R:R ≥1:2).
7. **Idioma de las alertas:** UI en inglés; ¿alertas Telegram en inglés o español?
8. **Acceso remoto:** ¿Tailscale, WireGuard propio, u otro?
9. **Modelo/routing IA:** ¿Opus para decisión + Sonnet/Haiku para tareas baratas? Límite de tokens/coste mensual.
10. **Política de short:** ¿solo LONG en spot (MVP) o también señales de salida/cobertura?
11. **Umbrales de los nuevos gates:** ADX mínimo de tendencia, definición de "BTC bajista", funding "extremo", liquidez/volumen 24h mínimos, umbral de depeg, umbral de correlación máxima.
12. **Plan de salida exacto:** niveles TP1/TP2, % a cerrar en cada uno, gatillo de breakeven, callback del trailing.
13. **Integración CryptoLedger:** ¿cómo se conecta el P&L real (API, fichero, MCP)? Límites del free tier de Coinglass.

---

## 19. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Sobreajuste de estrategia (backtest bonito, real malo) | Walk-forward + forward-test obligatorio + circuit breaker |
| Alucinación numérica del LLM | Frontera determinista + check post-IA (C-2/AC-04) |
| Cambios de tier de proveedores (CryptoPanic abr-2026, CCData may-2026) | Fallbacks ya previstos (GDELT/RSS); diseño multi-fuente |
| Geo-bloqueo Binance | Failover MEXC/Coinbase/BitMart |
| Falsos positivos de seguridad | Dedup + evaluación IA + threshold USD |
| Coste de tokens IA (agravado por cadencia intradía) | Routing por modelo, temperatura baja, `market-context` cacheado (1-2h), LLM solo sobre candidatos |
| Exposición accidental del servidor | VPN-only, binding loopback, sin puertos WAN, CI de seguridad |
| Dependencia maliciosa (caso pandas-ta) | Pinning + auditoría + escaneo en CI |
| Comisiones/slippage erosionan el +5% a mayor frecuencia | Modelado obligatorio en backtest; R:R 1:2 conserva margen neto |
| Overtrading / señales correlacionadas simultáneas | Cooldown por símbolo, tope de riesgo agregado 6%, límite por capital disponible, pérdida diaria máxima |
| Sentimiento intradía débil (fuentes gratis diarias/lagged) | Aceptado como filtro de régimen; triggers en precio/volumen + GDELT/PeckShield near-realtime; upgrade de pago en roadmap |
| Operación 24/7 con ejecución manual (alertas nocturnas) | Aceptado (24/7); ejecución automática futura (ADR-011) resolvería la cobertura nocturna |
| Evento macro programado gira el mercado y pilla posición | Filtro pre-evento (blackout/cautela, 12h/2h) + heads-up `MACRO_EVENT` sobre posiciones abiertas (ADR-013) |
| Fallo/retraso del calendario macro (FMP) | Cross-check con FRED + fechas FOMC hardcodeadas; fail-safe = tratar como blackout si hay incertidumbre |
| Alts arrastradas por caída de BTC | Gate BTC (C-15): no LONG en alts contra BTC bajista |
| Squeeze por posicionamiento saturado | Gate de derivados (funding/OI/liquidaciones, ADR-015) |
| Depeg de stablecoin / insolvencia de exchange (tail risk) | Salvaguardas sistémicas → pausa global (C-14/ADR-018) |
| El sistema no aporta sobre HODL | KPI alpha-vs-HODL como gate de promoción (C-13) |
| Iliquidez: no se puede llenar el nocional sin slippage | Gate de liquidez/spread previo a la señal (AC-15) |
| P&L teórico ≠ real (señales no ejecutadas) | Bucle de confirmación + posiciones reales + integración CryptoLedger (C-16) |
| Confianza no calibrada / racha perdedora | Calibración (signal-evaluator) + throttle por curva de equity (ADR-020) |

---

## 20. Glosario
**Swing trading:** operativa de días–semanas. · **Short-swing:** variante intradía de horas a ~1-2 días (la de AEGIS). · **Confluencia:** varias señales independientes apuntando igual. · **R:R:** ratio riesgo/recompensa. · **ATR:** Average True Range (volatilidad). · **OCO (One-Cancels-the-Other):** par de órdenes TP+SL donde al ejecutarse una se cancela la otra. · **Trailing stop:** stop que sigue al precio a una distancia/callback fijos. · **Nocional:** valor en € comprometido en una posición. · **Slippage:** diferencia entre precio esperado y ejecutado. · **FOMC:** comité de la FED que decide los tipos de interés. · **CPI/NFP/PCE/GDP:** indicadores macro US de alto impacto (inflación / empleo / gasto-inflación / PIB). · **Blackout:** ventana en la que no se abren nuevas posiciones por evento de alto impacto. · **ADX:** Average Directional Index (fuerza de tendencia). · **Régimen de mercado:** estado (tendencia/rango/alta-volatilidad) que condiciona qué estrategia aplica. · **Dominancia BTC:** % de capitalización total que es Bitcoin. · **Funding rate:** pago periódico entre largos y cortos en perpetuos (señal de posicionamiento). · **Open Interest (OI):** contratos abiertos vivos. · **Scale-out:** cerrar la posición por tramos. · **Breakeven (BE):** mover el stop al precio de entrada (riesgo cero). · **Alpha vs HODL:** exceso de rentabilidad ajustada por riesgo frente a comprar y aguantar. · **Calibración:** que la confianza declarada coincida con la tasa de acierto real. · **Depeg:** pérdida de la paridad de una stablecoin con el dólar. · **Shadow mode:** correr en vivo sin alertar, solo registrando. · **Walk-forward:** validación temporal por ventanas deslizantes. · **LLM-as-judge:** usar un modelo para evaluar resultados. · **Outcome:** resultado real de una señal (HIT/STOP/EXPIRED).

---

*Generado por IA bajo supervisión de un humano en el bucle.*
