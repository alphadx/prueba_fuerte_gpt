# Paso 12 — Validación final, observabilidad y checklist de salida

## Estado de iteración
- **Iteración actual:** Etapa 4 de 8 — definición de umbrales SLO/SLI, owners y alertas accionables.
- **Estado:** ✅ Completada.
- **Regla de control aplicada:** etapa cerrada; se requiere autorización del usuario para iniciar etapa 5.

## Referencias documentales consideradas
- `plan.md` (definición de etapa 4 del paso 12).
- `docs/release_pipeline_contract.md` (gates y criterio GO/NO-GO/PENDIENTE_ENTORNO).
- `docs/release_slo_ownership.md` (nuevo marco de SLO/SLI y ownership operativo).
- `apps/api/openapi.yaml` (endpoints de observabilidad de etapa 3 utilizados como fuente SLI).

## Objetivo de la etapa 4
Definir umbrales operativos mínimos (SLO), reglas de alerta accionables y ownership explícito por dominio para endurecer la decisión de salida MVP.

## Implementación realizada

### 1) Matriz formal SLI/SLO por dominio
Se creó `docs/release_slo_ownership.md` con:
- SLI críticos del release: pipeline, salud API, billing y pagos.
- Umbrales SLO con ventana temporal y severidad (P0/P1/P2).
- Owners por dominio y acción inmediata ante incumplimiento.

### 2) Reglas de alerta accionables
Se definieron alertas mínimas y runbooks breves:
- **A1:** bloqueo de release por gate rojo (P0).
- **A2:** degradación de billing por error_rate/dead-letter (P1).
- **A3:** degradación de pagos por error_rate/pending_total (P1/P2).

### 3) Endurecimiento del contrato de release
Se actualizó `docs/release_pipeline_contract.md` para que la decisión final valide también estado SLO:
- Si hay SLO crítico fuera de umbral en su ventana, el release permanece en **NO-GO** aunque los tests estén verdes.
- Se dejó backlog obligatorio para etapa 5 enfocado en checklist go-live y clasificación de riesgos.

## Resultado de la etapa 4
- **Cobertura funcional:** contrato de salida ahora incluye quality gates + señales operativas con ownership.
- **Estado release:** **NO-GO** condicionado hasta evidencia de cumplimiento SLO + validación Docker en entorno compatible.
- **Semáforo del paso:** 🟠 Ámbar con mejora en gobernanza operativa.

## Evidencia de ejecución (etapa 4)
- `make test`
- `make bootstrap-validate`
- `make smoke-test-state`
- `make doctor-docker`

## Avance del paso 12 tras etapa 4
- **Salud de pipeline:** 60%.
- **SLO técnico mínimo:** 62% (umbrales y ownership definidos; falta evidencia sostenida por ventana).
- **Preparación go-live:** 36%.
- **Cumplimiento estimado total del paso:** **50%**.
- **Semáforo:** 🟠 Ámbar.

---

**Cierre de etapa 4:** completado.
**Solicitud de control:** indícame si autorizas avanzar con la **Etapa 5 (checklist de go-live MVP con clasificación de riesgos críticos/no críticos)**.
