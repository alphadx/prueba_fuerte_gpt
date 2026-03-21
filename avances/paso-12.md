# Paso 12 — Validación final, observabilidad y checklist de salida

## Estado de iteración
- **Iteración actual:** Etapa 15 (post-cierre) — robustez del pipeline de cierre y consistencia checklist/gates.
- **Estado:** ✅ Completada.
- **Regla de control aplicada:** un gate consolidado no puede declararse válido si no ejecuta todos sus subchecks ni si el checklist derivado queda desalineado.

## Referencias documentales consideradas
- `infra/scripts/generate_release_evidence.py` (generación automatizada reforzada).
- `infra/scripts/validate_release_evidence.py` (validador con cruces checklist/gates/SLO).
- `infra/scripts/generate_release_closure_acta.py` (generador de acta).
- `docs/release_validation_stage9.yaml` (artefacto fuente).
- `docs/release_pipeline_contract.md` (contrato y resultado por etapa).
- `docs/release_stage12_closure_acta.md` (acta emitida automáticamente).

## Objetivo de la etapa 15
Eliminar falsos positivos en el gate de infraestructura y endurecer la validación para que ninguna evidencia inconsistente pueda cerrar el release.

## Implementación realizada

### 1) Gate Docker/Compose ejecutado de forma real
Se reforzó `infra/scripts/generate_release_evidence.py` para que el gate `make doctor-docker && make compose-smoke`:
- ejecute `doctor-docker` y, si pasa,
- ejecute `compose-smoke`,
- propague `FAIL` o `PENDIENTE_ENTORNO` según el resultado real observado.

### 2) Validador cruzado de evidencia
Se extendió `infra/scripts/validate_release_evidence.py` para validar:
- presencia de `go_live_checklist`, `critical_risks_open` y snapshot referenciado,
- consistencia entre gates y checklist (`C1`-`C4`),
- consistencia entre SLO y checklist (`C5`-`C7`),
- coherencia del dictamen final con checks bloqueantes.

### 3) Cobertura unitaria adicional
Se añadieron pruebas focalizadas para:
- ejecución secuencial del gate Docker/Compose,
- corte temprano en `warning_env`,
- rechazo de consolidado inconsistente por checklist.

## Resultado de la etapa 15
- **Cobertura funcional:** evidencia consolidada + validación automática + acta derivada automáticamente + robustez adicional del gate de infraestructura.
- **Estado release actualizado:** **PENDIENTE_ENTORNO** (bloqueo residual solo de infraestructura Docker/Compose).
- **Semáforo:** 🟡 Amarillo.

## Evidencia de ejecución (etapa 15)
- `python -m pytest -q tests/unit/test_release_validation_scripts.py`
- `PYTHONPATH=apps/api python infra/scripts/validate_release_evidence.py --path docs/release_validation_stage9.yaml`
- `make release-closure-pipeline-stage9`
- `make doctor-docker`

## Métricas finales actualizadas del paso 12
- **Salud de pipeline:** 86%.
- **SLO técnico mínimo:** 88%.
- **Preparación go-live:** 94%.
- **Cumplimiento estimado total del paso:** **94%**.
- **Semáforo final actualizado:** 🟡 Amarillo.

---

**Cierre de etapa 15:** completado.
**Estado final actualizado del paso 12:** `PENDIENTE_ENTORNO` hasta ejecutar corrida final en entorno Docker/Compose compatible y regenerar la evidencia/acta final con infraestructura validada.
