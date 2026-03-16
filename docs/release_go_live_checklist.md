# Checklist de go-live MVP (Paso 12 - Etapa 5)

## Objetivo
Estandarizar una checklist ejecutable de salida MVP con criterios de aprobación, clasificación de riesgo y responsables claros por ítem.

## Política de decisión
- **GO**: todos los ítems críticos en `PASS` y sin alertas P0/P1 fuera de SLO.
- **NO-GO**: al menos un ítem crítico en `FAIL` o incidente activo P0/P1.
- **PENDIENTE_ENTORNO**: faltan evidencias por limitaciones de infraestructura (ej. Docker no disponible), sin fallas funcionales críticas.

## Checklist ejecutable

| ID | Categoría | Check | Comando/Evidencia | Tipo | Riesgo si falla | Owner | Estado |
|---|---|---|---|---|---|---|---|
| C1 | Pipeline | Suite de tests completa | `make test` | Bloqueante | Crítico | Release captain | `PASS|FAIL|PENDIENTE_ENTORNO` |
| C2 | Pipeline | Validación bootstrap report | `make bootstrap-validate` | Bloqueante | Crítico | Backend/API | `PASS|FAIL|PENDIENTE_ENTORNO` |
| C3 | Pipeline | Smoke de estado QA | `make smoke-test-state` | Bloqueante | Crítico | QA | `PASS|FAIL|PENDIENTE_ENTORNO` |
| C4 | Infra | Salud Docker/Compose | `make doctor-docker` + `make compose-smoke` | Bloqueante (en entorno Docker) | Crítico | Infra owner | `PASS|FAIL|PENDIENTE_ENTORNO` |
| C5 | Observabilidad | Billing dentro de SLO (`error_rate <= 2.0`) | `GET /billing/observability/metrics` | Bloqueante | Crítico | Billing owner | `PASS|FAIL|PENDIENTE_ENTORNO` |
| C6 | Observabilidad | Pagos dentro de SLO (`error_rate <= 3.0`) | `GET /payments/observability/metrics` | Bloqueante | Crítico | Payments owner | `PASS|FAIL|PENDIENTE_ENTORNO` |
| C7 | Observabilidad | API health/readiness estable | `GET /health`, `GET /ready` | Bloqueante | Alto | Backend/API | `PASS|FAIL|PENDIENTE_ENTORNO` |
| C8 | Operación | Runbooks y owners vigentes | `docs/release_slo_ownership.md` | No bloqueante | Medio | Tech lead | `PASS|FAIL|PENDIENTE_ENTORNO` |
| C9 | Operación | Evidencia consolidada versionada | YAML de corrida final | No bloqueante | Medio | Release captain | `PASS|FAIL|PENDIENTE_ENTORNO` |
| C10 | Seguridad operacional | Sin secretos en diff de release | revisión git + `.env.example` | No bloqueante | Alto | Backend/API | `PASS|FAIL|PENDIENTE_ENTORNO` |

## Registro de riesgos (críticos/no críticos)

| Riesgo | Clasificación | Impacto | Probabilidad | Mitigación | Due date | Owner | Estado |
|---|---|---|---|---|---|---|---|
| Fallo en gate `make test` | Crítico | Alto | Media | Corregir regresión + revalidar suite | Inmediato (antes de release) | Backend/API | Abierto |
| No disponibilidad de Docker en entorno validación | Crítico | Alto | Alta | Ejecutar corrida en runner con Docker y adjuntar evidencia | Antes de declarar GO | Infra owner | Abierto |
| `billing.error_rate` fuera de SLO | Crítico | Alto | Media | Revisar DLQ/reintentos + reproceso controlado | <24h | Billing owner | Monitoreado |
| `payments.pending_total` sostenido alto | No crítico (si < umbral de alerta) | Medio | Media | Conciliación por sucursal + revisar webhooks | <48h | Payments owner | Monitoreado |
| Desalineación documental de checklist/evidencia | No crítico | Medio | Baja | Validación cruzada PR checklist vs reporte final | Antes de cierre etapa 8 | Release captain | Abierto |

## Plantilla rápida de ejecución por corrida

```yaml
go_live_checklist:
  timestamp_utc: "YYYY-MM-DDTHH:MM:SSZ"
  commit: "<sha>"
  checks:
    - id: "C1"
      status: "PASS|FAIL|PENDIENTE_ENTORNO"
      notes: ""
    - id: "C2"
      status: "PASS|FAIL|PENDIENTE_ENTORNO"
      notes: ""
    - id: "C3"
      status: "PASS|FAIL|PENDIENTE_ENTORNO"
      notes: ""
    - id: "C4"
      status: "PASS|FAIL|PENDIENTE_ENTORNO"
      notes: ""
    - id: "C5"
      status: "PASS|FAIL|PENDIENTE_ENTORNO"
      notes: ""
    - id: "C6"
      status: "PASS|FAIL|PENDIENTE_ENTORNO"
      notes: ""
  decision: "GO|NO-GO|PENDIENTE_ENTORNO"
  open_critical_risks: []
```
