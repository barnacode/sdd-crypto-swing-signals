<!--
SYNC IMPACT REPORT
==================
Version change: (plantilla sin versión) → 1.0.0
Bump rationale: Ratificación inicial. Se sustituye la plantilla genérica por la
  constitución del proyecto AEGIS con 16 principios vinculantes (C-1…C-16)
  derivados de §15 del PROJECT-BRIEF.md (v1.3, 2026-06-13).

Principios definidos (16, frente a los 5 de la plantilla):
  C-1  Advisory en Fase 1 (sin ejecución automática)
  C-2  Determinismo primero (frontera Python↔IA sagrada)
  C-3  Auditable y reproducible
  C-4  Fail-safe (silencio > señal mala)
  C-5  Validación antes de producción
  C-6  Privado y seguro
  C-7  Coste controlado
  C-8  TDD constitucional
  C-9  Cero deuda técnica
  C-10 No es consejo financiero
  C-11 Solidez sobre frecuencia
  C-12 Sizing acotado
  C-13 Debe batir al HODL
  C-14 Salvaguardas sistémicas
  C-15 BTC manda
  C-16 P&L honesto

Secciones añadidas:
  - Restricciones Tecnológicas y de Arquitectura (stack cerrado + frontera determinista)
  - Requisitos de Seguridad
  - Flujo de Desarrollo y Quality Gates (SDD estricto + TDD)
  - Governance (enmiendas, versionado, cumplimiento)

Templates revisados:
  ✅ .specify/templates/plan-template.md — "Constitution Check" usa placeholder
     genérico que lee de este archivo; no requiere cambios.
  ✅ .specify/templates/spec-template.md — sin referencias a principios; OK.
  ✅ .specify/templates/tasks-template.md — sin referencias a principios; OK.
  ✅ .specify/extensions.yml — hooks git intactos; ejecutado before_constitution
     (git ya inicializado → skip).

Follow-up TODOs: ninguno. Sin tokens de plantilla sin resolver.
-->

# Constitución de AEGIS — Algorithmic Edge & Guidance Intelligence System

> Sistema privado, local y 24/7 de **señales short-swing cripto (advisory)**. Captura → cálculo
> determinista → razonamiento IA (Claude Code) → alerta Telegram con ficha de orden ejecutable.
> Esta constitución recoge los principios **NO-NEGOCIABLES** que rigen todo el ciclo SDD del
> proyecto. Prevalece sobre cualquier otra práctica, plan o decisión de implementación.

## Core Principles

### C-1 · Advisory en Fase 1 (sin ejecución automática)

En el MVP (Fase 1) el sistema **DEBE** emitir la ficha de orden completa (entrada, TP, SL,
estructura OCO/TP-SL/trailing, tamaño) pero **NUNCA DEBE** colocar, cancelar o modificar órdenes,
ni almacenar credenciales con permisos de trading. Ningún endpoint, skill o job de Fase 1 puede
ejecutar contra un exchange. La **ejecución automática real es una fase futura** que **REQUIERE
enmienda explícita de esta constitución** (ADR-011) con, como mínimo: keys de trading sin permiso
de retirada, IP whitelist, secretos en vault, modo paper obligatorio previo, kill-switch que
cancele todo, y matriz de capacidades por exchange.

**Rationale:** separar la asesoría del manejo de fondos elimina por diseño el riesgo de pérdida de
capital por un bug, una alucinación o un compromiso de seguridad.

### C-2 · Determinismo primero (la frontera Python↔IA es sagrada)

Todo número (precio, indicadores, niveles, R:R, tamaño, ficha de orden) **DEBE** producirlo Python
y quedar persistido. El LLM **decide, prioriza y explica, pero NUNCA inventa cifras**. Es
**OBLIGATORIO** un check determinista post-IA: toda cifra de la señal emitida debe coincidir
idénticamente con `signal_candidates`/`indicators`; si no coincide, la señal **DEBE** descartarse y
el incidente registrarse.

**Rationale:** garantiza señales reproducibles, auditables y libres de alucinación numérica
(ADR-004).

### C-3 · Auditable y reproducible

Cada señal **DEBE** persistir sus entradas, el prompt (o su hash), la cadena de razonamiento
resumida y la decisión (`signals.ai_rationale` + `ai_audit`). El razonamiento del LLM **DEBE**
usar temperatura baja y **structured output validado por esquema**. Misma entrada → misma decisión
esperable.

**Rationale:** sin trazabilidad no hay validación honesta ni mejora basada en evidencia.

### C-4 · Fail-safe (silencio > señal mala)

Ante duda, error, dato faltante, indisponibilidad del LLM o salida de IA que no valide contra su
esquema, el sistema **DEBE** no emitir señal. Nunca se degrada a una señal de menor calidad para
"no quedarse callado".

