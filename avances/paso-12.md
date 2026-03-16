# Paso 12 — Validación final, observabilidad y checklist de salida

## Estado de iteración
- **Iteración actual:** Planificación inicial (pre-etapa 1).
- **Estado:** 🟡 En planificación.
- **Regla de control activa:** no iniciar ejecución técnica de etapas sin orden explícita del usuario.

## Skill aplicada y referencias documentales consideradas
- **Skill principal:** `skills/release-readiness-observability-gates/SKILL.md`.
- **Referencias de la skill:**
  - `skills/release-readiness-observability-gates/references/release-gates-checklist.md`.
  - `skills/release-readiness-observability-gates/references/slo-template.md`.
- **Referencias del repositorio:**
  - `plan.md` (definición del paso 12 y entregables esperados).
  - `docs/development_standards.md` (estándares de ejecución y calidad).
  - `docs/mvp_scope.md` (criterios de aceptación del MVP y foco de salida).

## Objetivo de esta primera intervención
Definir un plan de trabajo iterativo de **8 etapas** para ejecutar el paso 12 con trazabilidad, evidencias y control de avance por autorización.

## Plan de trabajo (8 etapas)
1. **Baseline de release readiness (diagnóstico):**
   - Levantar estado actual de pipeline, observabilidad y checklist.
   - Definir brechas vs criterios de salida del MVP.

2. **Contrato de pipeline local y evidencias:**
   - Especificar comandos y evidencia mínima por gate: lint/format, unit, integración API, smoke e2e.
   - Formalizar formato de reporte de ejecución.

3. **Instrumentación mínima de observabilidad:**
   - Asegurar medición de latencia API, salud de cola worker y error rate boletas/pagos.
   - Definir dónde se consultan estas métricas en entorno local.

4. **SLO/SLI y umbrales accionables:**
   - Definir objetivos, ventana de medición, threshold de alerta y owner por métrica.
   - Alinear semáforo de salida (verde/amarillo/rojo) con estos umbrales.

5. **Checklist de go-live ejecutable con riesgos:**
   - Construir checklist con clasificación de riesgos críticos/no críticos.
   - Vincular cada ítem a evidencia y decisión (bloquea/no bloquea salida).

6. **Plan de rollback y contingencia:**
   - Definir condiciones de abortar release.
   - Establecer plan de reversión y responsables operativos.

7. **Corrida integral de validación final:**
   - Ejecutar pipeline completo y consolidar resultados.
   - Verificar cumplimiento de SLO mínimos y estado del checklist.

8. **Hardening documental y cierre:**
   - Emitir `docs/release_checklist.md` final.
   - Dejar reporte consolidado de pipeline + observabilidad + riesgos conocidos.

## Criterios de éxito del plan (para cerrar el paso 12)
- Pipeline final con gates trazables y evidencia reproducible.
- Métricas mínimas activas con umbrales y responsables definidos.
- Checklist go-live completo con clasificación de riesgos y decisiones documentadas.
- Estrategia de rollback validada documentalmente.
- Reporte final de salida con estado de cumplimiento del paso.

## Estado de avance del paso
- **Cumplimiento estimado actual:** **12%** (planificación estructurada lista, ejecución técnica pendiente).
- **Semáforo:** 🟡 Amarillo (preparado para iniciar etapa 1).

---

**Solicitud de control:** indícame con tu próxima instrucción si autorizas avanzar con la **Etapa 1 (baseline de release readiness)**.
