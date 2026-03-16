# Contrato de pipeline de release (Paso 12 - Etapa 2)

## Objetivo
Definir un contrato ejecutable y auditable para validar salida MVP con gates de calidad, criterios de bloqueo y formato mínimo de evidencias.

## Gates oficiales de release (orden de ejecución)

| Orden | Gate | Comando | Criterio de éxito | Severidad si falla |
|---|---|---|---|---|
| 1 | Unit + API integration | `make test` | Suite completa en verde (`exit 0`) | **Bloqueante** |
| 2 | Bootstrap report contract | `make bootstrap-validate` | Reporte válido en `infra/seeds/bootstrap_report.json` | **Bloqueante** |
| 3 | Smoke de estado QA local | `make smoke-test-state` | Flujo base QA ejecutable | **Bloqueante** |
| 4 | Health stack Docker core | `make doctor-docker` + `make compose-smoke` | Docker disponible y `/health` + `/ready` en verde | **Bloqueante en entorno Docker** |

## Reglas de decisión (go/no-go)
1. Si un gate bloqueante falla, el release queda en **NO-GO**.
2. Si el entorno no permite ejecutar un gate dependiente de infraestructura (por ejemplo Docker), el estado es **Pendiente por entorno** y no puede declararse GO final sin evidencia en entorno compatible.
3. No se permite compensar un gate rojo con evidencia manual no reproducible.

## Formato mínimo de evidencia por corrida
Cada corrida de validación final debe registrar:
- Fecha/hora UTC.
- Commit SHA evaluado.
- Resultado por gate (`pass`, `fail`, `warning_env`).
- Extracto de salida para fallas.
- Decisión final (`GO`, `NO-GO`, `PENDIENTE_ENTORNO`).

Plantilla sugerida:

```yaml
release_validation:
  timestamp_utc: "YYYY-MM-DDTHH:MM:SSZ"
  commit: "<sha>"
  gates:
    - name: "make test"
      status: "pass|fail|warning_env"
      notes: ""
    - name: "make bootstrap-validate"
      status: "pass|fail|warning_env"
      notes: ""
    - name: "make smoke-test-state"
      status: "pass|fail|warning_env"
      notes: ""
    - name: "make doctor-docker && make compose-smoke"
      status: "pass|fail|warning_env"
      notes: ""
  decision: "GO|NO-GO|PENDIENTE_ENTORNO"
```

## Evidencia baseline de etapa 2
- `make test`: **fail** por `tests/api/test_billing.py::test_billing_refresh_status_endpoint` (mismatch `processing` vs `accepted`).
- `make bootstrap-validate`: **pass**.
- `make smoke-test-state`: **pass**.
- `make doctor-docker`: **warning_env/fail** por ausencia de Docker en entorno actual.

## Acciones obligatorias para etapa 3
1. Corregir o aislar fallo de billing para llevar `make test` a verde.
2. Ejecutar evidencia de `compose-smoke` en entorno con Docker.
3. Versionar reporte consolidado de corrida final usando la plantilla de este contrato.

## Extensión de etapa 4: SLO/SLI y ownership operativo
- Las reglas de umbral, severidad, ventanas y responsables por dominio se definen en `docs/release_slo_ownership.md`.
- La decisión de release debe validar, además de los gates, que no existan alertas P0/P1 activas fuera de tolerancia SLO.
- Si un SLO crítico está fuera de umbral durante su ventana, la decisión final permanece en **NO-GO** aunque los gates de pruebas estén en verde.

## Acciones obligatorias para etapa 5
1. Convertir SLO/SLI definidos en checklist ejecutable de go-live MVP.
2. Clasificar riesgos críticos/no críticos con due date y owner.
3. Adjuntar evidencia de validación contra umbrales en la corrida integral.

## Resultado etapa 5 (checklist go-live)
- Checklist oficial: `docs/release_go_live_checklist.md`.
- La corrida final de release debe incluir estado por check (`PASS|FAIL|PENDIENTE_ENTORNO`) y riesgos críticos abiertos.
- No se permite declarar **GO** con riesgos críticos abiertos ni checks bloqueantes en estado `FAIL`.