**Rationale:** una señal mala cuesta dinero; el silencio no.

### C-5 · Validación antes de producción

Ninguna estrategia o umbral **DEBE** alertar en vivo (Telegram) sin superar el gate de validación
(backtest histórico + forward-test/shadow mode con **comisiones y slippage modelados
obligatoriamente** + KPIs objetivo). En producción **DEBE** existir un circuit breaker que
despromueva automáticamente a shadow mode si la precisión cae bajo umbral durante N señales.

**Rationale:** el backtest bonito no basta; solo el forward-test con costes reales acredita alpha
(ADR-006).

### C-6 · Privado y seguro

El sistema **DEBE** operar sin exposición entrante a Internet (binding loopback / red Docker;
acceso remoto solo vía VPN). **DEBE** usar TLS siempre, guardar secretos fuera del código (vault /
Docker secrets / `.env` cifrado) y mantener dependencias **pinneadas y auditadas**.

**Rationale:** es un sistema financiero privado de un solo operador; la superficie de ataque debe
ser mínima (ADR-007).

### C-7 · Coste controlado

El MVP **DEBE** operar a **0 €** en proveedores de datos. Producción **DEBE** mantenerse por debajo
de **50 €/mes**. Cualquier upgrade de proveedor de pago **REQUIERE** evidencia previa de alpha. El
coste de tokens IA se acota con routing por modelo, temperatura baja, `market-context` cacheado
(refresco 1-2 h o ante evento) e invocación del LLM **solo** sobre candidatos ya filtrados.

**Rationale:** se paga solo si se demuestra que el sistema aporta valor (ADR-008).

### C-8 · TDD constitucional

Las pruebas **DEBEN** escribirse antes que la implementación. Todo bug fix **DEBE** acompañarse de
un test de regresión con datos reales. El ciclo Red-Green-Refactor es obligatorio.

**Rationale:** disciplina heredada del proyecto hermano; previene regresiones en lógica financiera
crítica.

### C-9 · Cero deuda técnica

Un error detectado es un error que **DEBE** resolverse. Está **PROHIBIDO** dejar `TODO: fix later`,
silenciar errores o usar atajos no justificados. La calidad no se pospone.

**Rationale:** la deuda técnica en un sistema 24/7 de dinero real se paga con pérdidas.

### C-10 · No es consejo financiero

Toda UI y toda alerta **DEBEN** incluir disclaimers explícitos. El operador humano decide y opera
manualmente; el sistema solo aconseja.

**Rationale:** responsabilidad legal y de producto; AEGIS es un advisor, no un gestor.

### C-11 · Solidez sobre frecuencia

La cadencia objetivo (~2 señales/día) es **aspiracional, NUNCA una cuota**. Si no hay setups que
cumplan la confluencia, se emiten **0 señales**. Está **PROHIBIDO** relajar gates o umbrales para
"llegar" a un número de señales.

**Rationale:** forzar señales destruye la precisión, que es el North-Star del producto.

### C-12 · Sizing acotado

Toda señal **DEBE** respetar el modelo de doble restricción (`min(nocional €500-1.000, 2% de riesgo
del capital)`), el tope de riesgo agregado del **6 %**, el cap de correlación entre posiciones y el
límite por capital disponible. Una señal sin capital libre para su nocional **NO** se emite.

**Rationale:** la supervivencia del capital prevalece sobre cualquier oportunidad individual
(ADR-012/017).

### C-13 · Debe batir al HODL

Una estrategia que no supere a *buy-and-hold* de BTC/ETH **ajustado por riesgo** (alpha vs HODL > 0)
**NO DEBE** promoverse a producción. Si no hay alpha, no hay producto.

**Rationale:** el listón de honestidad: complejidad que no bate a lo pasivo no aporta (ADR-017).

### C-14 · Salvaguardas sistémicas

Ante un depeg de stablecoin por encima del umbral o un incidente grave de exchange/cadena, el
sistema **DEBE** activar una **pausa global de señales** (`SYSTEMIC_ALERT`) hasta la normalización.

**Rationale:** el *tail risk* sistémico invalida cualquier señal técnica (ADR-018).

### C-15 · BTC manda

Está **PROHIBIDO** emitir señales LONG en alts mientras BTC esté en régimen bajista o cayendo con
fuerza (gate de régimen + dominancia). BTC/ETH se evalúan por sí mismos.

**Rationale:** en cripto, las alts rara vez sobreviven a un BTC bajista; ignorarlo es arruinar el
edge (ADR-014).

### C-16 · P&L honesto

