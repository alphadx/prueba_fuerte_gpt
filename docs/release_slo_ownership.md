# SLO/SLI y ownership operativo para salida MVP (Paso 12 - Etapa 4)

## Objetivo
Definir umbrales operativos accionables para release readiness, con responsables por dominio y reglas de alerta mínimas para operación local/sandbox.

## Fuentes de señal (SLI)
1. **Calidad de build/release**
   - `make test`
   - `make bootstrap-validate`
   - `make smoke-test-state`
2. **Salud de plataforma**
   - `GET /health`
   - `GET /ready`
3. **Observabilidad de billing**
   - `GET /billing/observability/metrics`
4. **Observabilidad de pagos**
   - `GET /payments/observability/metrics`

## Matriz SLI/SLO por dominio

| Dominio | SLI | SLO objetivo | Ventana | Severidad si incumple | Owner | Acción inmediata |
|---|---|---|---|---|---|---|
| Pipeline release | `% gates en verde` | 100% gates bloqueantes en verde para GO | por corrida | P0 | Release captain | Declarar `NO-GO` y abrir plan de remediación |
| API disponibilidad | `/health` y `/ready` success rate | >= 99.0% | 24h (sandbox/local) | P1 | Backend/API | Revisar logs + reinicio controlado + rollback si persiste |
| Billing emisión | `error_rate` en `/billing/observability/metrics` | <= 2.0% | rolling 1h | P1 | Billing owner | Revisar DLQ, reintentos y proveedor sandbox |
| Billing cola | `queue_depth` en `/billing/observability/metrics` | <= 20 por más de 10 min | rolling 10 min | P2 | Billing owner | Escalar worker batch y drenar cola |
| Pagos rechazo | `error_rate` en `/payments/observability/metrics` | <= 3.0% | rolling 1h | P1 | Payments owner | Revisar webhooks/firma e idempotencia |
| Pagos pendientes | `pending_total` en `/payments/observability/metrics` | <= 10 por más de 15 min | rolling 15 min | P2 | Payments owner | Verificar conciliación y reintentos de webhook |

## Reglas de alerta accionables

### A1 — Bloqueo release por pipeline
- **Disparo:** cualquier gate bloqueante en estado `fail`.
- **Severidad:** P0.
- **Canal:** comentario en evidencia de release + ticket crítico.
- **Runbook corto:**
  1. congelar promoción,
  2. registrar gate fallido y comando,
  3. asignar owner del dominio,
  4. revalidar corrida completa.

### A2 — Degradación billing
- **Disparo:** `billing.error_rate > 2.0` o `dead_lettered_documents > 0` sostenido 10 min.
- **Severidad:** P1.
- **Canal:** alerta de operación backend.
- **Runbook corto:**
  1. inspeccionar documentos `dead_lettered`,
  2. validar estado del proveedor sandbox,
  3. ejecutar reproceso controlado,
  4. si persiste, declarar `NO-GO`.

### A3 — Degradación pagos
- **Disparo:** `payments.error_rate > 3.0` o aumento sostenido de `pending_total`.
- **Severidad:** P1/P2 según impacto.
- **Canal:** alerta de operación backend.
- **Runbook corto:**
  1. validar firmas y duplicados de webhook,
  2. revisar transiciones de estado,
  3. ejecutar conciliación por sucursal,
  4. revalidar SLI.

## Tabla de ownership (RACI reducido)

| Capability | Responsable (R) | Aprobador (A) | Consultado (C) | Informado (I) |
|---|---|---|---|---|
| Release gates | Release captain | Tech lead | QA | Producto |
| Billing sandbox/worker | Billing owner | Tech lead | QA | Release captain |
| Pagos adapters/webhooks | Payments owner | Tech lead | QA | Release captain |
| Infra Docker/Compose | Infra owner | Tech lead | Backend | QA |

## Criterio de cumplimiento de etapa 4
La etapa queda conforme cuando:
1. Cada SLI crítico tiene umbral explícito (SLO), ventana y severidad.
2. Cada alerta tiene owner y runbook resumido.
3. El contrato de release referencia estas reglas para decisión GO/NO-GO.
