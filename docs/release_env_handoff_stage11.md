# Handoff de entorno compatible para declarar GO (Etapa 11)

## Objetivo
Definir un procedimiento exacto para ejecutar la validación final en un entorno con Docker/Compose y cerrar el bloqueo `PENDIENTE_ENTORNO`.

## Precondiciones mínimas
1. Docker Engine instalado y operativo.
2. Docker Compose v2 disponible (`docker compose version`).
3. Puertos locales libres para API (`8000`) y servicios core.
4. Rama/commit exacto a validar identificado.

## Secuencia de ejecución (orden obligatorio)

1. **Validar entorno base**
   - `make doctor-docker`

2. **Levantar stack core**
   - `make compose-up`

3. **Verificar salud del stack**
   - `make compose-smoke`

4. **Ejecutar evidencia integral automatizada**
   - `make release-evidence-stage9`

5. **Apagar stack controladamente**
   - `make compose-down`

## Criterio de aceptación de handoff
El handoff se considera exitoso cuando:
- `doctor-docker` y `compose-smoke` quedan en PASS.
- `docs/release_validation_stage9.yaml` no contiene `warning_env` en gates de infraestructura.
- La decisión final cambia de `PENDIENTE_ENTORNO` a `GO` o `NO-GO` estrictamente por señal funcional/SLO (no por entorno).

## Evidencia mínima a adjuntar en PR/acta
1. Salida textual de los comandos ejecutados.
2. `docs/release_validation_stage9.yaml` regenerado en entorno Docker.
3. `docs/release_observability_snapshot_stage9.json` regenerado en la misma corrida.
4. SHA validado + timestamp UTC.

## Matriz de fallback
- Si `doctor-docker` falla: mantener `PENDIENTE_ENTORNO` y abrir ticket de infraestructura.
- Si `compose-smoke` falla: declarar `NO-GO` técnico de plataforma y ejecutar runbook de contingencia.
- Si SLO críticos fallan con entorno válido: `NO-GO` funcional (ya no es bloqueo de entorno).
