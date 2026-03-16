# Paso 12 — Validación final, observabilidad y checklist de salida

## Estado de iteración
- **Iteración actual:** Etapa 1 de 8 — baseline de release readiness y criterios de aceptación medibles.
- **Estado:** ✅ Completada.
- **Regla de control aplicada:** etapa cerrada; se requiere autorización del usuario para iniciar etapa 2.

## Referencias documentales consideradas
- `plan.md` (definición del paso 12 y entregables).
- `docs/development_standards.md` (estándares de calidad y testing).
- `docs/mvp_scope.md` (índices de término y criterios del MVP).
- `Makefile` (gates y comandos ejecutables disponibles).

## Objetivo de la etapa 1
Levantar el estado real de salida del paso 12 (pipeline, observabilidad y checklist go-live) y definir brechas concretas con criterios medibles para la etapa 2.

## Diagnóstico baseline (estado actual)

### 1) Pipeline de validación
- **Gates definidos en repositorio:**
  - `make test` (suite unitaria + API integrada),
  - `make bootstrap-validate` (valida reporte de bootstrap),
  - capacidades de smoke sobre compose (`make compose-smoke`) sujetas a Docker.
- **Resultado de evidencia ejecutada:**
  - `make test` ❌ con 1 falla (`tests/api/test_billing.py::test_billing_refresh_status_endpoint`) por mismatch de estado esperado `processing` vs recibido `accepted`.
  - `make bootstrap-validate` ✅ (reporte válido y dentro de contrato).
  - `make doctor-docker` ❌ por ausencia de Docker/Compose en el entorno actual.

### 2) Observabilidad mínima exigida por el paso 12
- **Latencia API:** parcial; existe endpoint de health/ready para smoke, pero no hay baseline documentado de p95 para salida MVP.
- **Salud de cola worker:** parcial; hay procesos de worker y colas en arquitectura, pero falta umbral operativo consolidado de backlog para gate de release.
- **Error rate boletas/pagos:** parcial; hay pruebas de billing/pagos, pero no existe consolidado único con SLI/umbral y criterio de bloqueo de release.

### 3) Checklist de salida go-live
- **Estado:** no existe aún `docs/release_checklist.md` como gate ejecutable del paso 12.
- **Brecha clave:** falta clasificación formal de riesgos críticos/no críticos con criterio de bloquear/no bloquear release.

## Criterios de aceptación medibles definidos para paso 12 (baseline)
1. **Índice de salud de pipeline local:**
   - Meta: 100% de gates definidos para release en estado pass (sin fallas críticas abiertas).
2. **Índice de SLO técnico mínimo:**
   - Meta: 100% de métricas mínimas con target + threshold + owner (`latencia API`, `cola worker`, `error rate boletas/pagos`).
3. **Índice de preparación go-live:**
   - Meta: 100% de ítems críticos cerrados en checklist de salida y plan de rollback documentado.

## Matriz de brechas priorizadas para etapa 2
1. **Pipeline no verde** → corregir/aislar falla de billing y formalizar contrato de gates de release.
2. **Observabilidad sin umbrales operativos** → definir SLI/SLO y semáforo de decisión.
3. **Checklist de salida inexistente** → crear documento ejecutable con riesgos y ownership.
4. **Dependencia de Docker en entorno actual** → declarar limitación y separar evidencia local vs evidencia en entorno con Docker.

## Avance del paso 12 tras etapa 1
- **Salud de pipeline:** 35% (gates existentes, pero con falla crítica activa y limitación Docker en este entorno).
- **SLO técnico mínimo:** 20% (métricas identificadas, sin objetivos/umbrales consolidados).
- **Preparación go-live:** 10% (sin checklist final ni rollback formal en documento del paso 12).
- **Cumplimiento estimado total del paso:** **24%**.
- **Semáforo:** 🟠 Ámbar.

## Evidencia de ejecución (etapa 1)
- `make test`.
- `make bootstrap-validate`.
- `make doctor-docker`.

---

**Cierre de etapa 1:** completado.
**Solicitud de control:** indícame si autorizas avanzar con la **Etapa 2 (contrato de pipeline local y evidencias de release)**.