El sistema **DEBE** distinguir el P&L **teórico** (todas las señales) del **real** (trades
confirmados por el operador). Las métricas de producción y el throttle por curva de equity **DEBEN**
usar el P&L real cuando exista.

**Rationale:** medir sobre señales no ejecutadas se autoengaña; la verdad es lo que el operador
realmente tomó (ADR-019/020).

## Restricciones Tecnológicas y de Arquitectura

- **Stack cerrado (decisiones vinculantes, §3 del brief):** Python 3.12; `ccxt` async **solo
  endpoints públicos** (sin claves de trading); **TA-Lib + `pandas-ta-classic`** — está
  **PROHIBIDO** `pandas-ta` original (abandonado, señales de supply-chain attack); `vectorbt` +
  `backtesting.py` para validación; APScheduler (jobstore en Postgres); **PostgreSQL + TimescaleDB**
  como único store; FastAPI; **aiogram v3** (entrante + saliente); Next.js + TradingView
  lightweight-charts; Claude Code skills como motor de decisión; Docker Compose.
- **Frontera determinista inviolable:** la separación entre el cálculo determinista (indicadores +
  motor de candidatos) y la capa de IA (decisión/explicación) es arquitectónicamente sagrada (C-2).
- **No existen endpoints de ejecución de órdenes. Nunca** (C-1).
- **Acceso a datos por la IA:** las skills acceden a datos **solo vía la API interna** (nunca a la
  DB directamente), para preservar la frontera determinista y el mínimo privilegio.
- **Idioma:** strings de la app/dashboard en **inglés**; documentación y comunicación de proyecto en
  **español**.

## Requisitos de Seguridad

- **Sin exposición entrante:** binding a `127.0.0.1`/red Docker; acceso remoto solo vía VPN; ningún
  puerto abierto al WAN.
- **TLS siempre**, incluso en intranet (Caddy/Traefik).
- **Doble esquema de auth:** API Key (`X-API-Key`) para servicios/IA; JWT con scopes OAuth2
  (`read`, `admin`) para el dashboard.
- **Rate limiting** y **CORS** restringido al origen del dashboard.
- **Secretos** fuera del código, rotables y **nunca en logs**; logging estructurado sin volcar
  cuerpos sensibles.
- **Mínimo privilegio:** la IA accede solo a endpoints de lectura + `/internal/signals`; jamás a
  credenciales de exchange (que no existen en Fase 1).
- **Hardening:** dependencias pinneadas y auditadas, imágenes mínimas, escaneo de vulnerabilidades
  en CI, filesystem `read-only` donde sea posible.

## Flujo de Desarrollo y Quality Gates

- **SDD estricto, sin saltar fases** (orden obligatorio):
  `constitution → specify → clarify → plan → tasks → analyze → taskstoissues → checklist →
  implement`. Las fases **clarify**, **analyze** y **taskstoissues** son **OBLIGATORIAS** (regla del
  patrocinador).
- **TDD:** test antes que implementación; un commit por tarea (C-8).
- **Acceptance Criteria en formato EARS**, con AC-IDs trazables a tareas e issues.
- **Quality gates:** Constitution Check en `/speckit.plan` (Phase -1), cobertura de AC en
  `/speckit.analyze`, checklists de seguridad/calidad/constitución antes de implementar, coverage
  gate y contract testing en CI.
- **Cumplimiento constitucional:** ninguna feature avanza de fase si viola un principio C-1…C-16 sin
  enmienda aprobada.

## Governance

Esta constitución **prevalece** sobre cualquier otra práctica, plan o decisión de implementación.

- **Enmiendas:** toda modificación de un principio **REQUIERE** (a) un ADR que la documente y
  justifique, (b) un bump de versión semántica, y (c) un plan de migración cuando afecte a artefactos
  o código existente. La **habilitación de la ejecución automática real (C-1)** exige una **enmienda
  MAYOR explícita** con los controles enumerados en C-1/ADR-011.
- **Versionado semántico de la constitución:**
  - **MAJOR** — eliminación o redefinición incompatible de un principio o de la governance.
  - **MINOR** — nuevo principio/sección o ampliación material de guía.
  - **PATCH** — aclaraciones, redacción, correcciones no semánticas.
- **Revisión de cumplimiento:** todo PR/review **DEBE** verificar el cumplimiento de los principios
  aplicables; cualquier complejidad añadida **DEBE** justificarse frente a C-9. Los quality gates del
  flujo SDD son los puntos de control formales.
- **Guía runtime:** los artefactos SDD (`spec.md`, `plan.md`, `tasks.md`) y `PROJECT-BRIEF.md` son la
  guía de desarrollo; ninguno puede contradecir esta constitución.

**Version**: 1.0.0 | **Ratified**: 2026-06-13 | **Last Amended**: 2026-06-13
